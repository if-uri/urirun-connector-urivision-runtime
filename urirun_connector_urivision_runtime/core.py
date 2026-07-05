# Author: Tom Sapletta · Part of the ifURI solution.
"""urirun-connector-urivision-runtime — native URI surface over urivision's CapabilityRegistry.

urivision's runtime is the CONTRACT MAP of the perception/action stack: a CapabilityRegistry
of URI-addressed capabilities (ui://, input://, view://, browser://, vision://, guard://…)
with schemas, preconditions and safety tags — deliberately mock-backed, because the REAL
execution already lives in urirun connectors (kvm/vql/vdisplay). What the mesh lacked was the
CATALOG: a way for a flow, planner, or node to discover and reason over that contract map.
This connector serves it as ``runtime://`` routes — catalog, explain, and a guarded
(dry-run-by-default) dispatch — without duplicating any implementation.

Built to URI_NATIVE_CONNECTOR_CHECKLIST: lazy imports, handlers never raise (urirun envelope),
catalog/explain queries are in-process; the dispatching call route is isolated. A fresh default
registry is built per call — the mock state does not persist between invocations.
"""
from __future__ import annotations

from typing import Any

import urirun

CONNECTOR_ID = "urivision-runtime"
conn = urirun.connector(CONNECTOR_ID, scheme="runtime")


def _ok(**kw: Any) -> dict[str, Any]:
    return urirun.ok(connector=CONNECTOR_ID, **kw)


def _fail(msg: str, action: str, **extra: Any) -> dict[str, Any]:
    return urirun.fail(msg, connector=CONNECTOR_ID, action=action, **extra)


def _runtime():
    from urivision.runtime import default_runtime
    return default_runtime()


@conn.handler("capabilities/query/list", isolated=False,
              meta={"label": "List the urivision capability catalog (the contract map of the perception/action stack)"})
def capabilities_list(format: str = "json") -> dict[str, Any]:
    """The catalog: every URI-addressed capability urivision knows, with schemas, safety tags
    and preconditions. ``format``: json (structured), markdown / prompt (LLM cards), tools
    (OpenAI-style tool description). First step for any planner using the runtime."""
    if format not in ("json", "markdown", "prompt", "tools"):
        return _fail(f"unknown format {format!r} (json|markdown|prompt|tools)", "runtime-catalog")
    try:
        rt = _runtime()
        catalog = rt.catalog(format)
        count = len(rt.registry.all())
    except Exception as exc:  # noqa: BLE001
        return _fail(str(exc), "runtime-catalog", hint="pip install urivision")
    return _ok(action="runtime-catalog", format=format, count=count, catalog=catalog)


@conn.handler("capability/query/explain", isolated=False,
              meta={"label": "Explain which capability handles a URI and what payload it expects"})
def capability_explain(uri: str = "") -> dict[str, Any]:
    """Resolve one URI against the catalog: which capability pattern matches, its captures,
    input/output schema, safety tags. The cheap gate before dispatching anything."""
    if not uri:
        return _fail("uri is required", "runtime-explain")
    try:
        cap, captures = _runtime().registry.find(uri)
    except Exception as exc:  # noqa: BLE001 - includes UriDispatchError (no match)
        return _fail(str(exc), "runtime-explain")
    return _ok(action="runtime-explain", uri=uri, captures=captures, capability=cap.to_dict())


@conn.handler("capability/command/call", isolated=True,
              meta={"label": "Dispatch a capability through the registry (dry-run by default; execute=true runs the mock-backed handler)"})
def capability_call(uri: str = "", payload: dict | None = None, execute: bool = False) -> dict[str, Any]:
    """Dispatch ``uri`` with ``payload`` through the CapabilityRegistry. Default is a DRY RUN:
    the payload is validated and the capability that WOULD run is returned — no handler invoked.
    ``execute=true`` runs the registered handler (the default registry is mock-backed; real
    execution belongs to kvm/vql/vdisplay connectors). State is per-call, not persisted."""
    if not uri:
        return _fail("uri is required", "runtime-call")
    try:
        result = _runtime().call(uri, payload or {}, dry_run=not execute)
    except Exception as exc:  # noqa: BLE001 - dispatch/validation errors → envelope
        return _fail(str(exc), "runtime-call")
    return _ok(action="runtime-call", uri=uri, executed=bool(execute), result=result)


def urirun_bindings() -> dict[str, Any]:
    """Serializable v2 bindings (entry point: urirun.bindings)."""
    return conn.bindings()


def connector_manifest() -> dict[str, Any]:
    """Manifest prose + a GENERATED per-URI capability list (URI_COMMAND_STANDARD.md §6)."""
    m = urirun.load_manifest(__package__) or {}
    try:
        from urirun_connectors_toolkit.connector_sdk import manifest_routes
        m["routes"] = manifest_routes(urirun_bindings())
    except Exception:  # noqa: BLE001 - enrichment; never break the manifest
        pass
    return m


def main(argv: list[str] | None = None) -> int:
    return conn.cli(argv, manifest_prose=urirun.load_manifest(__package__))


if __name__ == "__main__":
    raise SystemExit(main())
