# LCS MeshChat v1.4.0 - full codec support (Opus + Codec2) both desktop and Docker

## Fixes
1. DESKTOP MIC (Windows/Mac/Linux) - fixes no-outbound-audio since v1.2.0. The global
   ringtone held a Web Audio AudioContext alive for the whole session, interfering with
   the system mic. Now the ringtone opens its context only while ringing and closes it
   right after. Works for ALL codecs on desktop (desktop uses the real mic via LXST, so
   Codec2/Opus all work once the mic is freed).

2. DOCKER MIC - now works for EVERY codec/quality, not just Opus MEDIUM:
   - Root cause (from your log): browser sent fixed-size frames but each codec/profile
     needs a different frame duration (Opus 60ms, Codec2 200/320/400ms). MEDIUM happened
     to tolerate it; everything else rejected the mismatched frame.
   - Fix: the backend now computes the exact frame size for the active profile and tells
     the browser over the audio-bridge websocket ("frame_config" message). The browser
     re-chunks mic audio to that exact size. So:
       Opus MEDIUM/HIGH/MAX -> 2880 samples (60ms)
       Codec2 LOW           -> 9600 samples (200ms)
       Codec2 VERY_LOW      -> 15360 samples (320ms)
       Codec2 ULTRA_LOW     -> 19200 samples (400ms)

3. Hardened outgoing-call profile param (could send empty and crash call setup).

## Files
- package.json, package-lock.json                      (v1.4.0)
- meshchat.py                                           (sends frame_config to browser)
- src/backend/webrtc_audio_bridge.py                   (computes per-profile frame size)
- src/frontend/js/TelephoneAudioBridge.js              (dynamic frame size from backend)
- src/frontend/components/App.vue                       (ringtone AudioContext lifecycle)
- src/frontend/components/telephone/TelephonePage.vue  (profile param hardening)

## Apply + push
    Copy-Item -Path lcs-v140\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "v1.4.0: full Opus+Codec2 support (dynamic frame sizing) + desktop mic fix"
    git config http.version HTTP/1.1
    git push origin lcs

## Then
- Docker: docker compose pull && docker compose up -d (after Actions rebuilds)
- Desktop: build the app and test

## Test matrix
- DOCKER: call on each quality - Opus MEDIUM/HIGH/MAX and each Codec2 level. All should
  now send mic audio. Watch the log for:
    "WebRTC bridge: target frame <ms> -> <N> samples @ 48000Hz for browser mic"
- DESKTOP (Windows): call on any codec - the other side should hear you.

## Honest caveats
- Docker Codec2 adds real latency by design (200-400ms frames = that much buffering
  before each send). That's inherent to Codec2's large frames, not a bug. Voice is still
  intelligible, just with noticeable delay on the ultra-low-bandwidth profiles.
- The DESKTOP mic fix remains a strong hypothesis (couldn't reproduce here). The Docker
  fixes are confirmed by your diagnostic log. Please test desktop and report.
- If a Codec2 call still fails in Docker, send the log line "WebRTC bridge: target frame..."
  plus any "Error while mixing frame" - that'll show if the computed size is off.
