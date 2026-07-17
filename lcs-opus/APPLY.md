# LCS MeshChat - CRITICAL fix: Opus codec missing in Docker (calls fail instantly)

## The bug you hit
Incoming calls failed instantly with no ring / no answer button. The container log showed:
  "The Opus library wasn't found or couldn't be loaded"
  on_telephone_ended: ...

LXST needs the Opus audio codec to encode/decode call audio. The Docker image never
installed it, so every call died the moment it tried to set up audio - before it could
ring. This is why: no ring, no answer button, active_call was null (call already ended).

This is a MISSING SYSTEM LIBRARY, not a code bug. It affects ALL calls in Docker,
regardless of the browser audio bridge.

## The fix
Dockerfile now installs libopus0 + libopusfile0 + libopusenc0 + opus-tools before
the Python deps. pyogg (which LXST uses) finds libopus via find_library("opus"),
which resolves once libopus0 is present.

## Apply (repo root, on lcs)
    Copy-Item -Path lcs-opus\Dockerfile -Destination . -Force
    git add Dockerfile
    git commit -m "Install libopus in Docker image (fixes call audio: Opus library not found)"
    git config http.version HTTP/1.1
    git push origin lcs

## Then rebuild + redeploy (this REBUILDS the image, so let Actions finish first)
    cd /opt/reticulum-meshchat
    docker compose pull
    docker compose up -d

## Verify the fix landed
After redeploy, on the Pi:
    docker exec reticulum-meshchat python3 -c "from ctypes.util import find_library; print(find_library('opus'))"
    -> should print: libopus.so.0   (not None)

Then place a real call between two nodes. It should now ring, show the answer button,
and connect. Watch the log - the "Opus library wasn't found" error should be GONE.

## Note
This is a frontend-independent fix - it's purely the Docker image. Your other pending
frontend changes (announce feedback, hide Add-LCS in docker, ringtone priming) are
separate and already pushed if you applied the previous bundle.
