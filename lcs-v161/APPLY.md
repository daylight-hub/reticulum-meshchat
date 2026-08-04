# LCS MeshChat v1.6.1 - exact v1.0.0 call stack (rns 1.3.7 / lxmf 1.0.1 / lxst 0.4.8)

## Answering your three questions directly

1) "Did you restore everything surrounding calls to v1.0.0?"
   Now yes - and importantly, most of it ALREADY was. I diffed the whole call path against
   v1.0.0 (3b4abd5):
     - backend switch endpoint (/api/v1/telephone/switch-audio-profile): BYTE-IDENTICAL
     - init_telephone: identical except the Docker-gated bridge install
     - profile dropdown + switchAudioProfile handler: identical
   The only leftovers were two cosmetic hardenings of mine, now reverted to v1.0.0 exactly.

2) "Could the docker-gated audio stuff be causing this?"
   NO - not on desktop. The bridge install is behind `if self.is_docker():`. On desktop it
   is never imported and never touches the telephone object. It cannot affect desktop
   codec switching. (It stays in place for Docker, unchanged.)

3) "Could it be the version bump on rns or lxmf?"
   THIS IS THE REMAINING SUSPECT, and you were right to ask. v1.0.0 ran:
        rns 1.3.7   lxmf 1.0.1   lxst 0.4.8
   v1.6.0 ran:
        rns 1.4.2   lxmf 1.1.1   lxst 0.4.8
   LXST already matched. So RNS + LXMF were the ONLY remaining difference from your
   known-good build. RNS carries the link/packet layer that codec-switch signalling rides
   on, so an RNS 1.3.7 -> 1.4.2 change is a very plausible cause.

## What this build does
Pins the EXACT v1.0.0 library stack:
    rns == 1.3.7
    lxmf == 1.0.1
    lxst == 0.4.8
Plus reverts the last two call-path hardenings so the call code is v1.0.0-identical.
This makes the libraries the only thing that changed - a clean test.

## KEPT (as requested)
- Ringtone (incoming call) - kept
- Docker browser audio bridge - kept, unchanged, still browser-compatible
- Header button differences (isDocker-gated: Add LCS Interfaces / restart variants) - kept
- All other LCS customizations: Tools (RNode tool, Bible), LoRa presets, LCS Gateway,
  LCS preset interfaces, propagation-node settings, branding

## Files
- requirements.txt                                       (exact v1.0.0 stack)
- package.json, package-lock.json                        (v1.6.1)
- src/frontend/components/telephone/TelephonePage.vue    (v1.0.0-identical profile param)

## Apply + push
    Copy-Item -Path lcs-v161\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.6.1: pin exact v1.0.0 call stack (rns 1.3.7 / lxmf 1.0.1 / lxst 0.4.8)"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

Verify the versions actually deployed:
    docker compose exec reticulum-meshchat sh -c "pip show rns lxst lxmf | grep -E 'Name|Version'"
Must read rns 1.3.7, lxmf 1.0.1, lxst 0.4.8.

## The test (this is a clean experiment)
DESKTOP: call, then switch Medium -> High, and Medium -> Low mid-call.
  - If switching now behaves like v1.0.0: the RNS/LXMF bump was the cause. Confirmed.
  - If it STILL goes deep / stops: the libraries are NOT the cause, and the difference is
    somewhere I haven't found yet - at that point I'd want to build a true v1.0.0 desktop
    binary and compare side by side, rather than keep guessing.

## Honest note
I can't reproduce desktop audio here (no audio hardware in my environment), so this is
reasoning from diffs, not from hearing it. The diffs now say: call code = v1.0.0, libraries
= v1.0.0. If the symptom survives that, my next suggestion is to test an actual v1.0.0
build to confirm v1.0.0 itself still behaves the way you remember - it's possible the peer
device (phone / Liberty Chat) changed underneath us, since codec switching is negotiated
between BOTH ends.
