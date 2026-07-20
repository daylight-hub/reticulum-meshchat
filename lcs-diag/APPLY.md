# LCS MeshChat - DIAGNOSTIC build (find why only MEDIUM sends mic in Docker)

This is a diagnostic build to pinpoint the Docker mic-per-codec issue. It adds logging;
it does not change behavior. Deploy it, make a HIGH-quality call, and send me the log.

## File
- src/backend/webrtc_audio_bridge.py   (adds frame-shape + mixer-target diagnostics)

## Apply + redeploy
    Copy-Item -Path lcs-diag\src\backend\webrtc_audio_bridge.py -Destination src\backend\webrtc_audio_bridge.py -Force
    git add src/backend/webrtc_audio_bridge.py
    git commit -m "Add mic diagnostics for per-codec Docker audio"
    git config http.version HTTP/1.1
    git push origin lcs
    # after Actions rebuilds:
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Capture the log - IMPORTANT: do this for a HIGH (or MAX) quality call
1. Start the log:   docker compose logs --tail=60 -f
2. Make a call set to HIGH quality, talk for ~5 seconds.
3. Copy everything and paste it as TEXT (not a file - files come through empty).

## What I'm looking for in the log
- "WebRTC bridge mic DIAG: frame_shape=... mixer_target_frame_ms=... mixer_samplerate=..."
  -> tells me the frame size vs what the codec expects
- "WebRTC bridge mic: received=N fed_to_mixer=M"
  -> whether frames still reach the mixer on HIGH
- Any LXST "Error while mixing frame on Mixer: ..." lines
  -> the actual reason HIGH-quality frames are rejected
- "WebSocketAudioSource feed error: ..." (now logged at NOTICE so it shows)

Paste those and I'll have the exact fix - almost certainly a frame-size vs codec
mismatch that I'll correct in the frame chunking.
