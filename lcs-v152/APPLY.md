# LCS MeshChat v1.5.2 - restore incoming-call UI (ringtone + answer/end buttons)

## Your symptoms
After the v1.5.1 version bump: no ringtone on incoming calls, no green answer / red end
buttons on the home page sidebar, and no audio once answered from the phone page.

## What these have in common
All three (ringtone, answer/end buttons, audio bridge) are driven by the same websocket
message handler (onWebsocketMessage). If that handler throws on ONE message, it stops
processing ALL further events - so the ringtone never plays, the buttons never appear
(they depend on getTelephoneStatus running), and the audio bridge never starts. This is
the same class of bug we hit before with the data/json and prime errors.

## What I changed
Wrapped onWebsocketMessage in try/catch so a single bad or unexpected message can no
longer kill all event handling. Also made 'incoming_audio_call' refresh telephone status
(so the answer/end buttons appear for that path too, matching 'telephone_ringing').

I verified against the new libraries that:
- the telephone callbacks (ringing/established/ended) still exist in LXST 0.5.1
- the call status enum is unchanged (RINGING=4, ESTABLISHED=6), so the button conditions
  are still correct
So the code paths are intact; the likely failure was a runtime throw in the handler, which
this now contains.

## Files
- package.json, package-lock.json        (v1.5.2)
- src/frontend/components/App.vue         (hardened message handler)

## Apply + push
    Copy-Item -Path lcs-v152\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add package.json package-lock.json src/frontend/components/App.vue
    git commit -m "v1.5.2: harden websocket handler so incoming-call UI (ringtone, answer/end buttons, audio) works"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d
Then hard-refresh the browser (new JS bundle) or clear site data.

## IMPORTANT - if it still doesn't work, grab the browser console
This hardening may fix it, but to be certain of the ROOT cause I need the browser console
(it's the one thing I can't see from here, and it pinpointed the last two bugs instantly):
1. At https://liberty.local:8443, press F12 -> Console.
2. Before the call, paste this to log every event that arrives:
       WebSocketConnection.on("message", (m) => console.log("WS:", JSON.parse(m.data).type))
3. Have the phone call you.
4. Tell me:
   - Do you see "WS: telephone_ringing" logged? (if NO -> backend isn't sending it)
   - Any RED errors, especially at onWebsocketMessage / startRingtone / App.vue?
Paste that as text and I'll fix the exact cause.

## Note
Desktop is unaffected (this is frontend handler logic, and desktop calling already works).
