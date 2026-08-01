# LCS MeshChat v1.5.6 - fix mic stopping after ONE frame (the real audio bug)

## Your log was the key
    WebRTC bridge mic: received=1 fed_to_mixer=1
...and then nothing. The browser connected, sent exactly ONE mic frame, then went silent.
Everything else in the log was perfect (pipelines open, call established, correct 2880-
sample frames). So the bug is: the browser stops capturing after the first buffer.

## Root cause
In the browser mic capture, the audio graph ends at a zero-gain "mute" node (so you don't
hear your own mic). That node was created as a LOCAL const. After start() returned, it went
out of scope and got garbage-collected - which disconnected the ScriptProcessor from the
audio destination. A ScriptProcessorNode only keeps firing onaudioprocess while it's
connected to a running destination, so it fired exactly once and stopped. That's the
received=1-then-silence you saw.

## The fix
Keep the mute node referenced on the object (this.muteNode) so it can't be garbage-
collected, and clean it up properly on stop(). One-line-class of bug, big effect.

## Files
- src/frontend/js/TelephoneAudioBridge.js   (keep muteNode referenced)
- package.json, package-lock.json           (v1.5.6)

## Apply + push
    Copy-Item -Path lcs-v156\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.5.6: keep mic mute node referenced so capture doesn't stop after one frame"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d
Then HARD-REFRESH the browser (Ctrl+Shift+R) or use a fresh InPrivate window.

## How to confirm it worked
On the Pi during a call:
    docker compose logs --tail=20 -f | grep "bridge mic"
Before: "received=1" then nothing.
After:  "received=N fed_to_mixer=N" with N CLIMBING (received=50, 150, 300...) = mic audio
flowing continuously. That means you should now be heard on the other end.

## What this fixes
- OUTBOUND audio (your mic -> other party): fixed by this (mic now sends continuously).
- INBOUND audio (other party -> your speaker): the speaker path was already working in the
  log (speaker sink injected, frames delivered). If you now hear them AND they hear you,
  we're done. If inbound is still silent, tell me - but the mic was the clear break here.

## Note
Backend confirmed fully working in your log - no backend change needed. This is purely the
browser mic-capture lifetime bug.
