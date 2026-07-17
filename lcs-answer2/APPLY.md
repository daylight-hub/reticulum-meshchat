# LCS MeshChat - fix answer (call was crashing on LineSource in Docker)

## Root cause (from your logs)
The log showed:
  WebRTC bridge: __open_pipelines called
  on_telephone_ended            <- call died immediately, no "mic swap" line

LXST's __open_pipelines builds a LineSource (PulseAudio microphone) UNCONDITIONALLY.
In Docker there's no PulseAudio, so that line throws - crashing the answer before our
swap code (which ran afterward) could execute. The call then hung up.

## The fix
Instead of wrapping __open_pipelines and swapping after (too late - it already crashed),
we now REPLACE __open_pipelines entirely with a copy that builds our WebSocket mic source
instead of LineSource. Everything else in the method is faithful to LXST 0.5.0.

Also fixed a secondary crash: on_telephone_call_ended threw on a None identity, which was
masking errors in the log.

## Files
- src/backend/webrtc_audio_bridge.py   (full __open_pipelines override)
- meshchat.py                          (None-guard on call-ended + deactivate bridge)

## Apply + redeploy
    Copy-Item -Path lcs-answer2\* -Destination . -Recurse -Force
    git add -A
    git commit -m "Fix Docker answer: replace __open_pipelines to use WebSocket mic (LineSource crashed)"
    git config http.version HTTP/1.1
    git push origin lcs
    # after Actions rebuilds:
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## After redeploy - capture the log on answer again
    docker compose logs --tail=40 -f
Expected NEW lines when you answer:
  WebRTC bridge: __open_pipelines (override) called
  WebRTC bridge: WebSocket microphone source installed
  WebRTC bridge: pipelines opened, call established     <- THIS means answer worked!

If instead you see "open_pipelines override failed: <error>" + a traceback, paste it -
that error names exactly what still needs fixing.

## Honest status
- This should make the call ANSWER and CONNECT (status established) without crashing.
- Whether AUDIO actually flows is the next question. The browser mic frames are passed
  as raw bytes; LXST's Mixer may expect a specific frame format. If the call connects but
  is silent/garbled, that's the format tuning - paste what you hear + any log lines and
  I'll adjust the frame handling. But first we need it to connect, which this fixes.
