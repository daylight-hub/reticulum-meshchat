# LCS MeshChat v1.7.0 - half duplex / PTT, in-call codec selector removed

Base: reverted to v1.5.0, then the changes below.
Versions: rns==1.4.2, lxmf==1.1.1, lxst==0.5.1

## 1) Half Duplex + Push-To-Talk (like Sideband)
LXST 0.5.1 is what makes this possible - it added call modes, which older LXST lacked.
- A "Call Mode" selector appears during a connected call: Full Duplex / Half Duplex.
- Choosing Half Duplex reveals a large "Hold to Talk" PTT button. Hold it to transmit,
  release to listen. It turns red and says "Transmitting - release to listen" while held.
- Works with mouse AND touch (mousedown/up/leave + touchstart/end/cancel), so it behaves
  properly on phones and tablets.
- The mode is also selectable BEFORE dialling, and is applied once the call connects.
- LXST signals the mode to the other party, so both ends stay in sync. If the far end
  changes mode, our selector follows it.

Mechanically: Half Duplex squelches the packetizer (not transmitting). PTT unsquelches
while held and re-squelches on release, and mirrors that on the transmit mute.

## 2) Can we hide the codec selector only for Columba/Liberty Chat? - NO
I checked LXST for any peer identification. There is none:
  - APP_NAME is just the shared Reticulum destination namespace ("lxst") that EVERY LXST
    app uses - Columba, Sideband, MeshChat all look identical.
  - identify() only exchanges the Reticulum IDENTITY (a key hash), not an app name/version.
There is no field anywhere in the call or signalling that says which app the peer is running.
So per your instruction, the in-call codec selector is REMOVED ENTIRELY.

## 3) Codec / duplex selectors updated for LXST 0.5.1
- Codec (quality) is now chosen BEFORE the call only, with a note explaining it can't be
  changed once connected. This avoids the mid-call switch bug entirely (the receive
  pipeline keeps the samplerate it latched at call start, which is what made lower
  codecs play back deep and slow - that's an LXST-level issue, not app-level).
- Call mode (duplex) IS switchable mid-call, because LXST 0.5.1 supports it properly and
  it doesn't touch the audio samplerate.

## New API endpoints
- GET /api/v1/telephone/switch-call-mode/{call_mode}   (1=Full Duplex, 2=Half Duplex)
- GET /api/v1/telephone/push-to-talk/{true|false}
- /api/v1/telephone/audio-profiles now also returns call_modes + default_call_mode
- telephone status now includes active_call.call_mode

## Files
- requirements.txt                                     (rns 1.4.2 / lxmf 1.1.1 / lxst 0.5.1)
- package.json, package-lock.json                      (v1.7.0)
- meshchat.py                                          (call-mode + PTT endpoints, status)
- src/frontend/components/telephone/TelephonePage.vue  (PTT UI, mode selector, codec removed)
- src/backend/webrtc_audio_bridge.py                   (v1.5.0 version, verified vs LXST 0.5.1)

## Apply + push
    Copy-Item -Path lcs-v170\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add -A
    git commit -m "v1.7.0: half duplex PTT, remove in-call codec selector, lxst 0.5.1"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Kept from v1.5.0
Tools (RNode Configuration Tool, Read the Holy Bible), LoRa modem presets, LCS Gateway
server entry, LCS preset interfaces, Docker browser audio bridge + LCS_DOCKER detection,
isDocker-gated header buttons, ringtone, branding.

## Test
- Desktop AND Docker: start a call, switch Call Mode to Half Duplex, hold the PTT button,
  confirm the far end hears you only while held.
- Confirm the codec selector no longer appears during a call (only before dialling).
- Verify versions: docker compose exec reticulum-meshchat sh -c "pip show rns lxst lxmf | grep -E 'Name|Version'"

## Honest note
I verified the PTT wiring against the LXST 0.5.1 API (switch_mode, packetizer squelch/
unsquelch, mute_transmit all confirmed present and behaving as used here), and the whole
app builds clean - but I have no audio hardware here, so the actual "held = heard" behaviour
needs your ears. If the far end hears nothing at all in half duplex, tell me and the likely
tweak is whether Liberty Chat expects the squelch on its own side too.
