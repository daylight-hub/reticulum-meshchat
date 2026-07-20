# LCS MeshChat v1.4.0 - full codec support + regression fix + diagnostics

## What this addresses
Your last log showed Docker calls establishing then ending in ~2s with NO mic frames and
NO "received=" diagnostic - i.e. the browser audio bridge wasn't feeding/consuming audio,
so LXST timed out the call. This build hardens that path and adds diagnostics to pinpoint
it if it persists.

## Changes since the last (2880) build
1. frame_config sent ONCE up front (before the audio stream) instead of interleaved in
   the speaker pump loop - cleaner, can't disturb the binary audio stream.
2. Dynamic per-codec frame sizing retained (Opus 60ms=2880, Codec2 200/320/400ms) so all
   codecs get the right frame duration.
3. getUserMedia now logs a LOUD, clear error to the browser console if it fails (the most
   common reason the bridge silently doesn't start: page not on HTTPS, or mic permission
   denied).
4. Desktop mic fix (ringtone AudioContext release) + profile param hardening retained.

## Files
- package.json, package-lock.json                      (v1.4.0)
- meshchat.py                                           (frame_config sent once up front)
- src/backend/webrtc_audio_bridge.py                   (per-codec frame size + diagnostics)
- src/frontend/js/TelephoneAudioBridge.js              (dynamic frame size + loud mic errors)
- src/frontend/components/App.vue                       (global bridge + ringtone lifecycle)
- src/frontend/components/telephone/TelephonePage.vue  (profile param hardening)

## Apply + push
    Copy-Item -Path lcs-v140\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "v1.4.0: per-codec frame sizing, send frame_config up front, loud mic diagnostics"
    git config http.version HTTP/1.1
    git push origin lcs
    # after Actions rebuilds:
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## CRUCIAL - if audio still fails, capture the BROWSER CONSOLE (this is the missing piece)
The container log shows the server side; the browser side is where the bridge lives.
1. In the browser on the MeshChat page, press F12 -> Console tab.
2. Make a call.
3. Look for and copy any of these:
   - "[AudioBridge] getUserMedia failed ..."  -> mic/HTTPS/permission problem (the likely cause)
   - "failed to start audio bridge: ..."      -> bridge threw during setup
   - any red errors mentioning audio-bridge, WebSocket, or getUserMedia
4. Also grab the container log line "WebRTC bridge mic: received=N fed_to_mixer=M"
   (or note if it never appears).
Paste BOTH as text.

## Most likely cause (based on the symptom)
Calls dying in ~2s with no mic frames = the browser bridge isn't connecting. The #1 reason
is getUserMedia being blocked because the page isn't served over HTTPS (browsers only allow
mic access over HTTPS or localhost). Confirm you're reaching MeshChat via the HTTPS reverse
proxy (https://192.168.2.1:8443), NOT plain http://<ip>:8000. If you're on http, the mic is
blocked and that fully explains both directions failing.
