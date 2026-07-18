# LCS MeshChat - fix home-page answer audio + outbound (mic -> phone) audio

## Your report decoded
- "Answer from home page = no audio, but telephone page open = audio works"
  -> the browser audio bridge only ran on the telephone page. MOVED it to App.vue so
     it runs app-wide, triggered by the call-established event regardless of page.
- "No audio going OUT to the phone" (they can't hear you)
  -> found the bug: the Mixer calls source.codec.decode(frame) on mic frames. We were
     feeding decoded numpy arrays but with a Raw() codec that expected bytes -> decode
     produced garbage/silence outbound. Added a PassthroughCodec whose decode() returns
     our numpy frames unchanged. Inbound already worked (that's why you heard them).
- Added mic-frame diagnostics (logs received/fed counts every 3s during a call).

## Files
- src/backend/webrtc_audio_bridge.py                   (PassthroughCodec + global-friendly + mic logging)
- src/frontend/components/App.vue                       (global audio bridge on call established/ended)
- src/frontend/components/telephone/TelephonePage.vue  (removed page-local bridge, now global)

## Apply + redeploy
    Copy-Item -Path lcs-audio4\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "Global browser audio bridge + PassthroughCodec fixes outbound audio + home-page answer"
    git config http.version HTTP/1.1
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Test both things
1. Answer a call FROM THE HOME PAGE (not the telephone page) - you should now hear audio.
2. Talk - the phone side should now hear YOU.

## Check the mic diagnostics during a call
    docker compose logs --tail=40 -f
Look for:  "WebRTC bridge mic: received=N fed_to_mixer=M ..."
  - received climbing + fed climbing = your mic is reaching the mixer (good).
  - received=0 = the browser isn't sending mic frames (mic permission? bridge not started?)
  - received>0 but fed=0 = the mixer is rejecting frames (tell me, I'll adjust).

## Honest status
- Home-page answer: fixed (bridge is global now).
- Outbound audio: the PassthroughCodec bug was real and this should fix it. If the phone
  still can't hear you, paste the "WebRTC bridge mic:" log lines - they'll show whether
  frames reach the mixer, which pinpoints what's left.
- Samplerate remains the one variable I can't fully verify without hardware; inbound
  "sounds pretty good" suggests 48k matches, so outbound should too.
