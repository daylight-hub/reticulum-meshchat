#!/usr/bin/env python3
"""
src/backend/rns_link_bridge.py  --  RNS link bridge for the microReticulum RNode Console.

Speaks the "rns.link.*" WebSocket dialect that
console_cross_compatible_rak4631_Heltecv4_browseralert.html expects from its
"RNS (via MeshChatX)" transport, and turns those messages into real Reticulum
Link + Request traffic aimed at a microReticulum node's /provision handler.

Two backends:

  LocalBackend    uses the RNS instance MeshChat already owns (recommended).
                  No extra daemon, no extra RNS instance, no extra port.

  RnsApiBackend   proxies to a bundled attermann/ReticulumAPI (rnsapid) daemon
                  over its /ws endpoint, translating envelopes both ways.

Two ways to serve it:

  attach_to_app(app, backend)          mount on MeshChat's existing aiohttp app
                                       at /rns/ws  (same port as the web UI)

  run_standalone(backend, port=9337)   dedicated 127.0.0.1 listener, optional
                                       TLS, for consoles opened from file:// or
                                       from a page hosted over https://

Wire protocol (client -> server), all JSON text frames:

  {"type":"ping"}
  {"type":"rns.link.open",    "request_id":N, "destination_hash":"<32hex>",
                              "aspect":"rnstransport.remote.management",
                              "auto_identify":true}
  {"type":"rns.link.request", "request_id":N, "destination_hash":"...",
                              "aspect":"...", "path":"/provision",
                              "data_b64":"<base64 msgpack>"}
  {"type":"rns.link.close",   "request_id":N, "destination_hash":"...",
                              "aspect":"..."}

Server -> client:

  {"type":"pong"}
  {"type":"rns.link.open",    "request_id":N, "status":"phase",
                              "phase":"finding_path"|"establishing_link"|"identifying"}
  {"type":"rns.link.open",    "request_id":N, "status":"success", "identified":bool}
  {"type":"rns.link.request", "request_id":N, "status":"progress", "progress":0.0..1.0}
  {"type":"rns.link.request", "request_id":N, "status":"success", "body_b64":"<base64 msgpack>"}
  {"type":"rns.link.*",       "request_id":N, "status":"failure", "failure_reason":"..."}
  {"type":"rns.link.event",   "event":"link_closed", "destination_hash":"...", "aspect":"..."}

Payload convention: data_b64 / body_b64 carry the *msgpack encoding* of the
provisioning value, which is exactly the KISS-frame payload the console builds.
RNS.Link.request re-wraps it as msgpack([timestamp, path_hash, data]), so the
bridge msgpack-decodes on the way out and msgpack-encodes on the way back.
Net effect: base64 in == base64 out, byte-for-byte compatible with the console
and with a microReticulum /provision handler.

Apache-2.0, to match ReticulumAPI.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import binascii
import contextlib
import json
import logging
import os
import secrets
import ssl
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Dict, Optional, Tuple
from urllib.parse import urlparse

from aiohttp import web, ClientSession, WSMsgType

import RNS
from RNS.vendor import umsgpack

log = logging.getLogger("meshchat.rns_bridge")

# ---------------------------------------------------------------------------
# constants
# ---------------------------------------------------------------------------

DEFAULT_BRIDGE_PATH = "/rns/ws"
DEFAULT_STANDALONE_PORT = 9337
DEFAULT_ASPECT = "rnstransport.remote.management"
PROVISION_PATH = "/provision"

# failure_reason strings the console knows how to render. Anything else is
# shown verbatim, so passing an unknown string through is safe but uglier.
FAIL_NO_PATH = "no_path_to_destination"
FAIL_LINK_TIMEOUT = "link_establishment_timeout"
FAIL_NO_IDENTITY = "no_identity_for_destination"
FAIL_NO_LOCAL_IDENTITY = "no_local_identity"
FAIL_NO_ACTIVE_LINK = "no_active_link"
FAIL_TIMEOUT = "timeout"
FAIL_MISSING_ARGS = "missing_destination_or_aspect"
FAIL_BAD_HASH = "invalid_destination_hash"
FAIL_INTERNAL = "internal_error"

PHASE_FINDING_PATH = "finding_path"
PHASE_ESTABLISHING = "establishing_link"
PHASE_IDENTIFYING = "identifying"

# The console's watchdog for a link.request is 15 s, refreshed by every phase or
# progress frame. A /provision round trip over LoRa at SF11 can easily exceed
# that, so heartbeat while we wait.
PROGRESS_HEARTBEAT_SECONDS = 5.0


class BridgeFailure(Exception):
    """Carries a console-legible failure_reason."""

    def __init__(self, reason: str, detail: str = ""):
        super().__init__(detail or reason)
        self.reason = reason
        self.detail = detail


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def split_aspect(aspect: str) -> Tuple[str, Tuple[str, ...]]:
    """'rnstransport.remote.management' -> ('rnstransport', ('remote','management'))"""
    parts = [p for p in (aspect or "").split(".") if p]
    if not parts:
        raise BridgeFailure(FAIL_MISSING_ARGS, "empty aspect")
    return parts[0], tuple(parts[1:])


def parse_dest_hash(value: str) -> bytes:
    if not value:
        raise BridgeFailure(FAIL_MISSING_ARGS, "missing destination_hash")
    value = value.strip().lower()
    expected = RNS.Reticulum.TRUNCATED_HASHLENGTH // 8
    try:
        raw = bytes.fromhex(value)
    except (ValueError, binascii.Error):
        raise BridgeFailure(FAIL_BAD_HASH, "destination_hash is not hex")
    if len(raw) != expected:
        raise BridgeFailure(FAIL_BAD_HASH,
                            f"destination_hash must be {expected * 2} hex chars")
    return raw


def b64d(value: Optional[str]) -> bytes:
    if not value:
        return b""
    return base64.b64decode(value)


def b64e(raw: bytes) -> str:
    return base64.b64encode(raw or b"").decode("ascii")


# ---------------------------------------------------------------------------
# backend interface
# ---------------------------------------------------------------------------

PhaseHook = Callable[[str], Awaitable[None]]
LinkClosedHook = Callable[[str, str], Awaitable[None]]   # (dest_hash_hex, aspect)


class Backend:
    """One instance per WebSocket connection."""

    async def open_link(self, dest_hex: str, aspect: str, auto_identify: bool,
                        on_phase: PhaseHook) -> Dict[str, Any]:
        raise NotImplementedError

    async def request(self, dest_hex: str, aspect: str, path: str,
                      payload: bytes, timeout: float) -> bytes:
        raise NotImplementedError

    async def close_link(self, dest_hex: str, aspect: str) -> None:
        raise NotImplementedError

    async def shutdown(self) -> None:
        pass

    def set_link_closed_hook(self, hook: LinkClosedHook) -> None:
        self._link_closed_hook = hook


# ---------------------------------------------------------------------------
# local backend -- drives the RNS instance MeshChat already runs
# ---------------------------------------------------------------------------

@dataclass
class _LinkEntry:
    link: Any
    aspect: str
    identified: bool = False


class LocalBackend(Backend):
    """
    Uses the in-process RNS stack. Construct one per WebSocket connection:

        backend = LocalBackend(identity=self.identity)

    `identity` is the RNS.Identity the bridge will present to the remote node
    when auto_identify is set. In MeshChat that is normally `self.identity`,
    the same identity your LXMF address is derived from, which is what a
    microReticulum /provision ALLOW_LIST will have been configured against.
    """

    def __init__(self, identity: Optional[Any] = None,
                 path_timeout: float = 15.0,
                 establishment_timeout: float = 20.0,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self.identity = identity
        self.path_timeout = path_timeout
        self.establishment_timeout = establishment_timeout
        self.loop = loop or asyncio.get_event_loop()
        self.links: Dict[Tuple[str, str], _LinkEntry] = {}
        self._link_closed_hook: Optional[LinkClosedHook] = None
        self._lock = asyncio.Lock()

    # -- internals ---------------------------------------------------------

    def _fire_closed(self, dest_hex: str, aspect: str) -> None:
        """Called from an RNS thread. Hop back onto the event loop."""
        hook = self._link_closed_hook
        if hook is None:
            return
        with contextlib.suppress(RuntimeError):
            asyncio.run_coroutine_threadsafe(hook(dest_hex, aspect), self.loop)

    async def _await_path(self, dest_raw: bytes, on_phase: PhaseHook) -> None:
        if RNS.Transport.has_path(dest_raw):
            return
        await on_phase(PHASE_FINDING_PATH)
        RNS.Transport.request_path(dest_raw)
        deadline = time.monotonic() + self.path_timeout
        while time.monotonic() < deadline:
            if RNS.Transport.has_path(dest_raw):
                return
            await asyncio.sleep(0.15)
        raise BridgeFailure(FAIL_NO_PATH,
                            "no path after %.0fs" % self.path_timeout)

    async def _await_active(self, link: Any) -> None:
        deadline = time.monotonic() + self.establishment_timeout
        while time.monotonic() < deadline:
            status = link.status
            if status == RNS.Link.ACTIVE:
                return
            if status in (RNS.Link.CLOSED, RNS.Link.STALE):
                raise BridgeFailure(FAIL_LINK_TIMEOUT, "link closed while establishing")
            await asyncio.sleep(0.05)
        with contextlib.suppress(Exception):
            link.teardown()
        raise BridgeFailure(FAIL_LINK_TIMEOUT,
                            "not ACTIVE after %.0fs" % self.establishment_timeout)

    # -- Backend -----------------------------------------------------------

    async def open_link(self, dest_hex: str, aspect: str, auto_identify: bool,
                        on_phase: PhaseHook) -> Dict[str, Any]:
        dest_raw = parse_dest_hash(dest_hex)
        app_name, aspects = split_aspect(aspect)
        key = (dest_hex.lower(), aspect)

        async with self._lock:
            entry = self.links.get(key)
            if entry is not None and entry.link.status == RNS.Link.ACTIVE:
                return {"identified": entry.identified, "reused": True}
            if entry is not None:
                self.links.pop(key, None)

            await self._await_path(dest_raw, on_phase)

            identity = RNS.Identity.recall(dest_raw)
            if identity is None:
                raise BridgeFailure(
                    FAIL_NO_IDENTITY,
                    "no announce carrying this destination's public key has been received")

            await on_phase(PHASE_ESTABLISHING)
            destination = RNS.Destination(
                identity,
                RNS.Destination.OUT,
                RNS.Destination.SINGLE,
                app_name,
                *aspects,
            )
            link = RNS.Link(destination)
            link.set_link_closed_callback(
                lambda _l, _d=dest_hex.lower(), _a=aspect: self._fire_closed(_d, _a))

            await self._await_active(link)

            identified = False
            if auto_identify:
                if self.identity is None:
                    with contextlib.suppress(Exception):
                        link.teardown()
                    raise BridgeFailure(FAIL_NO_LOCAL_IDENTITY,
                                        "bridge has no local identity to present")
                await on_phase(PHASE_IDENTIFYING)
                link.identify(self.identity)
                # RNS orders packets per link, so the LINKIDENTIFY packet is
                # queued strictly before any request the console can dispatch.
                # No sleep needed, but give the queue a tick anyway.
                await asyncio.sleep(0.05)
                identified = True

            self.links[key] = _LinkEntry(link=link, aspect=aspect, identified=identified)
            return {"identified": identified, "reused": False}

    async def request(self, dest_hex: str, aspect: str, path: str,
                      payload: bytes, timeout: float) -> bytes:
        key = (dest_hex.lower(), aspect)
        entry = self.links.get(key)
        if entry is None or entry.link.status != RNS.Link.ACTIVE:
            self.links.pop(key, None)
            raise BridgeFailure(FAIL_NO_ACTIVE_LINK, "link is not active")

        # The console hands us the msgpack encoding of the provisioning value.
        # RNS.Link.request packs [timestamp, path_hash, data] itself, so decode
        # to the native value first and the bytes on the wire come out identical.
        try:
            value = umsgpack.unpackb(payload) if payload else None
        except Exception as exc:                                   # noqa: BLE001
            raise BridgeFailure(FAIL_INTERNAL, f"payload is not msgpack: {exc}")

        fut: asyncio.Future = self.loop.create_future()

        def _ok(receipt):
            if not fut.done():
                self.loop.call_soon_threadsafe(fut.set_result, receipt.response)

        def _fail(_receipt):
            if not fut.done():
                self.loop.call_soon_threadsafe(
                    fut.set_exception, BridgeFailure(FAIL_TIMEOUT, "remote did not respond"))

        try:
            entry.link.request(
                path,
                data=value,
                response_callback=_ok,
                failed_callback=_fail,
                timeout=timeout,
            )
        except Exception as exc:                                   # noqa: BLE001
            raise BridgeFailure(FAIL_NO_ACTIVE_LINK, str(exc))

        try:
            response = await asyncio.wait_for(fut, timeout=timeout + 5.0)
        except asyncio.TimeoutError:
            raise BridgeFailure(FAIL_TIMEOUT, "no response within %.0fs" % timeout)

        if response is None:
            return b""
        if isinstance(response, (bytes, bytearray)):
            # Handler returned raw bytes; re-pack as a msgpack bin so the
            # console's decoder sees the same shape it would from any peer.
            return umsgpack.packb(bytes(response))
        return umsgpack.packb(response)

    async def close_link(self, dest_hex: str, aspect: str) -> None:
        entry = self.links.pop((dest_hex.lower(), aspect), None)
        if entry is not None:
            with contextlib.suppress(Exception):
                entry.link.teardown()

    async def shutdown(self) -> None:
        for entry in list(self.links.values()):
            with contextlib.suppress(Exception):
                entry.link.teardown()
        self.links.clear()


# ---------------------------------------------------------------------------
# rnsapid backend -- proxy to a bundled attermann/ReticulumAPI daemon
# ---------------------------------------------------------------------------

class RnsApiBackend(Backend):
    """
    Translates the console dialect into ReticulumAPI's `link.*` dialect.

    Envelope differences handled here:

        console                     rnsapid
        -----------------------     ------------------------------------
        rns.link.open               link.open        (+ link.open.phase,
                                                      link.established,
                                                      link.open.failed)
        rns.link.request            link.request     (+ link.request.response,
                                                      link.request.failed)
        rns.link.close              link.close       (+ link.closed)
        request_id                  id
        aspect "a.b.c"              app_name "a", aspects ["b","c"]
        status/failure_reason       distinct message types + reason

    data_b64 / response_b64 pass straight through: rnsapid msgpack-decodes
    data_b64 before handing it to RNS.Link.request and msgpack-encodes whatever
    the handler returned, which is exactly the console's convention.
    """

    REASON_MAP = {
        "no_known_identity": FAIL_NO_IDENTITY,
        "link_establishment_timed_out": FAIL_LINK_TIMEOUT,
        "identify_failed": FAIL_NO_LOCAL_IDENTITY,
        "invalid_request": FAIL_MISSING_ARGS,
        "internal": FAIL_INTERNAL,
    }

    def __init__(self, url: str = "http://127.0.0.1:9337/ws",
                 token: Optional[str] = None,
                 verify_tls: bool = False,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self.url = url
        self.token = token
        self.verify_tls = verify_tls
        self.loop = loop or asyncio.get_event_loop()
        self._session: Optional[ClientSession] = None
        self._ws = None
        self._reader: Optional[asyncio.Task] = None
        self._next_id = 1
        self._waiters: Dict[str, asyncio.Future] = {}
        self._phase_hooks: Dict[str, PhaseHook] = {}
        self._link_closed_hook: Optional[LinkClosedHook] = None
        self._aspect_by_link: Dict[str, str] = {}
        self._connect_lock = asyncio.Lock()

    # -- plumbing ----------------------------------------------------------

    def _nid(self) -> str:
        self._next_id += 1
        return f"b{self._next_id}"

    async def _ensure(self) -> None:
        async with self._connect_lock:
            if self._ws is not None and not self._ws.closed:
                return
            if self._session is None or self._session.closed:
                self._session = ClientSession()
            ssl_ctx: Any = None
            if self.url.startswith("wss://") or self.url.startswith("https://"):
                ssl_ctx = None if self.verify_tls else False
            self._ws = await self._session.ws_connect(self.url, ssl=ssl_ctx,
                                                      heartbeat=30)
            if self.token:
                await self._ws.send_json({"type": "auth", "token": self.token})
            self._reader = asyncio.ensure_future(self._read_loop())

    async def _send(self, payload: Dict[str, Any]) -> None:
        await self._ensure()
        await self._ws.send_str(json.dumps(payload))

    async def _read_loop(self) -> None:
        try:
            async for msg in self._ws:
                if msg.type is not WSMsgType.TEXT:
                    continue
                try:
                    frame = json.loads(msg.data)
                except ValueError:
                    continue
                await self._dispatch(frame)
        except Exception as exc:                                   # noqa: BLE001
            log.debug("rnsapid reader stopped: %s", exc)
        finally:
            for fut in list(self._waiters.values()):
                if not fut.done():
                    fut.set_exception(BridgeFailure(FAIL_INTERNAL,
                                                    "rnsapid connection lost"))
            self._waiters.clear()

    async def _dispatch(self, frame: Dict[str, Any]) -> None:
        ftype = frame.get("type")
        fid = frame.get("id")

        if ftype == "link.open.phase":
            hook = self._phase_hooks.get(fid)
            if hook:
                await hook(frame.get("phase") or "")
            return

        if ftype in ("link.established", "link.open.failed",
                     "link.request.response", "link.request.failed",
                     "link.close.result", "error"):
            fut = self._waiters.pop(fid, None)
            self._phase_hooks.pop(fid, None)
            if fut is None or fut.done():
                return
            if ftype in ("link.established", "link.request.response",
                         "link.close.result"):
                fut.set_result(frame)
            else:
                raw = frame.get("reason") or frame.get("error") or "failure"
                fut.set_exception(BridgeFailure(self.REASON_MAP.get(raw, raw),
                                                frame.get("detail") or ""))
            return

        if ftype == "link.closed":
            dest = (frame.get("destination_hash") or "").lower()
            aspect = self._aspect_by_link.get(dest) or frame.get("aspect") or ""
            hook = self._link_closed_hook
            if hook and dest:
                await hook(dest, aspect)
            return

    async def _call(self, msg: Dict[str, Any], timeout: float,
                    on_phase: Optional[PhaseHook] = None) -> Dict[str, Any]:
        rid = self._nid()
        msg["id"] = rid
        fut: asyncio.Future = self.loop.create_future()
        self._waiters[rid] = fut
        if on_phase is not None:
            self._phase_hooks[rid] = on_phase
        try:
            await self._send(msg)
            return await asyncio.wait_for(fut, timeout=timeout)
        except asyncio.TimeoutError:
            raise BridgeFailure(FAIL_TIMEOUT, "rnsapid did not reply")
        finally:
            self._waiters.pop(rid, None)
            self._phase_hooks.pop(rid, None)

    # -- Backend -----------------------------------------------------------

    async def open_link(self, dest_hex: str, aspect: str, auto_identify: bool,
                        on_phase: PhaseHook) -> Dict[str, Any]:
        parse_dest_hash(dest_hex)
        app_name, aspects = split_aspect(aspect)
        self._aspect_by_link[dest_hex.lower()] = aspect
        frame = await self._call({
            "type": "link.open",
            "destination_hash": dest_hex.lower(),
            "app_name": app_name,
            "aspects": list(aspects),
            "auto_identify": bool(auto_identify),
        }, timeout=45.0, on_phase=on_phase)
        return {"identified": bool(frame.get("remote_identity_hash")) or auto_identify}

    async def request(self, dest_hex: str, aspect: str, path: str,
                      payload: bytes, timeout: float) -> bytes:
        frame = await self._call({
            "type": "link.request",
            "link_id": dest_hex.lower(),
            "destination_hash": dest_hex.lower(),
            "path": path,
            "data_b64": b64e(payload),
            "timeout": timeout,
        }, timeout=timeout + 5.0)
        return b64d(frame.get("response_b64"))

    async def close_link(self, dest_hex: str, aspect: str) -> None:
        with contextlib.suppress(BridgeFailure, asyncio.TimeoutError):
            await self._call({
                "type": "link.close",
                "link_id": dest_hex.lower(),
                "destination_hash": dest_hex.lower(),
            }, timeout=10.0)
        self._aspect_by_link.pop(dest_hex.lower(), None)

    async def shutdown(self) -> None:
        if self._reader is not None:
            self._reader.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reader
        if self._ws is not None and not self._ws.closed:
            await self._ws.close()
        if self._session is not None and not self._session.closed:
            await self._session.close()


# ---------------------------------------------------------------------------
# origin / token gate
# ---------------------------------------------------------------------------

LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1", "[::1]", "0.0.0.0"}


@dataclass
class BridgeConfig:
    """
    token          if set, clients must pass ?token=... on the WebSocket URL.
    allowed_origins  extra origins permitted in addition to loopback and file://.
                   Put your hosted console's origin here if you use one, e.g.
                   "https://daylight-hub.github.io".
    allow_any_origin  disables the origin check entirely. Do not. Same-origin
                   requests are already accepted, so a reverse proxy does not
                   need this.
    request_timeout  seconds allowed for one /provision round trip.
    """
    token: Optional[str] = None
    allowed_origins: Tuple[str, ...] = ()
    allow_any_origin: bool = False
    request_timeout: float = 30.0
    allow_file_origin: bool = True


def request_host(request) -> str:
    """
    The host the browser actually asked for. Behind a reverse proxy the Host
    header is often rewritten, so prefer the forwarded value when present.
    """
    forwarded = request.headers.get("X-Forwarded-Host", "")
    if forwarded:
        return forwarded.split(",")[0].strip().lower()
    return (request.headers.get("Host") or "").strip().lower()


def origin_allowed(origin: Optional[str], cfg: BridgeConfig,
                   host: Optional[str] = None) -> bool:
    if cfg.allow_any_origin:
        return True

    # file:// pages and some WebViews send Origin: null or no Origin at all.
    if origin in (None, "", "null"):
        return cfg.allow_file_origin

    if origin in cfg.allowed_origins:
        return True

    try:
        parsed = urlparse(origin)
    except ValueError:
        return False

    if (parsed.hostname or "").lower() in LOOPBACK_HOSTS:
        return True

    # Same origin: the page asking for the socket is the page MeshChat itself
    # just served, which is the whole legitimate case. This is what makes a
    # reverse-proxied deployment work without having to name its hostname.
    if host and parsed.netloc.lower() == host:
        return True

    return False


# ---------------------------------------------------------------------------
# the WebSocket handler
# ---------------------------------------------------------------------------

class RnsLinkBridge:
    """
    backend_factory: called once per WebSocket connection, returns a Backend.
    """

    def __init__(self, backend_factory: Callable[[], Backend],
                 config: Optional[BridgeConfig] = None):
        self.backend_factory = backend_factory
        self.config = config or BridgeConfig()

    # -- handler -----------------------------------------------------------

    async def handle(self, request: web.Request) -> web.WebSocketResponse:
        origin = request.headers.get("Origin")
        if not origin_allowed(origin, self.config, request_host(request)):
            log.warning("rns bridge: rejected origin %r", origin)
            return web.Response(status=403, text="origin not allowed")

        if self.config.token:
            if not secrets.compare_digest(request.query.get("token", ""),
                                          self.config.token):
                log.warning("rns bridge: bad or missing token from %r", origin)
                return web.Response(status=401, text="token required")

        ws = web.WebSocketResponse(heartbeat=30, max_msg_size=8 * 1024 * 1024)
        await ws.prepare(request)

        backend = self.backend_factory()

        async def on_link_closed(dest_hex: str, aspect: str) -> None:
            await self._safe_send(ws, {
                "type": "rns.link.event",
                "event": "link_closed",
                "destination_hash": dest_hex,
                "aspect": aspect,
            })

        backend.set_link_closed_hook(on_link_closed)

        tasks: set = set()
        try:
            async for msg in ws:
                if msg.type is not WSMsgType.TEXT:
                    continue
                try:
                    frame = json.loads(msg.data)
                except ValueError:
                    continue
                if not isinstance(frame, dict):
                    continue

                ftype = frame.get("type")

                if ftype == "ping":
                    await self._safe_send(ws, {"type": "pong", "t": time.time()})
                    continue

                if ftype not in ("rns.link.open", "rns.link.request",
                                 "rns.link.close"):
                    continue

                # Each command runs concurrently: the console fires overlapping
                # provisioning requests and expects them correlated by
                # request_id, not serialised.
                task = asyncio.ensure_future(
                    self._handle_command(ws, backend, frame))
                tasks.add(task)
                task.add_done_callback(tasks.discard)
        finally:
            for task in list(tasks):
                task.cancel()
            with contextlib.suppress(Exception):
                await backend.shutdown()

        return ws

    # -- command dispatch --------------------------------------------------

    async def _handle_command(self, ws, backend: Backend,
                              frame: Dict[str, Any]) -> None:
        ftype = frame["type"]
        rid = frame.get("request_id")
        dest_hex = (frame.get("destination_hash") or "").strip().lower()
        aspect = frame.get("aspect") or DEFAULT_ASPECT

        async def phase(name: str) -> None:
            await self._safe_send(ws, {"type": ftype, "request_id": rid,
                                       "status": "phase", "phase": name})

        try:
            # validate up front so every backend reports the same failure
            # reasons for the same malformed input
            if ftype in ("rns.link.open", "rns.link.request"):
                parse_dest_hash(dest_hex)
                split_aspect(aspect)

            if ftype == "rns.link.open":
                result = await backend.open_link(
                    dest_hex, aspect, bool(frame.get("auto_identify")), phase)
                await self._safe_send(ws, {
                    "type": ftype, "request_id": rid, "status": "success",
                    "destination_hash": dest_hex, "aspect": aspect,
                    "identified": bool(result.get("identified")),
                })

            elif ftype == "rns.link.request":
                path = frame.get("path") or PROVISION_PATH
                payload = b64d(frame.get("data_b64"))
                body = await self._request_with_heartbeat(
                    ws, backend, ftype, rid, dest_hex, aspect, path, payload)
                await self._safe_send(ws, {
                    "type": ftype, "request_id": rid, "status": "success",
                    "destination_hash": dest_hex, "aspect": aspect,
                    "path": path, "body_b64": b64e(body),
                })

            elif ftype == "rns.link.close":
                await backend.close_link(dest_hex, aspect)
                await self._safe_send(ws, {
                    "type": ftype, "request_id": rid, "status": "success",
                    "destination_hash": dest_hex, "aspect": aspect,
                })

        except BridgeFailure as exc:
            log.info("rns bridge: %s failed: %s (%s)", ftype, exc.reason, exc.detail)
            await self._safe_send(ws, {
                "type": ftype, "request_id": rid, "status": "failure",
                "destination_hash": dest_hex, "aspect": aspect,
                "failure_reason": exc.reason, "detail": exc.detail,
            })
        except asyncio.CancelledError:
            raise
        except Exception as exc:                                   # noqa: BLE001
            log.exception("rns bridge: unhandled error in %s", ftype)
            await self._safe_send(ws, {
                "type": ftype, "request_id": rid, "status": "failure",
                "failure_reason": FAIL_INTERNAL, "detail": str(exc),
            })

    async def _request_with_heartbeat(self, ws, backend: Backend, ftype: str,
                                      rid: Any, dest_hex: str, aspect: str,
                                      path: str, payload: bytes) -> bytes:
        """
        The console's per-request watchdog is 15 s and is reset by every phase
        or progress frame. A provisioning round trip over a slow LoRa link is
        routinely longer than that, so emit progress while we wait.
        """
        timeout = self.config.request_timeout
        task = asyncio.ensure_future(
            backend.request(dest_hex, aspect, path, payload, timeout))
        started = time.monotonic()
        while True:
            done, _ = await asyncio.wait({task}, timeout=PROGRESS_HEARTBEAT_SECONDS)
            if done:
                return task.result()
            elapsed = time.monotonic() - started
            await self._safe_send(ws, {
                "type": ftype, "request_id": rid, "status": "progress",
                "progress": min(0.95, elapsed / max(timeout, 1.0)),
            })

    @staticmethod
    async def _safe_send(ws, payload: Dict[str, Any]) -> None:
        if ws.closed:
            return
        with contextlib.suppress(Exception):
            await ws.send_str(json.dumps(payload))


# ---------------------------------------------------------------------------
# mounting
# ---------------------------------------------------------------------------

def _health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "meshchat-rns-bridge"})


def attach_to_app(app: web.Application,
                  backend_factory: Callable[[], Backend],
                  config: Optional[BridgeConfig] = None,
                  path: str = DEFAULT_BRIDGE_PATH) -> RnsLinkBridge:
    """
    Mount the bridge on MeshChat's existing aiohttp application.

    The bridge lives on the same origin and port as the MeshChat web UI, so the
    transport console served from src/frontend/public/transport-console/
    connects with a relative URL: no TLS, no mixed content and no
    local-network-access permission in any browser.

    Must be registered BEFORE MeshChat's catch-all `web.static('/', 'public/')`
    route, otherwise the static resource swallows /console and /rns/ws.
    """
    bridge = RnsLinkBridge(backend_factory, config)
    app.router.add_get(path, bridge.handle)
    app.router.add_get(path.rsplit("/", 1)[0] + "/health", _health)
    return bridge


def build_ssl_context(cert_path: str, key_path: str,
                      generate: bool = True) -> ssl.SSLContext:
    """
    Load a TLS cert, generating a self-signed one valid for localhost, 127.0.0.1
    and ::1 if it is missing. `cryptography` is already an RNS dependency.
    """
    if generate and not (os.path.exists(cert_path) and os.path.exists(key_path)):
        from datetime import datetime, timedelta, timezone
        import ipaddress
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec

        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "MeshChat RNS Bridge")])
        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(name)
            .issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName([
                x509.DNSName("localhost"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None),
                           critical=True)
            .sign(key, hashes.SHA256())
        )
        os.makedirs(os.path.dirname(os.path.abspath(cert_path)), exist_ok=True)
        with open(key_path, "wb") as fh:
            fh.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()))
        with open(cert_path, "wb") as fh:
            fh.write(cert.public_bytes(serialization.Encoding.PEM))
        os.chmod(key_path, 0o600)
        log.info("generated self-signed bridge certificate at %s", cert_path)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_path, key_path)
    return ctx


async def run_standalone(backend_factory: Callable[[], Backend],
                         config: Optional[BridgeConfig] = None,
                         host: str = "127.0.0.1",
                         port: int = DEFAULT_STANDALONE_PORT,
                         path: str = "/ws",
                         ssl_context: Optional[ssl.SSLContext] = None) -> web.AppRunner:
    """
    Dedicated listener on 127.0.0.1:9337, matching the console's stock default
    URL shape. Use this in addition to attach_to_app when you want a fixed,
    predictable endpoint that does not move when MeshChat's own port changes.
    """
    app = web.Application()
    bridge = RnsLinkBridge(backend_factory, config)
    app.router.add_get(path, bridge.handle)
    app.router.add_get("/health",
                       lambda _r: web.json_response({"status": "ok",
                                                     "service": "meshchat-rns-bridge"}))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port, ssl_context=ssl_context)
    await site.start()
    scheme = "wss" if ssl_context else "ws"
    log.info("RNS console bridge listening on %s://%s:%d%s", scheme, host, port, path)
    return runner


# ---------------------------------------------------------------------------
# standalone entry point (useful for testing without touching meshchat.py)
# ---------------------------------------------------------------------------

async def _amain(args) -> None:
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s %(message)s")

    config = BridgeConfig(
        token=args.token,
        allowed_origins=tuple(args.allow_origin or ()),
        request_timeout=args.request_timeout,
    )

    identity = None
    if args.backend == "local":
        RNS.Reticulum(configdir=args.reticulum_config_dir)
        if args.identity_file:
            identity = RNS.Identity.from_file(args.identity_file)
        else:
            identity = RNS.Identity()
            log.warning("no --identity-file given, generated an ephemeral identity; "
                        "a /provision ALLOW_LIST on the node will reject it")
        loop = asyncio.get_running_loop()
        factory = lambda: LocalBackend(identity=identity, loop=loop)      # noqa: E731
    else:
        loop = asyncio.get_running_loop()
        factory = lambda: RnsApiBackend(url=args.rnsapi_url,             # noqa: E731
                                        token=args.rnsapi_token,
                                        loop=loop)

    ssl_ctx = None
    if args.tls:
        ssl_ctx = build_ssl_context(args.cert, args.key)

    await run_standalone(factory, config, host=args.host, port=args.port,
                         ssl_context=ssl_ctx)

    scheme = "wss" if ssl_ctx else "ws"
    print(f"\n  Console URL:  {scheme}://127.0.0.1:{args.port}/ws"
          + (f"?token={args.token}" if args.token else ""))
    print(f"  Health check: {'https' if ssl_ctx else 'http'}://127.0.0.1:{args.port}/health\n")

    with contextlib.suppress(asyncio.CancelledError):
        await asyncio.Event().wait()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RNS link bridge for the microReticulum RNode Console")
    parser.add_argument("--backend", choices=("local", "rnsapi"), default="local")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=DEFAULT_STANDALONE_PORT)
    parser.add_argument("--token", default=None,
                        help="require ?token=... on the WebSocket URL")
    parser.add_argument("--allow-origin", action="append",
                        help="extra allowed Origin, repeatable")
    parser.add_argument("--request-timeout", type=float, default=30.0)
    parser.add_argument("--identity-file", default=None)
    parser.add_argument("--reticulum-config-dir", default=None)
    parser.add_argument("--rnsapi-url", default="http://127.0.0.1:9338/ws")
    parser.add_argument("--rnsapi-token", default=None)
    parser.add_argument("--tls", action="store_true")
    parser.add_argument("--cert", default=os.path.expanduser("~/.config/meshchat/bridge-cert.pem"))
    parser.add_argument("--key", default=os.path.expanduser("~/.config/meshchat/bridge-key.pem"))
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    try:
        asyncio.run(_amain(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
