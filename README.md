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

### What's new in v1.9.4

- **Reverse proxy fix** — the same-origin check now tolerates a proxy that strips
  the port from the `Host` header, which is what nginx's `proxy_set_header Host
  $host` does. v1.9.3 refused those connections with a 403.
- **Docker and reverse proxy documentation** — see the Docker section above and
  `docs/REVERSE_PROXY_SETUP.md`.
- **Corrected code signing guidance** in `docs/code-signing.md`: EV certificates
  have not granted instant SmartScreen reputation since 2024.

### What's new in v1.9.3

- **Works behind a reverse proxy** — the console bridge now accepts same-origin
  WebSocket connections, so a proxied deployment such as
  `https://liberty.local:8443` works with no extra configuration.
  `X-Forwarded-Host` is honoured. Cross-origin requests are still rejected.
- **Frequency presets are back on Transport Config**, and usable over Reticulum,
  but selecting one while connected over the mesh asks for confirmation first and
  spells out that saving will take the node off the mesh permanently.
- **Preset labels now carry their parameters** in the app's RNode interface
  dropdown, matching the console: `Long Fast — SF11 / 250 kHz / CR 4:5 (★ LCS
  Recommended)`. Long Fast remains the default.
- **Short Slow renamed to "Average - Recommended for Speed"** in all three preset
  dropdowns: the app's interface dropdown, the console's Node Config tab, and the
  console's Transport Config tab.
- **Reticulum 1.5.4 and LXST 0.5.3.**

### Privacy

LCS MeshChat does not collect, transmit or sell personal information. There is no
telemetry, no analytics, no crash reporting and no account. Your identity keys,
messages and configuration stay in your own storage directory on your own machine.
Network traffic goes only to the Reticulum interfaces you configure yourself.
The application is open source and the code in this repository is what is built
into the released binaries.

**A note on the Windows download warning.** Microsoft Edge and SmartScreen may warn
that the installer is not commonly downloaded. This is a reputation check on the
signature of the file, not a finding about its content — it appears for any new
unsigned binary regardless of what it does. See `docs/code-signing.md` for the
status of signing.

### What's new in v1.9.2

- **Block an identity directly** — Settings → Blackhole takes an identity hash with
  an optional reason. No announce or prior contact is needed, since Reticulum blocks
  identities rather than destinations. The `<angle bracket>` form RNS prints is
  accepted, as is colon-delimited hex.
- **Block Contact no longer depends on a recent announce** — it resolves the peer's
  identity from RNS's persisted known-destinations table, then from MeshChat's own
  announce records, and finally by requesting a path so the announce is re-sent.
  It only fails if the destination has never been heard from at all, and says to
  paste the identity hash directly if so.
- **Release notes in the draft release** — the build workflow now generates the
  release body from this README's "What's new" section for the version being built,
  followed by the commits since the previous tag.
- **Clearer subscription wording** — the hash a subscriber adds as a source is the
  publisher's *transport instance* identity, which is a different key from your
  MeshChat identity.

### What's new in v1.9.1

**Blackhole management.** Conversations now have a **Block Contact** action in the
three-dot menu, and Settings gains a Blackhole section.

- **Block Contact** resolves the peer's destination hash to its identity hash and
  adds it to Reticulum's blackhole list — the same list `rnpath -B` writes.
  Announces from that identity are dropped and this node stops routing traffic to
  any of its destinations. It takes effect immediately.
- **Blocked list** in Settings shows everything blocked, whether you added it or a
  subscribed source did, with expiry and reason, and lets you unblock.
- **Publish** your list so other nodes can subscribe to it, served at
  `rnstransport.info.blackhole`.
- **Subscribe** to lists published by transport instances you trust, with a
  configurable update interval.

Blocking is identity-scoped and applies to your own network segments only. There is
no way to block anyone globally in Reticulum, and other nodes can still carry their
traffic. Publish and subscribe settings are read by Reticulum at startup, so those
need a restart; blocking and unblocking do not.

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

### Docker

```yaml
services:
  reticulum-meshchat:
    container_name: reticulum-meshchat
    image: ghcr.io/daylight-hub/reticulum-meshchat:latest
    restart: unless-stopped
    network_mode: bridge          # own namespace -> no host port conflicts
    environment:
      - LCS_DOCKER=1
    ports:
      - 8082:8000
    volumes:
      - /opt/reticulum-meshchat:/config
    command: >
      python meshchat.py --host=0.0.0.0 --port=8000
      --reticulum-config-dir=/config/.reticulum
      --storage-dir=/config/.meshchat --headless
```

```sh
docker compose up -d
```

The app is then on `http://<host>:8082`, and the Transport Node Console on
`http://<host>:8082/transport-console/index.html`.

**Voice calls need HTTPS.** The container has no audio hardware, so calls use the
browser's microphone and speaker over a WebSocket audio bridge — and browsers only
grant microphone access in a secure context. Put an HTTPS reverse proxy in front of
it. `docs/REVERSE_PROXY_SETUP.md` has working nginx configurations for OpenWrt and
Debian, certificate generation, firewall rules, and how to verify it.

`LCS_DOCKER=1` tells the app it is containerised so it uses the browser audio
bridge. Leave it set.

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
