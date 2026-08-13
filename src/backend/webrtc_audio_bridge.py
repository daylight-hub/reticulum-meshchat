# WebSocket audio bridge for running the LXST telephone inside Docker.
#
# Problem: LXST's Telephone captures/plays audio server-side via PulseAudio
# (LineSource/LineSink -> Backend). Inside a Docker container there is no
# microphone and no PulseAudio, so calls have no audio.
#
# Solution: when running in Docker, swap the Line source/sink for WebSocket-backed
# ones. The browser captures the microphone and streams PCM frames to the server
# over a WebSocket; the server streams received call audio back to the browser,
# which plays it via the Web Audio API. LXST's own codec/packetizer still runs
# server-side - we only replace the *local* audio endpoints (mic in, speaker out).
#
# This module provides:
#   - WebSocketAudioSink:   receives decoded call audio (handle_frame) -> browser
#   - WebSocketAudioSource: receives browser mic frames -> LXST transmit pipeline
#   - AudioBridge:          owns the per-call source/sink pair and the frame queues
#
# It is only used when meshchat detects it is running in Docker. On desktop the
# original LineSource/LineSink are used unchanged.

import time
import queue
import threading

import RNS

try:
    import numpy as np
except Exception:
    np = None

try:
    from LXST.Sources import Source
    from LXST.Sinks import Sink
    LXST_AVAILABLE = True
except Exception:
    # LXST not importable (shouldn't happen in normal runs) - degrade gracefully
    Source = object
    Sink = object
    LXST_AVAILABLE = False


# audio format the bridge exchanges with the browser (int16 mono PCM).
# LXST works internally with float numpy frames normalised to [-1, 1]; we convert
# between browser int16 PCM and LXST float frames at the sink/source boundary.
BRIDGE_SAMPLERATE = 48000
BRIDGE_CHANNELS = 1
INT16_MAX = 32767.0


class PassthroughCodec:
    """
    The Mixer calls source.codec.decode(frame) on frames from our source. We already
    hand it decoded numpy float arrays, so decode() just returns them unchanged.
    encode() is a no-op identity too (not used on the receive path, but defined for
    completeness).
    """
    def __init__(self):
        self.channels = BRIDGE_CHANNELS
        self.samplerate = BRIDGE_SAMPLERATE

    def decode(self, frame):
        return frame

    def encode(self, frame):
        return frame


class WebSocketAudioSink(Sink):
    """
    Stands in for the speaker (LineSink). LXST calls handle_frame() with decoded
    audio frames from the remote party; we hand them to the bridge, which forwards
    them to the browser over the websocket to be played.
    """

    def __init__(self, bridge):
        self.bridge = bridge
        self.released = False
        self.should_run = True
        self.samplerate = BRIDGE_SAMPLERATE
        self.channels = BRIDGE_CHANNELS

    def can_receive(self, from_source=None):
        return not self.released

    def handle_frame(self, frame, source=None):
        if self.released:
            return
        try:
            # LXST delivers a numpy float array (samples, channels) in [-1, 1].
            # convert to int16 mono PCM bytes for the browser to play.
            if np is not None and hasattr(frame, "shape"):
                arr = frame
                # downmix to mono if needed
                if arr.ndim == 2 and arr.shape[1] > 1:
                    arr = arr.mean(axis=1)
                arr = arr.reshape(-1)
                # float [-1,1] -> int16
                pcm = np.clip(arr, -1.0, 1.0)
                pcm = (pcm * INT16_MAX).astype(np.int16)
                self.bridge.queue_outgoing_to_browser(pcm.tobytes())
            else:
                # fallback: pass through whatever we got
                self.bridge.queue_outgoing_to_browser(bytes(frame))
        except Exception as e:
            RNS.log(f"WebSocketAudioSink.handle_frame error: {e}", RNS.LOG_DEBUG)

    # LXST calls start()/stop()/enable_low_latency() on the speaker sink - provide them
    def start(self):
        self.should_run = True

    def stop(self):
        self.should_run = False

    def enable_low_latency(self):
        pass

    def release(self):
        self.released = True
        self.should_run = False


