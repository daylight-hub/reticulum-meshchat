# LCS MeshChat — customization bundle

This bundle contains all the LCS customizations to apply on top of your
`feature/lxst` branch (after you've merged upstream v2.4.0 per the earlier
`UPDATE_LXST_FROM_UPSTREAM.md` steps).

## What's included

- **lcs-meshchat-source.patch** — code changes to 4 files:
  - `meshchat.py` — LCS preset-interface method + `/api/v1/reticulum/interfaces/add-lcs-presets`
    endpoint + desktop (`sys.frozen`) auto-add of the interfaces
  - `requirements.txt` — merged dependency versions (rns 1.3.7, lxmf 1.0.1,
    lxst 0.4.8, peewee<4.0.0, etc.)
  - `src/frontend/components/App.vue` — LCS branding/logo, Back / Restart /
    "Add LCS Interfaces" buttons (web-only), sidebar lcs.network link
  - `src/frontend/components/tools/ToolsPage.vue` — "LCS RNode Flasher" label +
    "Purchase RNode Mesh Radios" tile
- **lcs-assets/** — binary files (can't live in a text patch):
  - `images/lcs-logo.png` → copy to `src/frontend/public/assets/images/lcs-logo.png`
  - `rnode-flasher/index.html` → replace `src/frontend/public/rnode-flasher/index.html`

## Apply it

From the root of your repo, on your `feature/lxst` branch:

```sh
# 1. apply the code patch
git apply --check lcs-meshchat-source.patch   # dry-run; should print nothing
git apply lcs-meshchat-source.patch

# 2. drop in the binary assets
mkdir -p src/frontend/public/assets/images
cp /path/to/lcs-assets/images/lcs-logo.png            src/frontend/public/assets/images/lcs-logo.png
cp /path/to/lcs-assets/rnode-flasher/index.html       src/frontend/public/rnode-flasher/index.html

# 3. (optional) remove the now-unused old flasher libraries to slim the image
#    the new flasher is self-contained, so its old js/ folder is dead weight
# rm -rf src/frontend/public/rnode-flasher/js

# 4. commit + push
git add -A
git commit -m "LCS branding, header buttons, preset interfaces, flasher, lcs.network links"
git push origin feature/lxst
```

If `git apply` complains about context (e.g. if your merged tree differs
slightly), use a 3-way apply which is more forgiving:
```sh
git apply --3way lcs-meshchat-source.patch
```

## Build & deploy

Trigger your GitHub Actions build (Actions → Build and Release → Run workflow),
then on the Pi:
```sh
cd /opt/reticulum-meshchat
docker compose pull
docker compose up -d
```

## What you'll see

- Header: LCS logo + gradient "LCS MeshChat" wordmark; **Back**, **Add LCS
  Interfaces**, and **Restart** buttons (web/docker build only — hidden in the
  desktop .exe/.dmg/AppImage via the electron check)
- Sidebar: an always-visible **"Buy RNode Radios · lcs.network"** link
- Tools page: **LCS RNode Flasher** + **Purchase RNode Mesh Radios** (lcs.network)
- Interfaces: the **Add LCS Interfaces** button adds
  `TCPClient public.lcs.network:1776` (enabled) and an `RNode LoRa Interface`
  (disabled template with your LoRa params). Desktop builds add these
  automatically on first launch.

## Notes / caveats

- Interfaces require a **MeshChat restart** to take effect (inherent to RNS).
- `public.lcs.network:1776` must be a reachable RNS TCP server or clients will
  log connection retries — that's your infrastructure, not the code.
- The **Restart** button reloads the web app; it does NOT restart the Docker
  container (that would require exposing the Docker socket — a security risk).
- The flasher and buttons were verified to build cleanly, but the Web Serial
  flash flow and live button→backend calls couldn't be hardware-tested in the
  build environment — worth a quick click-test on your first build.
- License: MeshChat's MIT `LICENSE` is preserved; your flasher's BSD-3-Clause
  header + third-party attributions are intact. You're clear to distribute.
