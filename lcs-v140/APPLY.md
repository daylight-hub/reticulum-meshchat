# LCS MeshChat v1.4.0 - fix Docker no-audio (LineSource crash on profile switch + Docker detection)

## Your log revealed the REAL bug (finally the root cause)
Two problems, both now fixed:

### 1. LineSource crash on profile switch (the audio killer)
Your log showed LXST calling __reconfigure_transmit_pipeline -> LineSource -> libpulse.so
crash. This happens when the remote end negotiates a codec/profile mid-call. My earlier
override only replaced the INITIAL mic setup (__open_pipelines); I missed this SECOND place
(__reconfigure_transmit_pipeline) that also builds a PulseAudio LineSource. In Docker there's
no PulseAudio, so it crashed and killed audio in BOTH directions.
FIX: override __reconfigure_transmit_pipeline too, rebuilding with our WebSocket mic source
instead of LineSource (and updating the browser frame size for the new profile).

### 2. Docker not detected (why you saw desktop buttons)
You saw "Add LCS Interfaces" and the desktop restart button in Docker - because is_docker()
only checked /.dockerenv, which your container doesn't have. So the app thought it wasn't in
Docker: it hid the browser audio bridge AND showed desktop-only UI.
FIX: is_docker() now checks /.dockerenv, cgroup info, AND an env override.

## IMPORTANT - add this to your docker-compose to guarantee detection
In your docker-compose.yml, under the reticulum-meshchat service, add:

    environment:
      - LCS_DOCKER=1

This is the most reliable signal. The cgroup auto-detection should also work, but the env
var guarantees it. Example:

    services:
      reticulum-meshchat:
        image: ghcr.io/daylight-hub/reticulum-meshchat:latest
        environment:
          - LCS_DOCKER=1
        # ...rest of your config...

## Files
- meshchat.py                            (robust is_docker + app_info)
- src/backend/webrtc_audio_bridge.py     (override __reconfigure_transmit_pipeline)
- src/frontend/* , package.json          (prior v1.4.0 work retained)

## Apply + push
    Copy-Item -Path lcs-v140\* -Destination . -Recurse -Force
    npm run build-frontend
    git add -A
    git commit -m "v1.4.0: fix Docker audio - override reconfigure_transmit_pipeline (LineSource crash) + robust docker detection"
    git config http.version HTTP/1.1
    git push origin lcs

## Then on the Pi
1. Add the LCS_DOCKER=1 environment line to docker-compose.yml (see above)
2. docker compose pull
3. docker compose up -d

## Test
- The "Add LCS Interfaces" button and desktop restart should be GONE in Docker (confirms
  detection works).
- Calls should now pass audio both directions on all codecs, including after a profile
  switch. Watch the log:
    "WebRTC bridge: __reconfigure_transmit_pipeline (override) called"
    "WebRTC bridge: transmit pipeline reconfigured with WebSocket mic"
  ...instead of the libpulse.so crash.

## Why this is the real fix
The libpulse.so traceback is unambiguous: LXST was building a PulseAudio mic source in a
container with no PulseAudio. That crash, on every profile-switch signal, tore down the
audio. Overriding that method (as we already did for the initial setup) is the correct fix.
