# LCS MeshChat - fix the JavaScript crash that broke EVERYTHING

## THE root cause (found in your browser console)
    Uncaught ReferenceError: data is not defined
        at onWebsocketMessage

When I added the use_browser_audio handling, I referenced a variable named "data" that
doesn't exist - the parsed message in that function is called "json". This ReferenceError
threw on EVERY websocket message, crashing the entire message handler. That's why:
  - isDocker never got applied (the "Add LCS Interfaces" button stayed)
  - the restart button did nothing
  - call events never processed
  - the audio bridge never started -> NO AUDIO either direction

One broken line took down the whole websocket message pipeline. This is the bug behind
all the recent symptoms.

## The fix
Changed `data.use_browser_audio` to `json.use_browser_audio` (the correct variable name,
matching every other case in that handler).

## File
- src/frontend/components/App.vue

## Apply + push
    Copy-Item -Path lcs-jsfix\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "Fix ReferenceError (data->json) that crashed the websocket message handler"
    git config http.version HTTP/1.1
    git push origin lcs
    # after Actions rebuilds:
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Confirm it works
Load https://liberty.local:8443 and:
1. The "Add LCS Interfaces" button should be GONE (isDocker now applies correctly).
2. The browser console (F12) should have NO "data is not defined" error.
3. Make a call and check:
     docker compose logs --tail=30 -f | grep "bridge mic"
   You should FINALLY see "WebRTC bridge mic: received=N fed_to_mixer=N" climbing.
   That = mic audio flowing. Audio should work both directions.

## Why this explains everything
Every symptom (button showing, restart dead, no audio, empty-looking behavior) traces to
the websocket handler crashing on every message. The backend was always fine - this was a
frontend typo I introduced. Sorry for the runaround; the console error pinpointed it.
