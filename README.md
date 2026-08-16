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
