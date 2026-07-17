# LCS MeshChat - audio format fix + announce confirm on home page

## What the log told us
The call now CONNECTS ("pipelines opened, call established") - big milestone.
Two problems remained:
1. Crash on teardown: 'WebSocketAudioSink' object has no attribute 'stop'
   -> LXST calls .stop()/.enable_low_latency() on the sink; we hadn't defined them.
2. "Terrible sound" one way, silence the other = AUDIO FORMAT MISMATCH.
   LXST's audio frames are numpy float arrays in [-1,1], NOT raw bytes. We were
   shoving raw buffers around. Now we convert properly:
     - speaker: LXST numpy float frame -> int16 PCM bytes -> browser
     - mic:     browser int16 PCM bytes -> numpy float (samples,1) -> LXST Mixer

## Files
- src/backend/webrtc_audio_bridge.py   (stop/start/enable_low_latency + numpy format conversion)
- src/frontend/components/App.vue        (green "Announced!" confirm on home page too)

## Apply + redeploy
    Copy-Item -Path lcs-audio3\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "Fix Docker call audio: sink stop() + int16<->float numpy frame conversion; announce confirm on home page"
    git config http.version HTTP/1.1
    git push origin lcs
    # after Actions rebuilds:
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## After redeploy - test a call both directions
- The teardown crash ('no attribute stop') should be GONE.
- Audio should be much closer to correct. If it's still off, the remaining variable is
  SAMPLERATE: the browser captures at 48000 Hz; if LXST's internal pipeline runs at a
  different rate, audio will sound too fast/slow or chipmunk/deep. If so, tell me:
    * does it sound too fast (high-pitched) or too slow (deep)?
    * that tells me the exact rate ratio to fix.
- Also watch the log for any new "feed error" / "handle_frame error" lines and paste them.

## Honest status
This fixes the definite bugs (crash + raw-vs-numpy format). Samplerate matching is the
last likely variable. We're close - the pipeline connects and frames flow; it's now about
the numbers matching. Report exactly what you hear (fast/slow/garbled/silent + which
direction) and I'll dial it in.

## Also done
- Announce confirmation: the green "Announced!" now shows on BOTH the telephone page
  and the home page "Announce Now" button, all builds.
