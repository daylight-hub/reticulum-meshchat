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

### Features

**Branding and navigation**

- LCS logo throughout, "LCS MeshChat" naming, brand accent styling.
- **Add LCS Interfaces** — a header button opens a dialog to add LCS network
  interfaces to Reticulum. Choose which to add, whether to enable them
  immediately, and auto-detect a connected RNode's serial port:
  - **LCS Gateway Client** — `public.lcs.network` (TCP, gateway mode)
  - **IP RNode** — `iprnode.local:4545` (TCP, network-attached RNode)
  - **RNode LoRa** — direct serial LoRa radio (914.875 MHz, SF11), added disabled
    unless a serial port is provided.
- **Restart button** (Docker builds only) — restarts the app process, relying on
  the container's `restart: unless-stopped` policy. Does not need the Docker socket.
- **Back button**, **incoming call ringtone**, and a **Buy RNode Radios** link in
  the sidebar and Tools.
- Reports as LCS MeshChat, and the About page shows the LXST version.

**Transport Node Console** (Tools → Transport Console)

- Self-contained console for configuring and monitoring RNode transport nodes over
  Serial, Bluetooth, a LAN WebSocket, or Reticulum.
- **Remote management over Reticulum** — MeshChat answers the console's
  `rns.link.*` protocol at `/rns/ws` and turns it into Reticulum Link and Request
  traffic aimed at a node's `/provision` handler. It runs on the RNS instance and
  identity MeshChat already has: no sidecar daemon, no second identity store, no
  extra port.
- **Auto-connect** — the console finds the bridge itself, probing same-origin
  first, so it works from Tools, from disk, or from a hosted copy. When a browser
  blocks the connection it names the actual cause.
- **Setup guidance** — selecting the LCS MeshChat transport explains the one-time
  wired step of adding your Identity Hash to the node's remote-management allow
  list.
- **Frequency presets** on both Node Config and Transport Config, with the same
  labels as the app's RNode interface dropdown. Selecting one on a node reached
  over the mesh asks for confirmation first and warns that saving will take the
  node off the mesh permanently.
- **Deep links** — `?dest=`, `?aspect=`, `?transport=`, `?ws=`, `?port=`,
  `?token=`, `?identify=0`.
- Over Reticulum the console exposes Node Status and Transport Config. Logs and
  Node Config need Serial, Bluetooth or a LAN WebSocket, because they rely on
  legacy KISS frames that do not cross the Reticulum hop.

**Blackhole management**

- **Block Contact** in a conversation's three-dot menu, backed by the same
  Reticulum calls `rnpath -B/-U/-b` drives. Blocks are permanent until removed.
- Identity resolution without needing a recent announce: RNS's persisted
  known-destinations table, then MeshChat's own announce records, then a path
  request.
- **Block an identity directly** by pasting its hash in Settings. The
  `<angle bracket>` form RNS prints is accepted, as is colon-delimited hex.
- **Publish** your blocked list for others to subscribe to, served at
  `rnstransport.info.blackhole`, and **subscribe** to lists from transport
  instances you trust, with a configurable update interval.
- Blocking is identity-scoped and applies to your own network segments only.
  Publish and subscribe settings are read by Reticulum at startup and need a
  restart; blocking and unblocking do not.

**Deployment**

- Runs behind an HTTPS reverse proxy with no extra configuration — the bridge
  accepts same-origin WebSocket connections and tolerates a proxy that strips the
  port from the `Host` header.
- Origin allowlist on the bridge, since WebSockets bypass CORS, plus an optional
  `--rns-bridge-token` shared secret.
- Draft releases get a generated body: the matching section of
  `docs/CHANGELOG.md`, followed by the commits since the previous tag.

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
it. Working nginx configurations for OpenWrt 24.10 and Debian follow below.

`LCS_DOCKER=1` tells the app it is containerised so it uses the browser audio
bridge. Leave it set.

#### HTTPS reverse proxy

When LCS MeshChat runs in Docker, voice calls use **your browser's** microphone and speaker
over a WebSocket audio bridge — the container has no audio hardware of its own. Browsers
only grant microphone access in a **secure context**, so the app must be reached over
**HTTPS** (or `localhost`). This guide sets up an nginx reverse proxy to provide that.

**Prerequisites**

- LCS MeshChat running in Docker with the container port published to the host
- `LCS_DOCKER=1` set in the container environment

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

nginx listens on **8443 (HTTPS)** and proxies to **127.0.0.1:8082**, which Docker maps to
the container's port 8000.

---

#### OpenWrt 24.10

**1. Install nginx with SSL support**

```sh
opkg update
opkg install nginx-ssl
```

**2. Generate a self-signed certificate**

Use the hostname you will actually type in the browser — see the note on hostnames below.

```sh
mkdir -p /etc/nginx/ssl
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/meshchat.key \
  -out /etc/nginx/ssl/meshchat.crt \
  -subj "/CN=liberty.local" \
  -addext "subjectAltName=DNS:liberty.local,IP:192.168.2.1"
```

**3. Create `/etc/nginx/conf.d/meshchat.conf`**

