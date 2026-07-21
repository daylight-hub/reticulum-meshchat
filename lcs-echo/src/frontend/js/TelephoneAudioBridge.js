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
        try {
            this.micStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    channelCount: BRIDGE_CHANNELS,
                    sampleRate: BRIDGE_SAMPLERATE,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                },
            });
        } catch (err) {
            // most common cause: page not served over HTTPS (getUserMedia needs a secure
            // context) or microphone permission denied. surface it loudly.
            console.error("[AudioBridge] getUserMedia failed - mic will not work. " +
                "Ensure the page is served over HTTPS (or localhost) and mic permission is granted.", err);
            this.running = false;
            throw err;
        }

        // 2. audio context for both capture and playback
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)({
            sampleRate: BRIDGE_SAMPLERATE,
        });
        if (this.audioContext.state === "suspended") {
            await this.audioContext.resume();
        }
        this.playbackTime = this.audioContext.currentTime;

        // Route received audio through a MediaStreamDestination -> <audio> element,
        // NOT straight to audioContext.destination. The browser's echo canceller can
        // only cancel audio it plays through a media element / WebRTC path; audio sent
        // directly to audioContext.destination is invisible to the AEC, so it leaks
        // into the mic and the far end hears themselves. Playing via an <audio> element
        // fed by a MediaStream lets the AEC use it as the echo reference.
        this.playbackDestination = this.audioContext.createMediaStreamDestination();
        this.playbackAudioEl = new Audio();
        this.playbackAudioEl.srcObject = this.playbackDestination.stream;
        this.playbackAudioEl.autoplay = true;
        // must actually play for the AEC reference to be active
        try { await this.playbackAudioEl.play(); } catch (e) { /* autoplay may need gesture */ }

        // 3. open the websocket to the server bridge
        const scheme = window.location.protocol === "https:" ? "wss" : "ws";
        const url = `${scheme}://${window.location.host}/api/v1/telephone/audio-bridge`;
        this.ws = new WebSocket(url);
        this.ws.binaryType = "arraybuffer";

        this.ws.onmessage = (event) => {
            // text message = control (frame size); binary = call audio to play
            if (typeof event.data === "string") {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg && msg.type === "frame_config" && msg.frame_samples) {
                        // backend tells us the exact mic frame size to send so it matches
                        // the codec's frame duration (Opus 60ms, Codec2 200-400ms, etc.)
                        this.outputFrameSamples = msg.frame_samples;
                    }
                } catch (e) { /* ignore malformed control messages */ }
                return;
            }
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

        // Each frame we send must match the codec's frame duration, because LXST's mixer
        // passes frames straight to the encoder. That target differs by profile:
        //   Opus (MEDIUM/HIGH/MAX): 60 ms  = 2880 samples @ 48k
        //   Codec2 LOW:            200 ms  = 9600 samples
        //   Codec2 VERY_LOW:       320 ms  = 15360 samples
        //   Codec2 ULTRA_LOW:      400 ms  = 19200 samples
        // The backend sends the exact size via a "frame_config" message when the call
        // opens; until then we default to 60 ms (the common Opus case). We re-chunk the
        // captured audio into exactly that many samples per frame.
        this.outputFrameSamples = Math.round(BRIDGE_SAMPLERATE * 0.06); // 2880 default
        this._sendBuffer = new Float32Array(0);

        const captureSize = 4096;
        this.processor = this.audioContext.createScriptProcessor(captureSize, BRIDGE_CHANNELS, BRIDGE_CHANNELS);
        this.processor.onaudioprocess = (e) => {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                return;
            }
            const input = e.inputBuffer.getChannelData(0); // Float32 [-1,1]

            // append incoming samples to our pending buffer
            const merged = new Float32Array(this._sendBuffer.length + input.length);
            merged.set(this._sendBuffer, 0);
            merged.set(input, this._sendBuffer.length);

            // emit as many full target-size frames as we have accumulated
            const frameSamples = this.outputFrameSamples;
            let offset = 0;
            while (merged.length - offset >= frameSamples) {
                const frame = merged.subarray(offset, offset + frameSamples);
                const pcm = this.floatToInt16(frame);
                try {
                    this.ws.send(pcm.buffer);
                } catch (err) {
                    // ignore send errors
                }
                offset += frameSamples;
            }
            // keep the remainder for next time
            this._sendBuffer = merged.slice(offset);
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
            // route to the MediaStreamDestination (AEC-visible), not audioContext.destination
            source.connect(this.playbackDestination || this.audioContext.destination);

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
        if (this.playbackAudioEl) {
            try { this.playbackAudioEl.pause(); } catch (e) {}
            try { this.playbackAudioEl.srcObject = null; } catch (e) {}
            this.playbackAudioEl = null;
        }
        this.playbackDestination = null;
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
