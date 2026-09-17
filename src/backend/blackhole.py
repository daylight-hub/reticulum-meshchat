import time

import RNS


class BlackholeManager:

    """
    Wraps the blackhole API RNS exposes on the Reticulum instance.

    Blackholing works on *identity* hashes, while conversations in MeshChat are
    keyed by *destination* hashes, so anything coming from the UI is resolved
    through RNS.Identity.recall() first. That only succeeds once an announce
    carrying the peer's public key has been received, which is always true for
    a peer you have actually been messaging.

    The blocked list itself is persisted by RNS (storage/blackhole under the
    Reticulum config dir) and applies immediately: announces from a blackholed
    identity are dropped during validation, and its paths are removed.

    publish_blackhole, blackhole_sources and blackhole_update_interval are
    different: RNS reads them from the config file at startup, so writing them
    here takes effect on the next restart. Callers get requires_restart back so
    they can say so.
    """

    def __init__(self, reticulum):
        self.reticulum = reticulum

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _hash_from_hex(value, what="hash"):
        if value is None:
            raise ValueError(f"missing {what}")
        value = str(value).strip().lower().replace("<", "").replace(">", "")
        expected = RNS.Reticulum.TRUNCATED_HASHLENGTH // 8
        try:
            raw = bytes.fromhex(value)
        except ValueError:
            raise ValueError(f"{what} is not valid hex")
        if len(raw) != expected:
            raise ValueError(f"{what} must be {expected * 2} hex characters")
        return raw

    def _identity_hash_for_destination(self, destination_hash):
        identity = RNS.Identity.recall(destination_hash)
        if identity is None:
            raise ValueError(
                "no announce has been received from this peer yet, so its identity "
                "is not known and it can not be blocked"
            )
        return identity.hash

    def resolve_identity_hash(self, identity_hash=None, destination_hash=None):
        """Accept either form from the API and return identity hash bytes."""
        if identity_hash:
            return self._hash_from_hex(identity_hash, "identity_hash")
        if destination_hash:
            return self._identity_hash_for_destination(
                self._hash_from_hex(destination_hash, "destination_hash"))
        raise ValueError("provide identity_hash or destination_hash")

    # -- list / query ------------------------------------------------------

    def list(self):
        entries = []
        try:
            blackholed = self.reticulum.get_blackholed_identities() or {}
        except Exception:
            blackholed = {}

        # older and newer RNS builds hand this back as a dict of entries or as
        # a plain collection of hashes, so cope with both
        if isinstance(blackholed, dict):
            items = blackholed.items()
        else:
            items = [(entry, {}) for entry in blackholed]

        for identity_hash, entry in items:
            if not isinstance(entry, dict):
                entry = {}
            source = entry.get("source")
            until = entry.get("until")
            entries.append({
                "identity_hash": identity_hash.hex() if isinstance(identity_hash, (bytes, bytearray)) else str(identity_hash),
                "source": source.hex() if isinstance(source, (bytes, bytearray)) else source,
                "until": until,
                "expired": bool(until) and until < time.time(),
                "reason": entry.get("reason"),
                "local": self._is_local_source(source),
            })

        entries.sort(key=lambda e: (not e["local"], e["identity_hash"]))
        return entries

    def _is_local_source(self, source):
        try:
            local = RNS.Transport.identity.hash
        except Exception:
            return False
        if isinstance(source, (bytes, bytearray)):
            return bytes(source) == local
        return False

    def is_blocked(self, identity_hash=None, destination_hash=None):
        try:
            resolved = self.resolve_identity_hash(identity_hash, destination_hash)
        except ValueError:
            return False
        try:
            return bool(self.reticulum.is_blackholed(resolved))
        except Exception:
            return False

    # -- mutate ------------------------------------------------------------

    def block(self, identity_hash=None, destination_hash=None, reason=None, until=None):
        resolved = self.resolve_identity_hash(identity_hash, destination_hash)

        # refuse to blackhole ourselves, which would be an unpleasant surprise
        try:
            if RNS.Transport.identity is not None and resolved == RNS.Transport.identity.hash:
                raise ValueError("refusing to blackhole this node's own identity")
        except AttributeError:
            pass

        result = self.reticulum.blackhole_identity(resolved, until=until, reason=reason)
        return {
            "identity_hash": resolved.hex(),
            # RNS returns None when the identity was already on the list
            "blocked": result is not False,
            "already_blocked": result is None,
        }

    def unblock(self, identity_hash=None, destination_hash=None):
        resolved = self.resolve_identity_hash(identity_hash, destination_hash)
        result = self.reticulum.unblackhole_identity(resolved)
        return {
            "identity_hash": resolved.hex(),
            "unblocked": result is not False,
        }

    # -- publish / subscribe config ---------------------------------------

    def _reticulum_section(self):
        config = self.reticulum.config
        if "reticulum" not in config:
            config["reticulum"] = {}
        return config["reticulum"]

    @staticmethod
    def _as_bool(value, default=False):
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        return str(value).strip().lower() in ["yes", "true", "1", "on"]

    def get_config(self):
        section = self._reticulum_section()

        sources = section.get("blackhole_sources", [])
        if isinstance(sources, str):
            sources = [part.strip() for part in sources.split(",")]
        sources = [str(s).strip().lower() for s in sources if str(s).strip()]

        try:
            interval = int(section.get("blackhole_update_interval", 60))
        except (TypeError, ValueError):
            interval = 60

        return {
            "publish_blackhole": self._as_bool(section.get("publish_blackhole"), False),
            "blackhole_sources": sources,
            "blackhole_update_interval": interval,
            # what RNS is running with right now, which may differ from the file
            "active_source_count": len(getattr(RNS.Transport, "blackhole_sources", []) or []),
            "identity_hash": RNS.Transport.identity.hash.hex() if getattr(RNS.Transport, "identity", None) else None,
        }

    def set_config(self, publish_blackhole=None, blackhole_sources=None,
                   blackhole_update_interval=None):
        section = self._reticulum_section()

        if publish_blackhole is not None:
            section["publish_blackhole"] = "yes" if self._as_bool(publish_blackhole) else "no"

        if blackhole_sources is not None:
            if isinstance(blackhole_sources, str):
                blackhole_sources = [part.strip() for part in blackhole_sources.split(",")]
            cleaned = []
            for source in blackhole_sources:
                source = str(source).strip()
                if not source:
                    continue
                # validate before writing, a bad hash makes RNS refuse to start
                self._hash_from_hex(source, "blackhole source identity hash")
                if source.lower() not in cleaned:
                    cleaned.append(source.lower())
            section["blackhole_sources"] = cleaned

        if blackhole_update_interval is not None:
            interval = int(blackhole_update_interval)
            if interval < 1:
                raise ValueError("blackhole_update_interval must be at least 1 minute")
            section["blackhole_update_interval"] = interval

        self.reticulum.config.write()

        result = self.get_config()
        # RNS parses these at startup only
        result["requires_restart"] = True
        return result
