# Shipping the RNode Console bridge in MeshChat v1.8.9

## The short version

- **Don't use 9337 as the primary endpoint.** Serve the bridge on MeshChat's own
  port at `/rns/ws`, and serve the console itself from MeshChat at `/console`.
  Same origin means no TLS, no mixed content, no permission prompt, and it is
  the only arrangement that works in all three browser engines.
- **Keep 9337 as a secondary fixed listener** for consoles opened from `file://`
  or from a hosted copy. That is the port the console already defaults to, and
  it avoids the collision you would otherwise hit: `rnsapid` also defaults to
  **8000**, which is MeshChat's port.
- **The console does not speak ReticulumAPI's protocol.** Dropping `rnsapid` in
  as-is will not make the console work. A translation layer is required either
  way; `meshchat_rns_bridge.py` is that layer.

---

## 1. Why a shim is needed at all

The console's "RNS (via MeshChatX)" transport speaks a dialect that came from
MeshChatX, not from ReticulumAPI. The two differ on every field:

| | Console expects | `rnsapid` sends/accepts |
|---|---|---|
| open | `rns.link.open` | `link.open` |
| correlation | `request_id` | `id` |
| outcome | `status: phase / progress / success / failure` | separate types: `link.open.phase`, `link.established`, `link.open.failed` |
| aspect | `"rnstransport.remote.management"` (dotted string) | `app_name` + `aspects[]` (no dots allowed) |
| response body | `body_b64` | `response_b64` |
| failure | `failure_reason` | `reason` + `detail` |
| teardown | `rns.link.event` / `event: "link_closed"` | `link.closed` |

Only `ping` → `pong` matches, which is why the console's pre-flight check would
pass against `rnsapid` and then the link open would hang until the 5 s verify
window expired.

One thing that *does* line up perfectly: the payload convention. The console
base64s the raw msgpack it would have put in a KISS frame; `rnsapid`
msgpack-decodes `data_b64` before handing it to `RNS.Link.request`, which
re-wraps it as `msgpack([timestamp, path_hash, data])`. So `data_b64` passes
through byte-for-byte in both directions and a microReticulum `/provision`
handler sees exactly what it expects. `meshchat_rns_bridge.py` preserves that.

The phase names (`finding_path`, `establishing_link`, `identifying`) and the
`auto_identify` ordering guarantee are identical in both, so the bridge maps
them straight across.

---

## 2. Port assignment