```nginx
server {
    listen 8443 ssl;
    server_name liberty.local;

    ssl_certificate     /etc/nginx/ssl/meshchat.crt;
    ssl_certificate_key /etc/nginx/ssl/meshchat.key;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

**4. Test and restart**

OpenWrt's nginx is UCI-managed and runs with an explicit config path:

```sh
nginx -t -c /etc/nginx/uci.conf
/etc/init.d/nginx restart
/etc/init.d/nginx enable
```

**5. Allow port 8443 from the LAN**

```sh
uci add firewall rule
uci set firewall.@rule[-1].name='Allow-MeshChat-HTTPS'
uci set firewall.@rule[-1].src='lan'
uci set firewall.@rule[-1].proto='tcp'
uci set firewall.@rule[-1].dest_port='8443'
uci set firewall.@rule[-1].target='ACCEPT'
uci commit firewall
/etc/init.d/firewall restart
```

**6. Open the app**

```
https://liberty.local:8443
```

---

#### Debian

**1. Install nginx**

```sh
sudo apt update
sudo apt install nginx openssl
```

**2. Create a certificate**

For a LAN host, self-signed (substitute your own hostname and IP):

```sh
sudo mkdir -p /etc/nginx/ssl
sudo openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/nginx/ssl/meshchat.key \
  -out /etc/nginx/ssl/meshchat.crt \
  -subj "/CN=meshchat.local" \
  -addext "subjectAltName=DNS:meshchat.local,IP:192.168.1.50"
sudo chmod 600 /etc/nginx/ssl/meshchat.key
```

If the machine has a public domain name, use Let's Encrypt instead and avoid browser
certificate warnings entirely:

```sh
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d meshchat.example.com
```

**3. Create `/etc/nginx/sites-available/meshchat`**

```nginx
server {
    listen 8443 ssl;
    listen [::]:8443 ssl;
    server_name meshchat.local;

    ssl_certificate     /etc/nginx/ssl/meshchat.crt;
    ssl_certificate_key /etc/nginx/ssl/meshchat.key;
    ssl_protocols       TLSv1.2 TLSv1.3;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

**4. Enable the site and reload**

```sh
sudo ln -s /etc/nginx/sites-available/meshchat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable nginx
```

**5. Allow port 8443** (if `ufw` is active)

```sh
sudo ufw allow 8443/tcp
```

**6. Open the app**

```
https://meshchat.local:8443
```

---

#### The Transport Node Console over the proxy

The console is served from the same origin as the app, at:

```
https://liberty.local:8443/transport-console/index.html
```

It finds the RNS bridge by itself and shows a green **RNS bridge found** banner.
No extra flag is needed: since v1.9.4 the bridge accepts same-origin WebSocket
connections, and it tolerates `proxy_set_header Host $host` stripping the port.
Cross-origin connections are still refused.

If the banner does not appear, the `Upgrade` and `Connection` headers above are
almost always the cause — the same headers the audio bridge needs.

#### Verifying the setup

Check that the proxy reaches the app:

```sh
curl -skI https://liberty.local:8443/api/v1/app/info
```

A `200 OK` response means the proxy is routing correctly.

Then open the app in a browser. If Docker is being detected properly, the **"Add LCS
Interfaces"** button will be **absent** from the header — that button only appears on
desktop installs. Its absence confirms the browser audio bridge is active.

To confirm the microphone is available, open the browser console (F12) and run:

```js
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(() => console.log("microphone OK"))
  .catch(e => console.log("microphone blocked:", e.name));
```

---

#### Important notes

**Always use the hostname, not the IP address.** The certificate is issued for a hostname
(`liberty.local`). If you browse to `https://192.168.2.1:8443` instead, the browser may
silently block the app's API and WebSocket requests even after you accept the certificate
warning — the page loads but calls will not work. The `subjectAltName` in the commands
above covers both the hostname and the IP, but the hostname remains the reliable choice.

**HTTPS is required, not optional.** Browsers only allow `getUserMedia` (microphone access)
in a secure context. Without HTTPS, calls will connect but carry no audio.

**Do not omit the WebSocket headers.** `proxy_http_version 1.1` together with the `Upgrade`
and `Connection` headers is what allows both the application event socket and the audio
bridge at `/api/v1/telephone/audio-bridge` to work. Without them, calls connect but no
audio passes in either direction.

**Self-signed certificates show a browser warning.** Accept it once per device. For a
cleaner result, either install the certificate as trusted on client devices or use Let's
Encrypt with a real domain name.

**The bridge is reachable directly on port 8082.** `--host=0.0.0.0` inside the
container means the published port bypasses the proxy entirely. Browsers are
stopped by the origin check, but a scripted client can send any `Origin` it
likes, and the RNS bridge can reboot and reconfigure remote nodes. Either bind
the published port to loopback as below, or add `--rns-bridge-token SECRET` to
the command and append `?token=SECRET` to the console's WebSocket field.

**Optional hardening.** If MeshChat and nginx run on the same machine, publish the
container port on loopback only:

```yaml
ports:
  - 127.0.0.1:8082:8000
```

This prevents direct unencrypted access on port 8082 and forces all traffic through the
HTTPS proxy.

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
