<p align="center">
<img src="./logo/logo-chat-bubble.png" width="150">
</p>

<h2 align="center">LCS MeshChat</h2>

<p align="center">
A Liberty Communication Systems, Inc. distribution of Reticulum MeshChat.<br/>
built on MeshChat by Liam Cottle · <a href="https://lcs.network">lcs.network</a>
</p>

## About this fork

**LCS MeshChat** is Liberty Communication Systems' branded distribution of
Reticulum MeshChat, with additional features for LCS network deployments. It is
built on the open-source [Reticulum MeshChat](https://github.com/liamcottle/reticulum-meshchat)
by Liam Cottle (MIT licensed — see `LICENSE`).

### LCS additions

- **Branding** — LCS logo throughout, "LCS MeshChat" naming, brand accent styling.
- **Add LCS Interfaces** — a header button (all builds) opens a dialog to add LCS
  network interfaces to Reticulum. You choose which to add, whether to enable them
  immediately, and can auto-detect a connected RNode's serial port:
  - **LCS Gateway Client** — `public.lcs.network` (TCP, gateway mode)
  - **IP RNode** — `iprnode.local:4545` (TCP, network-attached RNode)
  - **RNode LoRa** — direct serial LoRa radio (914.875 MHz, SF11), added disabled
    unless a serial port is provided.
- **Restart button** (Docker builds only) — restarts the app process; relies on the
  container's `restart: unless-stopped` policy. Does not require the Docker socket.
- **Back button** — navigates to the previous page.
- **Incoming call ringtone** — a generated tone plays while a call is ringing.
- **Transport Node Console** — replaces the RNode Flasher tile in Tools; a
  self-contained console for configuring/monitoring RNode transport nodes.
- **Purchase link** — "Buy RNode Radios · lcs.network" in the sidebar and Tools.
- **Version** — reports as LCS MeshChat, and the About page shows the LXST version.

### What's new in v1.9.0

**Remote transport node management over Reticulum.** The Transport Node Console
in Tools can now reach RNode transport nodes anywhere on the mesh, not just ones
attached over USB, Bluetooth or the local network.

- **RNS console bridge** (`src/backend/rns_link_bridge.py`) — MeshChat's web
  server now answers the console's `rns.link.*` WebSocket protocol at `/rns/ws`
  and turns it into real Reticulum Link + Request traffic aimed at a node's
  `/provision` handler. It runs on the RNS instance and identity MeshChat
  already has: no extra daemon, no second identity store, no extra port.
- **Console auto-connect** — the Transport Node Console finds the bridge by
  itself. It probes the same origin first, so it works whether the console is
  opened from the Tools page, from disk, or from a hosted copy, and reports the
  actual cause when a browser blocks the connection rather than just failing.
- **Setup instructions** — selecting the LCS MeshChat transport now explains the
  one-time wired step: add your Identity Hash to the node's *Remote management
  allowed* list over USB-C serial before the node will answer you over the mesh.
- **Modem parameter warning** — Transport Config warns, when the node is reached
  over Reticulum, that changing frequency, bandwidth, SF or CR makes the node
  stop matching the mesh that carried the command, with no path left to undo it.
  Modem parameters need a USB-C serial connection.
- **Naming** — the console's transport is labelled "RNS (via LCS MeshChat)".
- **Deep links** — the console accepts `?dest=`, `?aspect=`, `?transport=`,
  `?ws=`, `?port=`, `?token=` and `?identify=0`, so a node can be linked to
  directly.
- **Origin allowlist** — WebSockets bypass CORS, so the bridge only accepts
  loopback origins and `file://` pages by default. `--rns-bridge-token` adds a
  shared secret, `--rns-bridge-allow-origin` permits a hosted console, and
  `--disable-rns-bridge` turns the whole thing off.

Over RNS the console exposes Node Status and Transport Config. Logs and Node
Config still need Serial, Bluetooth or a LAN WebSocket — they rely on legacy
KISS opcodes that don't survive the Reticulum hop. Nodes must be announcing on
`rnstransport.remote.management`, and your MeshChat identity hash has to be in
the node's `/provision` ALLOW_LIST.

See `docs/rns-console-bridge.md` for the protocol details and why
`attermann/ReticulumAPI` is not a drop-in substitute.

### Build & deploy

- **Docker** — GitHub Actions builds a multi-arch image on every push to the `lcs`
  branch, pushed to `ghcr.io/<owner>/reticulum-meshchat:latest` and `:lcs`.
- **Desktop apps** (Windows/Mac/Linux) — built on a version tag push, or via the
  Actions "Run workflow" button with the desktop-build option enabled. All desktop
  artifacts attach to a single release. Mac builds install `codec2` via Homebrew so
  the `pycodec2` dependency compiles.

### License

The LCS name, logos, branding, and additions are the property of Liberty
Communication Systems, Inc. The underlying Reticulum MeshChat remains MIT licensed;
that notice is retained in `LICENSE` as required.


## License

MIT