class WebSocketAudioSource(Source):
    """
    Stands in for the microphone (LineSource). Runs an ingest loop that pulls PCM
    frames the browser sent over the websocket and pushes them into LXST's
    transmit pipeline via sink.handle_frame(), exactly like LineSource does.
    """

    def __init__(self, bridge, sink=None, target_frame_ms=20, codec=None, filters=None):
        self.bridge = bridge
        self.sink = sink
        self._codec = codec
        self.filters = filters or []
        self.target_frame_ms = target_frame_ms
        self.samplerate = BRIDGE_SAMPLERATE
        self.channels = BRIDGE_CHANNELS
        self.should_run = False
        self.released = False
        self.ingest_thread = None

    @property
    def codec(self):
        return self._codec

    @codec.setter
    def codec(self, codec):
        self._codec = codec

    def start(self):
        if self.should_run:
            return
        self.should_run = True
        self.ingest_thread = threading.Thread(target=self.__ingest_job, daemon=True)
        self.ingest_thread.start()

    def stop(self):
        self.should_run = False

    def release(self):
        self.released = True
        self.should_run = False

    def __ingest_job(self):
        # pull mic frames the browser queued and feed them to the transmit sink
        frames_received = 0
        frames_fed = 0
        last_log = time.time()
        while self.should_run and not self.released:
            try:
                frame = self.bridge.get_incoming_from_browser(timeout=0.5)
            except queue.Empty:
                continue
            except Exception as e:
                RNS.log(f"WebSocketAudioSource ingest error: {e}", RNS.LOG_DEBUG)
                continue

            if frame is None:
                continue

            frames_received += 1

            try:
                # browser sends int16 mono PCM bytes; convert to a numpy float array
                # shaped (samples, channels) in [-1, 1], which is what the Mixer/codec expect.
                if np is not None:
                    int16 = np.frombuffer(frame, dtype=np.int16)
                    frame_samples = (int16.astype(np.float32) / INT16_MAX).reshape(-1, 1)
                else:
                    frame_samples = frame

                # apply any LXST filters (AGC, bandpass, echo) like LineSource does
                for f in self.filters:
                    try:
                        frame_samples = f.handle_frame(frame_samples, self.samplerate)
                    except Exception:
                        pass

                if self.sink and self.sink.can_receive(from_source=self):
                    self.sink.handle_frame(frame_samples, self)
                    frames_fed += 1
                    # one-time diagnostic: log frame shape + mixer target on first frame
                    if frames_fed == 1:
                        try:
                            shape = getattr(frame_samples, "shape", None)
                            target = getattr(self.sink, "target_frame_ms", None)
                            samplerate = getattr(self.sink, "samplerate", None)
                            RNS.log(f"WebRTC bridge mic DIAG: frame_shape={shape} src_samplerate={self.samplerate} "
                                    f"mixer_target_frame_ms={target} mixer_samplerate={samplerate}", RNS.LOG_NOTICE)
                        except Exception:
                            pass
            except Exception as e:
                RNS.log(f"WebSocketAudioSource feed error: {e}", RNS.LOG_NOTICE)

            # periodic diagnostic so we can see if mic frames flow to the mixer
            if time.time() - last_log >= 3.0:
                RNS.log(f"WebRTC bridge mic: received={frames_received} fed_to_mixer={frames_fed} "
                        f"sink={type(self.sink).__name__ if self.sink else None}", RNS.LOG_NOTICE)
                last_log = time.time()


class AudioBridge:
    """
    Owns the queues and the source/sink pair for browser <-> LXST audio.
    One bridge is shared by the app; it exposes:
      - queue_outgoing_to_browser(frame): called by the sink (call audio -> browser)
      - get_incoming_from_browser(): called by the source (browser mic -> LXST)
      - push_mic_frame(frame): called by the websocket handler when the browser
        sends a mic frame
      - drain_speaker_frames(): called by the websocket handler to get frames to
        send to the browser
    """

    def __init__(self, max_queue=50):
        # browser mic -> LXST
        self.incoming = queue.Queue(maxsize=max_queue)
        # LXST call audio -> browser
        self.outgoing = queue.Queue(maxsize=max_queue)
        self.active = False
        # how many samples per frame the browser should send (set per call so Opus
        # and Codec2 frame durations match the mixer target). 2880 = 60ms @ 48k default.
        self.target_frame_samples = 2880

    def set_target_frame_samples(self, samples):
        if samples and samples > 0:
            self.target_frame_samples = int(samples)

    # ---- lifecycle ----

    def activate(self):
        self.active = True
        # clear any stale frames from a previous call
        self.__drain(self.incoming)
        self.__drain(self.outgoing)

    def deactivate(self):
        self.active = False
        self.__drain(self.incoming)
        self.__drain(self.outgoing)

    def __drain(self, q):
        try:
            while True:
                q.get_nowait()
        except queue.Empty:
            pass

    # ---- sink side (call audio -> browser) ----

    def queue_outgoing_to_browser(self, frame):
        if not self.active:
            return
        try:
            self.outgoing.put_nowait(frame)
        except queue.Full:
            # drop oldest to keep latency bounded
            try:
                self.outgoing.get_nowait()
                self.outgoing.put_nowait(frame)
            except Exception:
                pass

    def drain_speaker_frames(self, max_frames=10):
        frames = []
        for _ in range(max_frames):
            try:
                frames.append(self.outgoing.get_nowait())
            except queue.Empty:
                break
        return frames

    # ---- source side (browser mic -> LXST) ----

    def push_mic_frame(self, frame):
        if not self.active:
            return
        try:
            self.incoming.put_nowait(frame)
        except queue.Full:
            try:
                self.incoming.get_nowait()
                self.incoming.put_nowait(frame)
            except Exception:
                pass

    def get_incoming_from_browser(self, timeout=0.5):
        return self.incoming.get(timeout=timeout)

    # ---- factory for the source/sink pair ----

    def make_sink(self):
        return WebSocketAudioSink(self)

    def make_source(self, sink=None, target_frame_ms=20, codec=None, filters=None):
        return WebSocketAudioSource(self, sink=sink, target_frame_ms=target_frame_ms,
                                    codec=codec, filters=filters)


