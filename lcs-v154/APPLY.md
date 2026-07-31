# LCS MeshChat v1.5.4 - restore working v1.5.0 audio + keep the library revert

## Where we are
- Reverting the libraries (v1.5.4) brought back the ringtone + answer button. Confirmed:
  the RNS/LXST version bump broke the telephone events.
- But audio was still dead both ways. Cause: changes I made AFTER v1.5.0 to the audio path
  (the speaker-side resample, and a websocket race-handling change) were still in place and
  were interfering.

## The fix
Restored the two audio files to EXACTLY their working v1.5.0 versions:
- src/backend/webrtc_audio_bridge.py      -> identical to v1.5.0 (resample removed)
- src/frontend/js/TelephoneAudioBridge.js -> identical to v1.5.0 (race change removed)
And kept the library pins from v1.5.4:
- rns==1.3.8, lxmf==1.0.1, lxst==0.5.0

So now EVERYTHING that touches calling - the libraries AND the audio bridge - matches the
v1.5.0 build where ringtone, button, and audio all worked. The only things kept from after
v1.5.0 are non-audio: the Tools additions (RNode tool, Bible), the LoRa presets, and the
harmless try/catch around the websocket handler.

## Files
- requirements.txt                          (pinned to v1.5.0 versions)
- package.json, package-lock.json           (v1.5.4)
- src/backend/webrtc_audio_bridge.py        (restored to v1.5.0)
- src/frontend/js/TelephoneAudioBridge.js   (restored to v1.5.0)
- src/frontend/components/App.vue           (v1.5.0 audio logic + harmless handler guard)

## Apply + push
    Copy-Item -Path lcs-v154\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.5.4: restore v1.5.0 audio path (remove resample + race change), keep library pin"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d
Then hard-refresh the browser.

## Verify after deploy
    docker compose exec reticulum-meshchat sh -c "pip show rns lxst lxmf | grep -E 'Name|Version'"
Should show rns 1.3.8, lxmf 1.0.1, lxst 0.5.0.

Then a call should have: ringtone + answer button (already working) AND audio both ways
(restored). This is functionally the v1.5.0 calling experience.

## What we GAVE UP to get back to working (honest)
- The Codec2 "deep and slow" speaker fix is removed (it was the resample). Codec2 over the
  Docker browser may again have that issue - but Opus (the normal WiFi/TCP path) works,
  which is what matters for browser calling. We can revisit Codec2 separately and carefully.
- The newer RNS/LXST are shelved until we can test a version bump against a live call
  without breaking events.

If audio works again after this, we have a solid known-good baseline to build on.
