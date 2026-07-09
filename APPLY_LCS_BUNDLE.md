# LCS MeshChat — customization bundle (v3)

Apply on top of your feature/lxst branch (after the upstream v2.4.0 merge).
Verified: the patch applies cleanly with both `git apply` and `git apply --3way`.

## Contents

### lcs-meshchat-source.patch  (10 text files)
- LICENSE          -> LCS ownership of additions/branding/marks + retained MIT
- package.json / package-lock.json -> version 2.4.0 -> 1.0.0
- meshchat.py      -> add-lcs-presets endpoint, docker-safe /app/restart, is_docker flag
- App.vue          -> branding, accent bar, Back + Add LCS Interfaces (all builds),
                      Restart (docker only), sidebar lcs.network link
- InterfacesPage / SettingsPage / ToolsPage / index.html / call.html
                   -> "MeshChat" -> "LCS MeshChat" rename

### lcs-assets/  (binary files — paths mirror the repo)
All logos/favicons/icons regenerated from your LCS logo at correct sizes:
- src/frontend/public/assets/images/  lcs-logo.png, logo.png,
                                      logo-chat-bubble.png, reticulum_logo_512.png
- src/frontend/public/favicons/       favicon-512x512.png
- src/frontend/public/rnode-flasher/  reticulum_logo_512.png, index.html (LCS flasher)
- logo/                               logo.png, logo-chat-bubble.png, icon.ico (Windows app icon)

## Apply (repo root, on feature/lxst)

    git apply --3way lcs-meshchat-source.patch

    # copy ALL binary assets in one shot (paths already match the repo layout)
    cp -r lcs-assets/. .          # Linux/Mac
    # Windows PowerShell:
    #   Copy-Item -Path lcs-assets\* -Destination . -Recurse -Force

    git add -A
    git commit -m "LCS branding, logos, v1.0.0, license, buttons, presets, restart, flasher"
    git push origin feature/lxst

On Windows PowerShell run commands one per line (no &&).

## Build & deploy

Trigger GitHub Actions -> build. Then on the Pi:
    cd /opt/reticulum-meshchat
    docker compose pull
    docker compose up -d

## Notes
- Version now shows 1.0.0 everywhere (About, API, built artifact filenames), since
  get_app_version() reads package.json.
- LICENSE: Liam Cottle's MIT notice is RETAINED (legally required for MIT derivatives).
  Your LCS additions/branding/marks are declared LCS property and NOT MIT-licensed.
  This is the correct, enforceable way to protect an MIT fork — you cannot remove the
  upstream MIT notice, but everything you added is protected.
- Restart button (docker only) exits the app process; docker restart:unless-stopped
  relaunches it. It does NOT run `docker compose restart` (that needs the docker
  socket = root control of the host from an unauthenticated UI = unsafe).
- Add LCS Interfaces button: all builds. Idempotent, non-destructive, needs a restart.

## Verify on first build (couldn't test in build env)
- Restart endpoint (needs live container), flasher Web Serial (needs hardware),
  live button->backend calls, logos rendering. All code compiles; frontend builds clean.
