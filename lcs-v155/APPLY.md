# LCS MeshChat v1.5.5 - fix the audio bridge crash (re-applied on the working base)

## Your console error
    failed to start audio bridge: TypeError: Cannot read properties of null
    (reading 'createMediaStreamSource')

## What happened
This is the SAME race-condition crash I fixed back in v1.5.3 - but when I reverted the
audio files to v1.5.0 (to fix the codec problem), that revert accidentally REMOVED the
race fix too. So the crash came back, and it kills audio in BOTH directions on every codec
(the bridge crashes before it ever sends/receives a frame).

## The fix (surgical - one file)
Re-applied ONLY the race-condition fix to the current bridge:
- Don't wire websocket onclose/onerror -> stop() until AFTER the mic is fully set up.
- Treat an early websocket close/error during startup as a clean failure, not a crash.
- Bail out cleanly if teardown happened mid-startup.
Everything else (the v1.5.0 audio path, per-codec sizing, v1.5.0-floor libraries that gave
you working incoming+outgoing calls) is unchanged.

## Files
- src/frontend/js/TelephoneAudioBridge.js   (race fix only)
- package.json, package-lock.json           (v1.5.5)
- requirements.txt                          (unchanged: rns 1.3.8 / lxmf 1.0.1 / lxst 0.5.0)

## Apply + push
    Copy-Item -Path lcs-v155\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.5.5: re-apply audio bridge race-condition fix (null micStream crash)"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d
Then HARD-REFRESH the browser (Ctrl+Shift+R) - the new bundle must load.

## Test
Make a call (both directions). Audio should now work.
- Confirm no "failed to start audio bridge" error in the console (F12).

## If audio STILL fails after this (but no crash)
Then the audio-bridge websocket itself isn't staying connected. With the crash gone, the
console will now show a clean "audio-bridge websocket failed to open/closed before opening"
instead. If you see THAT, it's the nginx proxy dropping the /api/v1/telephone/audio-bridge
websocket - tell me and I'll give you the proxy fix (upgrade headers on that path). But the
crash had to be fixed first to even see that clearly.
