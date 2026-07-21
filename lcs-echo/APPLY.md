# LCS MeshChat - fix echo (both sides hear themselves) + the prime-crash fix

This bundle includes BOTH fixes since you haven't deployed the prime fix yet:

## 1. Echo fix (the new one)
Symptom: everyone hears themselves repeated.
Cause: received call audio was played straight to audioContext.destination, which the
browser's echo canceller CANNOT see. So the far end's voice came out your speaker, leaked
into your mic, and got sent back - they hear themselves.
Fix: play received audio through a MediaStreamDestination -> <audio> element, which the
browser AEC monitors and uses as its echo reference. The speaker audio is now cancelled
from your outgoing mic signal.

## 2. Prime-crash fix (from before, not yet deployed)
"ReferenceError: prime is not defined" in mounted() left the "Add LCS Interfaces" button
showing and restart broken. Removed the two dead listener lines.

## Files
- src/frontend/js/TelephoneAudioBridge.js   (echo: AEC-visible playback)
- src/frontend/components/App.vue            (prime crash fix)

## Apply + push
    Copy-Item -Path lcs-echo\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "Fix call echo (route playback through browser AEC) + remove dead prime listeners"
    git config http.version HTTP/1.1
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Test at https://liberty.local:8443
- Echo should be gone or greatly reduced.
- "Add LCS Interfaces" button gone, restart works.
- Calls still connect with audio both ways.

## Honest notes on echo
- This is the right fix for browser-side echo (playback now visible to the AEC), best on
  Chromium browsers (Edge/Chrome), which you use.
- If a FAINT echo remains, the second layer is LXST's server-side EchoSuppressor; we can
  tune that too. The browser AEC is the primary defense and this enables it.
- If echo persists strongly, tell me the setup: both sides MeshChat-Docker, or one is
  Sideband on a phone? The phone's own AEC matters and where echo originates changes the fix.