def install_bridge_on_telephone(telephone, bridge):
    """
    Patch an LXST Telephone instance so its local audio endpoints use the
    WebSocket bridge instead of PulseAudio LineSource/LineSink. Docker-only.

    Strategy (kept surgical to limit coupling to LXST internals):
      - Speaker: pre-set telephone.audio_output to our sink before pipelines open.
        LXST only builds a LineSink `if audio_output == None`, so ours is kept.
        We re-inject on each call because LXST resets audio_output between calls.
      - Microphone: LXST always rebuilds audio_input as a LineSource, so we wrap
        the private pipeline-open methods; after LXST builds them, we stop its
        LineSource and substitute our WebSocketSource feeding the same sink.

    This relies on LXST's private method names (name-mangled as
    _Telephone__open_pipelines etc). If a future LXST changes these, the wrap
    will no-op for the mic and we log a clear warning rather than crash.
    """
    import types

    RNS.log("WebRTC bridge: installing on telephone instance", RNS.LOG_NOTICE)

    # --- speaker: wrap the mangled __prepare_dialling_pipelines to inject our sink ---
    prepare_name = "_Telephone__prepare_dialling_pipelines"
    original_prepare = getattr(telephone, prepare_name, None)

    if original_prepare is not None:
        def prepare_wrapper(*args, **kwargs):
            # Inject our sink before LXST would build a LineSink (PulseAudio speaker),
            # which does not exist in Docker.
            try:
                if telephone.audio_output is None:
                    telephone.audio_output = bridge.make_sink()
                    RNS.log("WebRTC bridge: speaker sink injected", RNS.LOG_NOTICE)
            except Exception as e:
                RNS.log(f"WebRTC bridge: speaker inject failed: {e}", RNS.LOG_ERROR)

            # CRITICAL: this method is called by __reset_dialling_pipelines(), which runs
            # in __caller_identified() IMMEDIATELY BEFORE signal(STATUS_RINGING). If
            # anything in here raises, the call never reaches RINGING - the status stays
            # at AVAILABLE(3), no ringtone plays and no answer button appears. In Docker
            # the dial-tone ToneSource can fail because there is no audio backend, so we
            # must swallow errors here rather than let them abort the incoming call.
            try:
                return original_prepare(*args, **kwargs)
            except Exception as e:
                RNS.log(f"WebRTC bridge: prepare_dialling_pipelines failed (continuing so "
                        f"the call can still ring): {e}", RNS.LOG_WARNING)

                # Build the minimum receive pipeline ourselves so the call still works.
                try:
                    from LXST.Mixer import Mixer
                    from LXST.Pipeline import Pipeline
                    from LXST.Codecs import Null
                    t = telephone
                    if t.audio_output is None:
                        t.audio_output = bridge.make_sink()
                    if getattr(t, "receive_mixer", None) is None:
                        t.receive_mixer = Mixer(target_frame_ms=t.target_frame_time_ms,
                                                gain=t.receive_gain)
                    # no dial tone in Docker - it needs an audio backend we do not have
                    t.dial_tone = None
                    if getattr(t, "receive_pipeline", None) is None:
                        t.receive_pipeline = Pipeline(source=t.receive_mixer,
                                                      codec=Null(),
                                                      sink=t.audio_output)
                    RNS.log("WebRTC bridge: built fallback receive pipeline (no dial tone)",
                            RNS.LOG_NOTICE)
                except Exception as inner:
                    RNS.log(f"WebRTC bridge: fallback receive pipeline failed: {inner}",
                            RNS.LOG_ERROR)
                return None
        setattr(telephone, prepare_name, prepare_wrapper)
    else:
        RNS.log("WebRTC bridge: could not find __prepare_dialling_pipelines; "
                "speaker bridging may not work on this LXST version", RNS.LOG_WARNING)

    # --- microphone + full pipeline: REPLACE __open_pipelines entirely ---
    # The original builds a LineSource (PulseAudio mic) unconditionally, which throws
    # in Docker before we could swap it. So we replace the whole method with a copy
    # that builds our WebSocketAudioSource instead. Faithful to LXST 0.5.0's version.
    open_name = "_Telephone__open_pipelines"
    original_open = getattr(telephone, open_name, None)

    if original_open is not None:
        def open_pipelines_override(identity, *args, **kwargs):
            RNS.log("WebRTC bridge: __open_pipelines (override) called", RNS.LOG_NOTICE)
            try:
                from LXST.Mixer import Mixer
                from LXST.Pipeline import Pipeline
                from LXST.Network import Packetizer, LinkSource
                from LXST.Codecs import Raw
                import LXST.Primitives.Telephony as Tel
                Signalling = Tel.Signalling
                BandPass = getattr(Tel, "BandPass", None)
                AGC = getattr(Tel, "AGC", None)
                EchoSuppressor = getattr(Tel, "EchoSuppressor", None)
                Profiles = getattr(Tel, "Profiles", None)

                t = telephone
                with t.pipeline_lock:
                    if not t.active_call.get_remote_identity() == identity:
                        RNS.log("Identity mismatch while opening call pipelines, tearing down call", RNS.LOG_ERROR)
                        t.hangup()
                        return

                    if not hasattr(t.active_call, "pipelines_opened"):
                        t.active_call.pipelines_opened = False
                    if t.active_call.pipelines_opened:
                        RNS.log("Pipelines already opened", RNS.LOG_ERROR)
                        return

                    if t.active_call.is_incoming:
                        t.signal(Signalling.STATUS_CONNECTING, t.active_call)

                    # build the same filter chain LXST would
                    filter_chain = []
                    if getattr(t, "use_bandpass", False) and BandPass:
                        filter_chain.append(BandPass(250, 8500))
                    if getattr(t, "use_agc", False) and AGC:
                        filter_chain.append(AGC(target_level=-15.0))
                    if getattr(t, "use_echo_cancellation", False) and EchoSuppressor:
                        t.active_call.echo_suppressor = EchoSuppressor()
                        t.receive_mixer.reference_outs = [t.active_call.echo_suppressor]
                        filter_chain.append(t.active_call.echo_suppressor)
                    t.active_call.filters = filter_chain

                    # this injects our speaker sink (audio_output) and builds receive pipeline
                    getattr(t, "_Telephone__prepare_dialling_pipelines")()

                    t.active_call.packetizer = Packetizer(t.active_call, failure_callback=getattr(t, "_Telephone__packetizer_failure"))
                    if Profiles and t.active_call.call_mode == Profiles.MODE_HALF_DUPLEX:
                        t.active_call.packetizer.squelch()

                    t.transmit_mixer = Mixer(target_frame_ms=t.target_frame_time_ms, gain=t.transmit_gain)

                    # tell the browser how many samples per frame to send so the frame
                    # duration matches the codec (Opus 60ms, Codec2 200-400ms). the mixer
                    # doesn't compute samples_per_frame until a frame flows, so we derive it
                    # from the target frame time and our source samplerate (48k). we also
                    # read the mixer's possibly-quantized target if available.
                    try:
                        target_ms = getattr(t.transmit_mixer, "target_frame_ms", None) or t.target_frame_time_ms
                        browser_spf = int(round((target_ms / 1000.0) * BRIDGE_SAMPLERATE))
                        if browser_spf > 0:
                            bridge.set_target_frame_samples(browser_spf)
                            RNS.log(f"WebRTC bridge: target frame {target_ms}ms -> {browser_spf} samples "
                                    f"@ {BRIDGE_SAMPLERATE}Hz for browser mic", RNS.LOG_NOTICE)
                    except Exception as e:
                        RNS.log(f"WebRTC bridge: could not compute target frame size: {e}", RNS.LOG_WARNING)

                    # *** THE KEY CHANGE: WebSocket mic source instead of LineSource ***
                    ws_source = bridge.make_source(sink=t.transmit_mixer, filters=t.active_call.filters, codec=PassthroughCodec())
                    t.audio_input = ws_source
                    bridge.activate()
                    ws_source.start()
                    RNS.log("WebRTC bridge: WebSocket microphone source installed", RNS.LOG_NOTICE)

                    t.transmit_pipeline = Pipeline(source=t.transmit_mixer, codec=t.transmit_codec, sink=t.active_call.packetizer)

                    t.active_call.audio_source = LinkSource(link=t.active_call, signalling_receiver=t, sink=t.receive_mixer)
                    t.receive_mixer.set_source_max_frames(t.active_call.audio_source, t.target_buffer_frames)

                    t.active_call.pipelines_opened = True
                    t.signal(Signalling.STATUS_ESTABLISHED, t.active_call)
                    RNS.log("WebRTC bridge: pipelines opened, call established", RNS.LOG_NOTICE)
            except Exception as e:
                import traceback
                RNS.log(f"WebRTC bridge: open_pipelines override failed: {e}", RNS.LOG_ERROR)
                RNS.log(traceback.format_exc(), RNS.LOG_ERROR)
                try:
                    telephone.hangup()
                except Exception:
                    pass
        setattr(telephone, open_name, open_pipelines_override)
    else:
        RNS.log("WebRTC bridge: could not find __open_pipelines; "
                "microphone bridging unavailable on this LXST version", RNS.LOG_WARNING)

    # --- override __reconfigure_transmit_pipeline (runs on profile switch) ---
    # When the remote negotiates a codec/profile mid-call, LXST rebuilds the transmit
    # pipeline with a LineSource (PulseAudio mic), which crashes in Docker (no libpulse).
    # We replace it with a version that rebuilds using our WebSocket mic source and
    # updates the browser frame size for the new profile.
    reconf_name = "_Telephone__reconfigure_transmit_pipeline"
    original_reconf = getattr(telephone, reconf_name, None)

    if original_reconf is not None:
        def reconfigure_transmit_override(*args, **kwargs):
            RNS.log("WebRTC bridge: __reconfigure_transmit_pipeline (override) called", RNS.LOG_NOTICE)
            try:
                from LXST.Mixer import Mixer
                from LXST.Pipeline import Pipeline
                import LXST.Primitives.Telephony as Tel
                Signalling = Tel.Signalling

                t = telephone
                if t.transmit_pipeline and t.call_status == Signalling.STATUS_ESTABLISHED:
                    # stop the old chain
                    try:
                        if t.audio_input: t.audio_input.stop()
                    except Exception:
                        pass
                    try:
                        t.transmit_mixer.stop()
                    except Exception:
                        pass
                    try:
                        t.transmit_pipeline.stop()
                    except Exception:
                        pass

                    # rebuild mixer for the (possibly new) target frame time
                    t.transmit_mixer = Mixer(target_frame_ms=t.target_frame_time_ms, gain=t.transmit_gain)

                    # update the browser's mic frame size for the new profile
                    try:
                        target_ms = getattr(t.transmit_mixer, "target_frame_ms", None) or t.target_frame_time_ms
                        browser_spf = int(round((target_ms / 1000.0) * BRIDGE_SAMPLERATE))
                        if browser_spf > 0:
                            bridge.set_target_frame_samples(browser_spf)
                            RNS.log(f"WebRTC bridge: reconfigured target frame {target_ms}ms -> {browser_spf} samples", RNS.LOG_NOTICE)
                    except Exception:
                        pass

                    # rebuild our WebSocket mic source instead of a LineSource
                    ws_source = bridge.make_source(sink=t.transmit_mixer,
                                                   filters=t.active_call.filters,
                                                   codec=PassthroughCodec())
                    t.audio_input = ws_source

                    t.transmit_pipeline = Pipeline(source=t.transmit_mixer,
                                                   codec=t.transmit_codec,
                                                   sink=t.active_call.packetizer)

                    try:
                        t.transmit_mixer.mute(getattr(t, "_Telephone__transmit_muted", False))
                    except Exception:
                        pass
                    t.transmit_mixer.start()
                    ws_source.start()
                    t.transmit_pipeline.start()
                    RNS.log("WebRTC bridge: transmit pipeline reconfigured with WebSocket mic", RNS.LOG_NOTICE)
            except Exception as e:
                import traceback
                RNS.log(f"WebRTC bridge: reconfigure override failed: {e}", RNS.LOG_ERROR)
                RNS.log(traceback.format_exc(), RNS.LOG_ERROR)
        setattr(telephone, reconf_name, reconfigure_transmit_override)
    else:
        RNS.log("WebRTC bridge: could not find __reconfigure_transmit_pipeline; "
                "profile switches may crash audio on this LXST version", RNS.LOG_WARNING)

    return telephone
