# LCS MeshChat v1.5.4c - pin to v1.5.0 floor versions (isolate the version variable)

## Why only requirements.txt changes
Your current build (v1.5.4b: rns 1.4.2 / lxmf 1.1.1 / lxst 0.5.0) gives:
  - working: ringtone, button, OUTGOING calls
  - broken: INCOMING calls, audio bad/missing on most codecs

The audio bridge code is ALREADY identical to v1.5.0 (including the per-codec frame sizing -
that was never actually missing; I was wrong earlier). So the code isn't the difference.
The one remaining variable between "v1.5.0 fully worked" and now is the LIBRARY VERSIONS.

v1.5.0 was built with `>=` pins, pulling whatever was newest THEN. This build pins to the
conservative floor that v1.5.0 specified:
    rns==1.3.8   lxmf==1.0.1   lxst==0.5.0

## This is a clean experiment
ONLY requirements.txt changed (plus version metadata). Everything else is byte-identical to
your current build. So whatever changes in behavior is caused purely by the library versions.

## Files
- requirements.txt   (rns 1.3.8, lxmf 1.0.1, lxst 0.5.0)
- package.json, package-lock.json

## Apply + push
    Copy-Item -Path lcs-v154c\* -Destination . -Recurse -Force
    git config http.version HTTP/1.1
    git add requirements.txt package.json package-lock.json
    git commit -m "v1.5.4c: pin to rns1.3.8/lxmf1.0.1/lxst0.5.0 (v1.5.0 floor) to isolate version cause"
    git push origin lcs
    cd /opt/reticulum-meshchat && docker compose pull && docker compose up -d

## Verify the versions actually deployed
    docker compose exec reticulum-meshchat sh -c "pip show rns lxst lxmf | grep -E 'Name|Version'"
Must show rns 1.3.8, lxmf 1.0.1, lxst 0.5.0. If not, the image didn't rebuild.

## Then test and tell me (this is the experiment result)
1. Can you now call INTO meshchat (incoming)?
2. Is audio good on Opus (Medium/High/Max)?
3. Is audio good on Codec2?

RESULT INTERPRETATION:
- If incoming + audio now work -> the newer RNS/LXST were the cause. We stay on these pins
  and you have a fully working build. Done.
- If STILL broken with these old versions -> it's NOT the versions. Then it's the incoming
  path or the proxy, and I need the backend log during an INCOMING call (paste as TEXT,
  since file attachments keep arriving empty):
      docker compose logs --tail=50 -f
  ...specifically whether "__open_pipelines (override) called" and "pipelines opened" appear
  on an INCOMING call, and the "WebRTC bridge mic: received=" line.

## Note on the empty attachments
Every log file you attach arrives EMPTY on my end. Please paste log text directly into the
chat instead of attaching a file - that's the only way I can read it.
