# LCS MeshChat - fix outbound mic frame size (Opus + Codec2 compatible)

## The bug your logs revealed
With OPUS: "Error while mixing frame: The effective frame duration (21.3 ms) was not
one of the acceptable values" - repeated endlessly, no audio to phone.
With CODEC2: no mixer errors, frames flow (received=fed_to_mixer, climbing), but still
no audio.

Root cause: the browser was sending 1024-sample frames = 21.3 ms at 48 kHz. Opus ONLY
accepts 2.5/5/10/20/40/60 ms frames, so it rejected every one. Codec2 tolerated the
odd size but the mismatch still produced no usable audio.

## The fix (works for BOTH Opus and Codec2)
The browser now sends exactly 960-sample frames = 20 ms at 48 kHz. 20 ms is valid for
Opus AND composes cleanly into Codec2/larger mixer targets. Because ScriptProcessorNode
buffers must be powers of two (can't be 960), we capture at 2048 and re-chunk the audio
stream into exact 960-sample frames before sending.

This makes the mic compatible with any LXST peer regardless of the codec they choose -
Sideband (Opus) or Columba (Codec2/Opus).

## Files
- src/frontend/js/TelephoneAudioBridge.js   (re-chunk mic into 960-sample / 20ms frames)

## Apply + redeploy
    Copy-Item -Path lcs-frames\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "Send 20ms (960-sample) mic frames for Opus+Codec2 compatibility"
    git config http.version HTTP/1.1
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Test
Call between MeshChat (Docker) and the phone, BOTH directions, with:
  - Sideband (Opus)
  - Columba (try Codec2 AND Opus modes)
The phone should now hear your MeshChat mic.

Watch the log during a call:
    docker compose logs --tail=40 -f
- The "21.3 ms not acceptable" errors should be GONE.
- "WebRTC bridge mic: received=N fed_to_mixer=N" should still climb (frames flowing).
- Now the phone side should actually get audio.

## Honest status
- This directly fixes the exact error in your Opus log (frame duration).
- For Codec2 (which showed frames flowing but no audio), the 20ms alignment should also
  resolve it - the odd 21.3ms size was likely producing garbage after mixing/encoding.
- If Codec2 STILL has no audio after this while Opus works, tell me - it would point to a
  Codec2-specific samplerate (Codec2 runs at 8 kHz internally; the mixer should resample,
  but if not, that's the next tweak). But 20ms frames are the right foundation for both.
