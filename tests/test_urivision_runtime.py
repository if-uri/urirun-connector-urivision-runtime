# Author: Tom Sapletta · Part of the ifURI solution.
"""The runtime:// contract: catalog served, URIs explainable, dispatch guarded (dry-run first)."""
from urirun_connector_urivision_runtime import (
    capabilities_list,
    capability_call,
    capability_explain,
    connector_manifest,
    urirun_bindings,
)


def test_catalog_lists_the_capability_map():
    r = capabilities_list()
    assert r["ok"] and r["format"] == "json" and r["count"] >= 10
    uris = [c["uri_pattern"] for c in r["catalog"]["capabilities"]]
    assert "runtime://{target}/capabilities/query/list" in uris
    assert "input://{target}/keyboard/command/type" in uris


def test_catalog_llm_formats_are_text_or_tools():
    assert "URI Runtime Capability Catalog" in capabilities_list(format="markdown")["catalog"]
    tools = capabilities_list(format="tools")["catalog"]
    assert tools[0]["function"]["name"] == "uri_runtime_call"
    bad = capabilities_list(format="nope")
    assert bad["ok"] is False


def test_explain_resolves_a_uri_to_its_contract():
    r = capability_explain(uri="input://local/keyboard/command/type")
    assert r["ok"] and r["captures"] == {"target": "local"}
    assert r["capability"]["kind"] == "command"
    assert capability_explain(uri="nosuch://x/y")["ok"] is False
    assert capability_explain()["ok"] is False


def test_call_is_dry_run_by_default_and_executes_on_request():
    dry = capability_call(uri="input://local/keyboard/command/type", payload={"text": "hi"})
    assert dry["ok"] and dry["executed"] is False and dry["result"]["dry_run"] is True
    live = capability_call(uri="input://local/keyboard/command/type",
                           payload={"text": "hi"}, execute=True)
    assert live["ok"] and live["executed"] is True and live["result"]["typed"] == "hi"


def test_call_validates_payload_and_never_raises():
    bad = capability_call(uri="input://local/keyboard/command/type", payload={"text": 42})
    assert bad["ok"] is False and "text" in bad["error"]
    assert capability_call(uri="nosuch://x")["ok"] is False
    assert capability_call()["ok"] is False


def test_bindings_and_manifest_expose_the_three_routes():
    text = str(urirun_bindings())
    for route in ("capabilities/query/list", "capability/query/explain", "capability/command/call"):
        assert route in text
    m = connector_manifest()
    assert m.get("id") == "urivision-runtime"
