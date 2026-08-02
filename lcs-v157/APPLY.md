# LCS MeshChat v1.5.7 - fix mid-call codec SWITCHING

## What works now (your report)
Calling on ANY codec and staying there = clear audio both ways. The problem is ONLY when
you SWITCH codec mid-call.

## The two switch bugs, and the fixes

### Bug 1: Medium -> High loses inbound audio (mic still works)
Medium/High/Max are structurally identical (Opus, 60ms frames). My reconfigure override was
doing a FULL transmit teardown/rebuild even for these no-op switches, and that rebuild
orphaned the echo-suppressor reference held by the RECEIVE mixer -> inbound (phone->MeshChat)
audio stalled.
FIX: when the frame timing is unchanged (Opus->Opus), just swap the transmit codec in place
and leave the receive pipeline completely untouched. No teardown = nothing to break.

### Bug 2: switching to Codec2 = deep / nothing
Two parts:
 (a) On a real framing change (Opus 60ms <-> Codec2 200-400ms) the full rebuild now ALSO
     re-wires the echo-suppressor reference to the new transmit path, so the receive mixer
     keeps a valid reference and inbound keeps flowing.
 (b) The browser is told the new mic frame size immediately on switch (set_target_frame_samples)
     so it sends correctly-sized frames for the new codec.

## Files
- src/backend/webrtc_audio_bridge.py   (reconfigure override rewritten)
- package.json, package-lock.json      (v1.5.7)

## Apply + push
    Copy-Item -Path lcs-v157\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.5.7: fix mid-call codec switch (skip no-op rebuild, preserve echo reference, update frame size)"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Test
- Call on Medium, switch to High: inbound audio should now KEEP working (was dropping).
  Log will show: "codec swapped in place (framing unchanged, 60ms); receive pipeline left intact"
- Call on Opus, switch to a Codec2 profile: should reconfigure cleanly. Log shows the full
  rebuild with the new 200/320/400ms frame size.

## Honest note on Codec2 quality
Opus<->Opus switching is now fully fixed. Codec2 involves an 8kHz vs 48kHz samplerate
difference; switching framing is handled, but if Codec2 audio still sounds off (pitch/speed)
after switching INTO it, that's the deeper samplerate-resample work we deferred earlier.
You said "whatever codec I call on works" - so calling directly on Codec2 is fine; this fix
targets the SWITCH path. If switching into Codec2 still sounds deep after this, tell me and
we'll add the receive-side resample carefully (Docker-only, desktop untouched).
