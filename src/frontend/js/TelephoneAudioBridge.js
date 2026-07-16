// Browser-side audio bridge for the Docker telephone.
//
// In Docker, the MeshChat server has no microphone or speaker, so LXST's
// server-side audio can't work. This module captures the browser microphone,
// streams raw PCM frames to the server over a WebSocket, and plays back the
// call audio frames the server sends. It pairs with the server-side
// webrtc_audio_bridge.py (WebSocketAudioSource / WebSocketAudioSink).
//
// Audio format must match the server bridge: 48 kHz, mono, 16-bit PCM.

const BRIDGE_SAMPLERATE = 48000;
const BRIDGE_CHANNELS = 1;
const FRAME_MS = 20; // 20ms frames

export default class TelephoneAudioBridge {

    constructor() {
        this.ws = null;
        this.audioContext = null;
        this.micStream = null;
        this.micSource = null;
        this.processor = null;
        this.playbackTime = 0;
        this.running = false;
    }

    // open the bridge: mic capture + websocket + playback
    async start() {
        if (this.running) {
            return;
        }
        this.running = true;

        // 1. get the microphone
        this.micStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: BRIDGE_CHANNELS,
                sampleRate: BRIDGE_SAMPLERATE,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            },
        });

        // 2. audio context for both capture and playback
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: BRIDGE_SAMPLERATE,
        });
        if (this.audioContext.state === "suspended") {
            await this.audioContext.resume();
        }
        this.playbackTime = this.audioContext.currentTime;

        // 3. open the websocket to the server bridge
        const scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${scheme}://${window.location.host}/api/v1/telephone/audio-bridge`;
        this.ws = new WebSocket(url);
        this.ws.binaryType = "arraybuffer";

        this.ws.onmessage = (event) => {
            // received call audio (int16 PCM) -> schedule for playback
            this.playFrame(event.data);
        };
        this.ws.onclose = () => this.stop();
        this.ws.onerror = () => this.stop();

        await new Promise((resolve) => {
            if (this.ws.readyState === WebSocket.OPEN) {
                resolve();
            } else {
                this.ws.onopen = () => resolve();
            }
        });

        // 4. capture mic -> send PCM frames over the websocket
        this.micSource = this.audioContext.createMediaStreamSource(this.micStream);

        // ScriptProcessorNode is deprecated but universally supported and simplest
        // here; frame size 1024 ~ 21ms at 48k. (AudioWorklet is the modern path.)
        const frameSamples = 1024;
        this.processor = this.audioContext.createScriptProcessor(frameSamples, BRIDGE_CHANNELS, BRIDGE_CHANNELS);
        this.processor.onaudioprocess = (e) => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                return;
            }
            const input = e.inputBuffer.getChannelData(0); // Float32 [-1,1]
            const pcm = this.floatToInt16(input);
            try {
                this.ws.send(pcm.buffer);
            } catch (err) {
                // ignore send errors
            }
        };

        this.micSource.connect(this.processor);
        // processor must be connected to destination to run, but we don't want to
        // hear ourselves; route through a zero-gain node
        const mute = this.audioContext.createGain();
        mute.gain.value = 0;
        this.processor.connect(mute);
        mute.connect(this.audioContext.destination);
    }

    // play a received int16 PCM frame via Web Audio, scheduled back-to-back
    playFrame(arrayBuffer) {
        if (!this.audioContext) {
            return;
        }
        try {
            const int16 = new Int16Array(arrayBuffer);
            const float32 = this.int16ToFloat(int16);
            const buffer = this.audioContext.createBuffer(BRIDGE_CHANNELS, float32.length, BRIDGE_SAMPLERATE);
            buffer.getChannelData(0).set(float32);

            const source = this.audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(this.audioContext.destination);

            // schedule sequentially to avoid gaps/overlaps
            const now = this.audioContext.currentTime;
            if (this.playbackTime < now) {
                this.playbackTime = now;
            }
            source.start(this.playbackTime);
            this.playbackTime += buffer.duration;
        } catch (err) {
            // ignore malformed frames
        }
    }

    stop() {
        this.running = false;
        try { if (this.processor) this.processor.disconnect(); } catch (e) {}
        try { if (this.micSource) this.micSource.disconnect(); } catch (e) {}
        if (this.micStream) {
            this.micStream.getTracks().forEach((t) => t.stop());
        }
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            try { this.ws.close(); } catch (e) {}
        }
        if (this.audioContext) {
            try { this.audioContext.close(); } catch (e) {}
        }
        this.ws = null;
        this.processor = null;
        this.micSource = null;
        this.micStream = null;
        this.audioContext = null;
    }

    // ---- PCM conversion helpers ----

    floatToInt16(float32) {
        const out = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
            let s = Math.max(-1, Math.min(1, float32[i]));
            out[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return out;
    }

    int16ToFloat(int16) {
        const out = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
            out[i] = int16[i] / (int16[i] < 0 ? 0x8000 : 0x7FFF);
        }
        return out;
    }
}
