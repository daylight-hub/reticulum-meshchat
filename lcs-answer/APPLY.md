# LCS MeshChat - fix answer button + outgoing calls in Docker

## What this fixes
- "Please select input microphone" blocking outgoing calls in Docker (there are no
  server audio devices in Docker - the browser provides them). Now the device checks
  are skipped in Docker.
- Answer button not answering: fixed a real bug in the audio bridge where the private
  method wrapper was passing the wrong first argument (self vs identity), which broke
  the pipeline swap on answer. Also added detailed logging so we can see exactly what
  happens during answer/connect.

## Files
- src/frontend/components/telephone/TelephonePage.vue  (skip device checks in Docker)
- src/backend/webrtc_audio_bridge.py                   (wrapper arg fix + diagnostics)

## Apply (repo root, on lcs)
    Copy-Item -Path lcs-answer\* -Destination . -Recurse -Force
    npm run build-frontend      # want: ✓ built
    git add -A
    git commit -m "Fix Docker answer/call: skip device checks, fix bridge wrapper args, add logging"
    git config http.version HTTP/1.1
    git push origin lcs

## Then rebuild + redeploy
    cd /opt/reticulum-meshchat
    docker compose pull
    docker compose up -d

## IMPORTANT - after redeploy, capture the log during an answer
This build adds NOTICE-level logging to the bridge. When you answer an incoming call,
run this and paste what appears:
    docker compose logs --tail=30 -f
Look for lines starting "WebRTC bridge:" - they trace the answer:
  - "__open_pipelines called" = answer reached the pipeline setup
  - "speaker sink injected" = speaker bridged OK
  - "swapping mic ... " / "microphone swapped to WebSocket source" = mic bridged OK
  - "mic swap failed: <error>" = tells us EXACTLY what's wrong if it still fails

These log lines are how we finish this - they'll show whether the answer now works and,
if not, precisely where it breaks. Please paste them from your next answer attempt.
