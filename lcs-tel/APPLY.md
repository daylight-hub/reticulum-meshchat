# LCS MeshChat - telephone + announce fixes

Verified: python compiles, frontend builds. Apply on lcs branch.

## Files
- meshchat.py                                          (items 1b, 5)
- src/frontend/components/telephone/TelephonePage.vue  (items 1a, 2)
- src/frontend/components/App.vue                       (items 3, 4)

## Apply (repo root, on lcs)
    Copy-Item -Path lcs-tel\* -Destination . -Recurse -Force
    npm run build-frontend      # want: ✓ built
    git add -A
    git commit -m "Telephone fixes: null guard, audio-devices 500, announce feedback, hide Add-LCS in Docker, ringtone priming, hourly announce"
    git config http.version HTTP/1.1
    git push origin lcs

## Then on the Pi (after Actions rebuilds)
    cd /opt/reticulum-meshchat
    docker compose pull
    docker compose up -d

## What each item does
1a. Fixed the crash "Cannot read properties of null (reading 'audio_profile_id')" that
    was aborting every telephone status poll (null-guarded active_call). THIS is what was
    stopping the call UI and audio bridge from working.
1b. /api/v1/telephone/audio-devices now returns empty lists in Docker instead of a 500
    (server has no audio hardware; the browser provides audio).
2.  Announce button now shows "Announced!" (green) for 2s so you get confirmation it worked.
    It was working before - just gave zero feedback, so it felt dead.
3.  "Add LCS Interfaces" button is now hidden in Docker builds, shown on all others.
4.  Ringtone audio priming strengthened for phones (touch/pointer events, keeps priming).
5.  Auto-announce now defaults to ENABLED, every hour (3600s), for all builds.

## IMPORTANT caveats
- Item 5 (hourly announce) changes the DEFAULT. Existing installs that already saved
  auto_announce as OFF keep their saved value - the new default only applies to fresh
  configs. On your existing Pi, toggle auto-announce on once in Settings if it doesn't
  self-enable (or clear that config value).
- Item 4 (ringtone): browsers fundamentally block audio until the user has interacted
  with the page at least once. The priming makes this as reliable as possible, but if a
  call arrives before ANY tap/click on the page since load, the first ring may still be
  silent. This is a browser rule, not something code can fully override. Once you've
  tapped anywhere, it works.
- Items 1a/1b are the real fix for the errors you pasted - those errors were from the
  OLD deployed image; they're fixed here but need this redeploy to take effect.
