## HTTPS Reverse Proxy Setup (Docker)

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

### OpenWrt 24.10

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

### Debian

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

### The Transport Node Console over the proxy

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

### Verifying the setup

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

### Important notes

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
