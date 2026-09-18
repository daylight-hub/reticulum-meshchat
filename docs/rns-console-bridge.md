# RNS console bridge

MeshChat already ships the microReticulum RNode Console at
`src/frontend/public/transport-console/index.html`, linked from the Tools page.
This adds the server side it needs to reach nodes over Reticulum.

## What it does

The console's "RNS (via MeshChatX)" transport opens a WebSocket and speaks
`rns.link.open` / `rns.link.request` / `rns.link.close`. MeshChat answers that on
its own web server at `/rns/ws` and turns it into real RNS Link + Request
traffic aimed at a node's `/provision` handler.

Because the Electron app runs MeshChat on port 9337, and the console is served
from `/transport-console/index.html` on that same server, the console reaches
the bridge at a same-origin relative URL. No TLS, no mixed content, no
local-network-access permission in any browser.

## Why it isn't ReticulumAPI

The console's dialect came from MeshChatX, not from `attermann/ReticulumAPI`:

| | Console | `rnsapid` |
|---|---|---|
| open | `rns.link.open` | `link.open` |
| correlation | `request_id` | `id` |
| outcome | `status: phase/progress/success/failure` | separate message types |
| aspect | `"rnstransport.remote.management"` | `app_name` + `aspects[]` |
| response | `body_b64` | `response_b64` |

Only `ping`/`pong` matches, so dropping `rnsapid` in unmodified would pass the
console's 5 s verify step and then hang on link open. `RnsApiBackend` in
`src/backend/rns_link_bridge.py` does the translation if you want that path;
`LocalBackend` is the default and uses the RNS instance MeshChat already runs —
no sidecar, no second identity store, no self-signed TLS.

The base64 payload passes through untouched in both directions: `rnsapid`
msgpack-decodes `data_b64` before handing it to `RNS.Link.request`, which is
exactly the convention the console uses.

## Endpoints

| Endpoint | Notes |
|---|---|
| `ws://127.0.0.1:<meshchat port>/rns/ws` | Always on. 9337 in the desktop app. |
| `http://127.0.0.1:<port>/rns/health` | `{"status": "ok"}` |
| `--rns-bridge-port N` | Optional extra loopback listener at `ws://127.0.0.1:N/ws`, for a console opened from disk. Off by default — the desktop app already occupies 9337. |

## CLI flags

```
--disable-rns-bridge              turn it off
--rns-bridge-port N               optional extra fixed loopback listener
--rns-bridge-token SECRET         require ?token=SECRET on the WebSocket
--rns-bridge-allow-origin ORIGIN  extra allowed browser Origin, repeatable
```

## Console changes

`transport-console/index.html` is the upstream file with one addition: an
inlined script before `</body>` that probes for the bridge with the same
`{"type":"ping"}` handshake the RNS transport uses, fills in the URL and selects
the RNS transport. Order tried: `?ws=` parameter, cached URL, **same origin** +
`/rns/ws`, then `localhost` and `127.0.0.1` on 9337/8000/8080/4000. It drives
the console through its own `input`/`change` handlers, so it survives a console
rebuild as long as the `title` attributes on those inputs stay put.

Query parameters: `ws`, `port`, `token`, `dest`, `aspect`, `transport`,
`identify=0`. So Tools can deep-link a node:
`/transport-console/index.html?dest=<32 hex>&transport=rns`.

A hosted `https://` copy still cannot reach a loopback bridge in Safari (all
mixed content is blocked, including localhost) and needs the Local Network
Access permission in Chrome 141+. That is why MeshChat serves its own copy.

## Security

WebSockets are not subject to CORS, so any page in any tab could otherwise
reach `ws://127.0.0.1:9337/rns/ws` and drive your identity into every node whose
`/provision` ALLOW_LIST you are on — including reboot and EEPROM wipe.
`BridgeConfig` gates it with an origin allowlist (loopback plus `null` for
`file://`) and an optional token. Keep `--host` on loopback; MeshChat prints a
warning if it isn't and no token is set.

## Using it

Read the node's destination hash from the Node Status tab over Serial once, put
your MeshChat identity hash in the node's `/provision` ALLOW_LIST, then pick
**RNS (via MeshChatX)**, paste the hash, leave authenticate ticked, Connect.
Logs and Node Config stay hidden on this transport — they need legacy KISS
opcodes that don't cross the RNS hop.
