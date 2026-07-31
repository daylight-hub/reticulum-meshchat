# LCS MeshChat v1.5.3 - fix audio bridge crash (race condition)

## Your console error (the real cause)
    failed to start audio bridge: TypeError: Cannot read properties of null
    (reading 'createMediaStreamSource')  at Proxy.start

## Root cause - a race condition
In the audio bridge's start():
1. getUserMedia succeeds, mic acquired
2. it wires ws.onclose/onerror = stop()  BEFORE the mic is fully set up
3. it then AWAITS the websocket opening
4. if the websocket closes/errors during that await (e.g. proxy hiccup, the 502s you've
   seen), stop() fires and NULLS micStream + audioContext
5. execution resumes and calls audioContext.createMediaStreamSource(micStream) on null
   -> TypeError, bridge fails to start -> no audio

## The fix
- Don't wire onclose/onerror -> stop() until AFTER the mic is fully wired.
- During the "wait for websocket open" step, treat close/error as a clean rejection.
- After the await, bail out cleanly if stop() already ran (state is null).
This removes the crash and makes an early websocket close fail gracefully instead of
throwing.

## Files
- package.json, package-lock.json        (v1.5.3)
- src/frontend/js/TelephoneAudioBridge.js (race fix)
- src/frontend/components/App.vue         (carries the v1.5.2 handler hardening)

## Apply + push
    Copy-Item -Path lcs-v153\* -Destination . -Recurse -Force
    npm run build-frontend
    git config http.version HTTP/1.1
    git add package.json package-lock.json src/frontend/components/App.vue src/frontend/js/TelephoneAudioBridge.js
    git commit -m "v1.5.3: fix audio bridge start race (null micStream) + handler hardening"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d
Then hard-refresh the browser.

## What this fixes vs. what to verify
FIXED (definite): the createMediaStreamSource null crash. The audio bridge will no longer
throw on startup. Combined with the v1.5.2 handler hardening, the crash can't cascade to
block other events (ringtone, answer button).

STILL VERIFY after deploy - report each:
1. AUDIO: does calling now pass audio both ways? If the bridge still fails, the browser
   console will now show a clean "audio-bridge websocket failed to open" instead of a
   crash - tell me if you see that (it would mean the bridge WEBSOCKET itself isn't
   connecting through the proxy, a separate proxy-config fix).
2. ANSWER BUTTON: does the green answer / red end button now appear on the home page when
   a call comes in?
3. RINGTONE: this is a SEPARATE issue - see below.

## The ringtone (separate, browser-policy issue)
The ringtone may still be silent, and it's NOT a bug in the usual sense: browsers block
AudioContext audio that starts WITHOUT a recent user gesture (autoplay policy). The
ringtone creates its context when the call arrives - with no click at that moment - so the
browser suspends it. Fixing this properly needs a different approach (e.g. an <audio>
element with a pre-loaded sound file, or priming on any earlier click). If the ringtone
matters to you, tell me and I'll do a focused fix - but I didn't want to bundle a
speculative ringtone change with this crash fix. The browser notification should still pop.

## Honest note
The crash fix is solid and directly matches your console error. The ringtone and (possibly)
the answer button are downstream of it or separate; deploy this, then tell me exactly which
of the 3 still misbehave and I'll target them precisely with the console output.
