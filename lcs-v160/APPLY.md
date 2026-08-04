# LCS MeshChat v1.6.0 - LXST 0.4.8, codec-switch workarounds removed

## Why LXST 0.4.8
Investigating why in-call codec switching broke on DESKTOP between v1.0.0 and v1.1.0, I
diffed the libraries. v1.1.0 bumped LXST 0.4.8 -> 0.5.0, and 0.5.0 changed the CALL
SIGNALLING PROTOCOL:
  - added a duplex "call mode" feature (Full/Half Duplex)
  - added a new signal PREFERRED_MODE (240)
  - profile switches are now sent as a BUNDLED LIST [profile, mode] instead of one signal
The codec-switch code itself (switch_profile, __reconfigure_transmit_pipeline) is
BYTE-IDENTICAL between 0.4.8 and 0.5.0. So the switching logic never broke - the signalling
around it changed, which breaks switching against peers that don't speak the new format.
Going back to 0.4.8 restores the v1.0.0-era signalling that worked.

## Versions
    rns  == 1.4.2   (bumped as requested)
    lxmf == 1.1.1   (bumped as requested)
    lxst == 0.4.8   (rolled back to the v1.0.0-era signalling)
Verified: all three install together, and every LXST internal the Docker audio bridge
patches still exists in 0.4.8 (__open_pipelines, __reconfigure_transmit_pipeline,
__prepare_dialling_pipelines, Mixer, Pipeline, Signalling, BandPass/AGC/EchoSuppressor).
Profile IDs and frame times are IDENTICAL in 0.4.8 (Opus 60ms, Codec2 200/320/400ms), so
the bridge's frame-size logic is unaffected.

## Codec-switch workarounds REMOVED
- "swap codec in place / same_framing" branch (v1.5.7) - gone
- echo-suppressor reference re-wiring on switch (v1.5.7) - gone
- (the v1.5.8 speaker resample/flush was never pushed, so nothing to remove)
The Docker reconfigure override is now a MINIMAL, faithful mirror of LXST's own method -
the only difference is it rebuilds with the WebSocket mic source instead of a LineSource.
Nothing clever, no special-casing per codec.

Desktop was already free of codec-switch hacks: the switch endpoint just calls
telephone.switch_profile() directly. Confirmed by inspection.

## IMPORTANT - why one Docker override must stay
The __reconfigure_transmit_pipeline override CANNOT be deleted entirely. Without it, a
codec switch makes LXST build a LineSource (PulseAudio mic), which does not exist in
Docker - that's the libpulse.so crash that killed calls earlier. It is now the minimum
required substitution and nothing more.

## Everything else KEPT (verified present)
Tools: RNode Configuration Tool, Read the Holy Bible. Interfaces: LoRa modem presets,
LCS Gateway server, LCS preset interfaces. Docker: LCS_DOCKER detection, use_browser_audio
flag, audio-bridge endpoint. Genuine bug fixes retained: muteNode (mic stopping after one
frame), websocket race fix, browser echo cancellation.

## Files
- requirements.txt                      (rns 1.4.2 / lxmf 1.1.1 / lxst 0.4.8)
- package.json, package-lock.json       (v1.6.0)
- src/backend/webrtc_audio_bridge.py    (minimal reconfigure override)

## Apply + push
    Copy-Item -Path lcs-v160\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.6.0: LXST 0.4.8 (pre-duplex signalling), rns 1.4.2, lxmf 1.1.1; remove codec-switch workarounds"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d
Verify: docker compose exec reticulum-meshchat sh -c "pip show rns lxst lxmf | grep -E 'Name|Version'"
Should read rns 1.4.2, lxmf 1.1.1, lxst 0.4.8.

## Test both platforms
DESKTOP: make a call, switch codec mid-call (Medium <-> High <-> Codec2). This is the
regression we're chasing - it should behave like v1.0.0 again.
DOCKER: call in/out, audio both ways, then switch codec mid-call.

## Honest caveat re: Liberty Chat / other peers
LXST 0.4.8 speaks the OLD signalling. Peers running LXST 0.5.x (possibly Liberty Chat
1.3.8, newer Sideband) speak the new bundled profile+mode format. Codec switching works
best when BOTH ends use compatible LXST. If switching works desktop<->desktop on 1.6.0 but
misbehaves against a phone, that confirms the phone is on 0.5.x - tell me and we can decide
whether to match the phone instead. Basic calling/messaging is unaffected either way.
