# microReticulum RNode Console

`index.html` is the console from the
[microReticulum_Firmware](https://github.com/attermann/microReticulum_Firmware)
project (GPL-3.0), with one addition: a small endpoint-discovery script inlined
before `</body>`, and the hard-coded `wss://127.0.0.1:9337/ws` default changed
to `window.__MESHCHAT_RNS_WS__ || "ws://127.0.0.1:9337/ws"`.

The file is self-contained. MeshChat serves it verbatim at
<http://127.0.0.1:8000/console>, and it behaves identically when opened from
disk or hosted on any static web server.

## How it connects

The console's "RNS (via MeshChatX)" transport opens a WebSocket and speaks
`rns.link.open` / `rns.link.request` / `rns.link.close`. MeshChat answers on:

| Endpoint | Use |
|---|---|
| `ws://127.0.0.1:<meshchat port>/rns/ws` | Primary. Same origin when served from here, so no TLS, no mixed content, no permission prompt. |
| `ws://127.0.0.1:9337/ws` | Fixed fallback, for a console opened from `file://` or a hosted copy. `--rns-bridge-port` changes it, `--disable-rns-bridge` turns both off. |

The inlined script finds whichever is live by opening each candidate and
sending `{"type":"ping"}`, then fills in the URL and switches the transport
selector. **None of that is required** — the stock console works too, you just
type the endpoint into the URL field yourself.

## Which transport for which node

| Transport | Reaches | Tabs available |
|---|---|---|
| Serial | node on USB | all |
| Bluetooth | node in BLE range | all |
| WebSocket `ws://localhost:8080` | a native `rnoded` daemon on this machine (port 81 on an embedded node's own AP) | all |
| RNS via MeshChatX | any node on the mesh, however many LoRa hops out | Node Status + Transport Config |

Logs and Node Config need KISS frames that don't survive the RNS hop, so they
are hidden on that transport. If your node is local, the WebSocket transport
gives you more.

## Deep links

`/console/` accepts `ws`, `port`, `token`, `dest`, `aspect`, `transport` and
`identify=0`:

```
http://127.0.0.1:8000/console/?dest=a1b2c3d4e5f60718293a4b5c6d7e8f90&transport=rns
```

## Replacing this file

Drop a newer `console.html` from the firmware project over `index.html`. The
discovery script is lost when you do; either re-inline it or just type the
endpoint into the URL field.

## Browser limits

A copy hosted on `https://` cannot reach a loopback bridge in Safari at all —
Safari blocks every mixed-content request including localhost, and no port or
certificate changes that. Chrome 141+ / Edge 142+ gate it behind the Local
Network Access permission. Neither limit is something this file can fix, which
is why MeshChat serves its own copy over `http://127.0.0.1`.

## License

The console originates from microReticulum_Firmware and is licensed GPL-3.0.
