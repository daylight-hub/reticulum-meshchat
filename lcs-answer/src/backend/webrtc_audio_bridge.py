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
    from LXST.Sources import Source
    from LXST.Sinks import Sink
    LXST_AVAILABLE = True
except Exception:
    # LXST not importable (shouldn't happen in normal runs) - degrade gracefully
    Source = object
    Sink = object
    LXST_AVAILABLE = False


# audio format the bridge exchanges with the browser. LXST frames are raw PCM;
# the browser side must match this samplerate/channels when capturing and playing.
BRIDGE_SAMPLERATE = 48000
BRIDGE_CHANNELS = 1


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
            # frame is raw PCM bytes (or a buffer) coming from the receive pipeline
            self.bridge.queue_outgoing_to_browser(frame)
        except Exception as e:
            RNS.log(f"WebSocketAudioSink.handle_frame error: {e}", RNS.LOG_DEBUG)

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

            try:
                frame_samples = frame
                # apply any LXST filters (AGC, bandpass, echo) like LineSource does
                for f in self.filters:
                    try:
                        frame_samples = f.handle_frame(frame_samples, self.samplerate)
                    except Exception:
                        pass
                if self.sink and self.sink.can_receive(from_source=self):
                    self.sink.handle_frame(frame, self)
            except Exception as e:
                RNS.log(f"WebSocketAudioSource feed error: {e}", RNS.LOG_DEBUG)


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
            # inject our sink before LXST would build a LineSink
            try:
                if telephone.audio_output is None:
                    telephone.audio_output = bridge.make_sink()
                    RNS.log("WebRTC bridge: speaker sink injected", RNS.LOG_NOTICE)
            except Exception as e:
                RNS.log(f"WebRTC bridge: speaker inject failed: {e}", RNS.LOG_ERROR)
            return original_prepare(*args, **kwargs)
        setattr(telephone, prepare_name, prepare_wrapper)
    else:
        RNS.log("WebRTC bridge: could not find __prepare_dialling_pipelines; "
                "speaker bridging may not work on this LXST version", RNS.LOG_WARNING)

    # --- microphone: wrap the mangled __open_pipelines to swap in our source ---
    open_name = "_Telephone__open_pipelines"
    original_open = getattr(telephone, open_name, None)

    if original_open is not None:
        def open_wrapper(identity, *args, **kwargs):
            RNS.log("WebRTC bridge: __open_pipelines called (answering/connecting)", RNS.LOG_NOTICE)
            result = original_open(identity, *args, **kwargs)
            try:
                # LXST just built audio_input as a LineSource feeding transmit_mixer.
                # replace it with our WebSocketSource feeding the same sink.
                if getattr(telephone, "audio_input", None) is not None:
                    old = telephone.audio_input
                    sink = getattr(old, "sink", None)
                    RNS.log(f"WebRTC bridge: swapping mic (old={type(old).__name__}, sink={type(sink).__name__ if sink else None})", RNS.LOG_NOTICE)
                    try:
                        old.stop()
                    except Exception:
                        pass
                    ws_source = bridge.make_source(sink=sink)
                    ws_source.codec = getattr(old, "codec", None)
                    telephone.audio_input = ws_source
                    bridge.activate()
                    ws_source.start()
                    RNS.log("WebRTC bridge: microphone swapped to WebSocket source", RNS.LOG_NOTICE)
                else:
                    RNS.log("WebRTC bridge: no audio_input to swap after __open_pipelines", RNS.LOG_WARNING)
            except Exception as e:
                RNS.log(f"WebRTC bridge: mic swap failed: {e}", RNS.LOG_ERROR)
            return result
        setattr(telephone, open_name, open_wrapper)
    else:
        RNS.log("WebRTC bridge: could not find __open_pipelines; "
                "microphone bridging unavailable on this LXST version", RNS.LOG_WARNING)

    return telephone