| Port | Listener | Purpose |
|---|---|---|
| **8000** (MeshChat's `--port`) | `/rns/ws` + `/console` | Primary. Same origin as the UI. |
| **9337** | `/ws` on 127.0.0.1 | Fixed fallback for `file://` and hosted consoles. Matches the console's stock default. |
| 9338 | `rnsapid` | Only if you bundle ReticulumAPI. Move it off its default 8000 so it doesn't fight MeshChat. |

9337 has no IANA assignment and is what the console already suggests, so keeping
it costs nothing and saves your users a config step.

---

## 3. Wiring it into `meshchat.py`

MeshChat is aiohttp, so this is three lines in `run()`, right after the route
table is built and before `web.run_app`:

```python
from meshchat_rns_bridge import (
    LocalBackend, BridgeConfig, attach_to_app, run_standalone,
)

# ... inside ReticulumMeshChat.run(), after `app = web.Application()` ...

loop = asyncio.get_event_loop()
bridge_config = BridgeConfig(
    # allowed_origins=("https://daylight-hub.github.io",),   # only if you host a copy
    request_timeout=30.0,
)

attach_to_app(
    app,
    backend_factory=lambda: LocalBackend(identity=self.identity, loop=loop),
    config=bridge_config,
    console_dir=os.path.join(os.path.dirname(__file__), "public", "console"),
)
```

Drop `console_meshchat_rns_autoconnect.html` into
`public/console/index.html` and it is reachable at
`http://127.0.0.1:8000/console`, where it will find the bridge with a relative
URL on the first probe.

For the fixed 9337 listener, add an `on_startup` hook:

```python
async def _start_bridge(_app):
    _app["rns_bridge_runner"] = await run_standalone(
        backend_factory=lambda: LocalBackend(identity=self.identity, loop=loop),
        config=bridge_config,
        host="127.0.0.1",
        port=9337,
    )

async def _stop_bridge(_app):
    runner = _app.get("rns_bridge_runner")
    if runner:
        await runner.cleanup()

app.on_startup.append(_start_bridge)
app.on_shutdown.append(_stop_bridge)
```

`LocalBackend` uses the RNS instance MeshChat already owns. No second
`RNS.Reticulum()`, no shared-instance RPC hop, no extra process in the Electron
bundle. `self.identity` is the right identity to pass: it is the one your LXMF
address derives from, so it is the one a node operator will have put in the
`/provision` ALLOW_LIST.

### If you want ReticulumAPI in the bundle anyway

Swap the factory:

```python
from meshchat_rns_bridge import RnsApiBackend

backend_factory = lambda: RnsApiBackend(url="http://127.0.0.1:9338/ws", loop=loop)
```

and launch `rnsapid` as a sidecar from the Electron main process with
`[network] allow_http = true`, `port = 9338`. Point it at the same
`~/.config/reticulum` and set `share_instance = Yes` in the Reticulum config so
it attaches to MeshChat's instance rather than starting a competing one.

Be aware of the trade: a second process in the installer, a second identity
store (`~/.config/rnsapi/default_identity`) that the user has to populate to
match their MeshChat identity, and rnsapid's self-signed TLS if you leave
`allow_http = false`. `LocalBackend` avoids all of it. My recommendation is to
ship `LocalBackend` as the default and expose `RnsApiBackend` behind a setting
for people who already run `rnsapid`.

---

## 4. https / offline behaviour

This is where the port choice actually matters, because browsers treat the
loopback carve-out very differently.

| Console opened from | Chrome / Edge | Firefox | Safari |
|---|---|---|---|
| MeshChat: `http://127.0.0.1:8000/console` | works | works | works |
| `file://` on the same machine | works | works | works |
| `http://` from a LAN box | works | works | works (but Web Serial / BLE are disabled — not a secure context) |
| `https://` hosted → `ws://127.0.0.1` | permission prompt since Chrome 141 / Edge 142 | mixed-content exempt for the `localhost` hostname; unreliable for the bare `127.0.0.1` literal | **never** |
| `https://` hosted → `wss://127.0.0.1:9337` with self-signed cert | works after the user accepts the cert at `https://127.0.0.1:9337/health`, still subject to the permission prompt | same | still blocked |

Two consequences:

1. **There is no configuration that makes a page hosted on `https://` reach a
   local bridge in Safari.** Safari blocks all mixed content including loopback.
   The only fix is serving the console locally — which is exactly what
   `/console` does.
2. Chrome 141+ gates public-origin → loopback behind the Local Network Access
   permission ("Access other apps and services on this device"). It will prompt
   on first probe. That is survivable for a hosted copy but it is one more thing
   to fail, and it is avoided entirely by same-origin.

So: publish the hosted copy if you like, but make
`http://127.0.0.1:8000/console` the link in the release notes.

### What the patched console does about it

`console_meshchat_rns_autoconnect.html` is the file you sent with two changes:

- the hard-coded `wss://127.0.0.1:9337/ws` default became
  `window.__MESHCHAT_RNS_WS__ || "ws://127.0.0.1:9337/ws"`;
- an appended script probes for the bridge and fills the field in.

The probe is the same `{"type":"ping"}` → `{"type":"pong"}` handshake the RNS
transport already uses, so anything that answers a probe will also complete the
transport's own verify step. Order tried:

1. `?ws=` query parameter
2. last known good URL from `localStorage`
3. **same origin** + `/rns/ws`
4. `?port=` if given
5. `localhost` then `127.0.0.1`, on 8000/8080/4000 `/rns/ws`, then 9337 `/ws`
6. the `wss://` variants, only when the page itself is https

`localhost` is deliberately tried before `127.0.0.1` — Firefox's mixed-content
exemption is written against the hostname.

On success it writes the URL into the field, switches the transport selector to
RNS, and shows a green banner for six seconds. On failure it names the actual
cause for the browser in use rather than "connect failed", including the
`local-network-access` permission state when Chrome exposes it.

It touches nothing inside the console's closure. It sets `.value` and dispatches
the `input` / `change` events the existing handlers are already bound to, so it
will survive a console rebuild as long as the `title` attributes on those inputs
stay put.

Query parameters it understands: `ws`, `port`, `token`, `dest`, `aspect`,
`transport`, `identify=0`. So MeshChat can deep-link straight to a node:

```
/console/?dest=a1b2c3...&transport=rns
```

---

## 5. Security — please don't skip this

**WebSockets are not subject to CORS.** Any page in any tab can open
`ws://127.0.0.1:8000/rns/ws` while MeshChat is running. Without a check, a
random website could drive your identity into every node whose ALLOW_LIST you
are on — and the console's own surface includes reboot, EEPROM wipe, TNC/HOST
mode switching and radio reconfiguration. That is a genuinely bad day.

`BridgeConfig` gates it two ways:

- **Origin allowlist**, on by default: loopback origins plus `null` (which is
  what `file://` sends). Add your hosted origin explicitly if you publish one.
  `allow_any_origin=True` exists and should stay unused.
- **Token**, off by default: set `BridgeConfig(token=...)` and clients must pass
  `?token=…`. Worth enabling on the 9337 listener specifically, since that one
  is the most likely to get exposed by a careless reverse proxy. Surface the
  token in MeshChat's UI and append it to the `/console` deep link so the local
  flow stays one click.

Also keep both listeners bound to `127.0.0.1`, not `0.0.0.0`. MeshChat's own
`--host` defaults to `0.0.0.0`; `run_standalone` deliberately does not inherit
that.

---

## 6. Testing without touching `meshchat.py`

```bash
python meshchat_rns_bridge.py \
    --backend local \
    --identity-file ~/.reticulum/storage/identities/meshchat \
    --port 9337 -v
```

then open the patched console from disk. It should find `ws://127.0.0.1:9337/ws`
on the fifth probe or so and go green. `--tls` generates a self-signed cert for
`localhost`, `127.0.0.1` and `::1` if you want to exercise the `wss://` path;
visit `https://127.0.0.1:9337/health` once first to accept it.

To check the rnsapid path:

```bash
rnsapid   # with port = 9338, allow_http = true in ~/.config/rnsapi/config
python meshchat_rns_bridge.py --backend rnsapi --rnsapi-url http://127.0.0.1:9338/ws
```

---

## 7. One implementation detail worth knowing

The console's per-request watchdog is 15 seconds, and it is reset by every
`phase` or `progress` frame it receives. A `/provision` round trip at SF11/125k
can exceed that on a multi-hop path, so the bridge emits a `progress` frame
every 5 seconds while a request is outstanding. Without that heartbeat the
console gives up on perfectly healthy slow links. If you reimplement the bridge
yourself, keep it.

---

## Files

| File | What it is |
|---|---|
| `meshchat_rns_bridge.py` | The bridge. `LocalBackend` + `RnsApiBackend`, aiohttp mount helpers, origin/token gate, self-signed cert generation, standalone CLI. Apache-2.0 to match ReticulumAPI. |
| `console_meshchat_rns_autoconnect.html` | Your console with endpoint auto-discovery and browser-specific diagnostics. Drop in `public/console/index.html`. |
