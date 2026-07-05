# urirun-connector-urivision-runtime

Native `runtime://` URI surface over [urivision](https://github.com/if-uri/urivision)'s
`CapabilityRegistry` — the URI-addressed **contract map** of the perception/action stack
(`ui://`, `input://`, `view://`, `browser://`, `vision://`, `guard://` …).

urivision's registry is deliberately mock-backed: it owns the *contracts* (schemas,
preconditions, safety tags), while real execution lives in urirun connectors
(kvm / vql / vdisplay). This connector serves the missing piece to the mesh — the
**catalog** — without duplicating any implementation.

## Routes

| Route | What it does |
| --- | --- |
| `runtime://{node}/capabilities/query/list` | Full capability catalog. `format`: `json`, `markdown`, `prompt` (LLM cards), `tools` (OpenAI-style). |
| `runtime://{node}/capability/query/explain` | Resolve one URI → matching capability, captures, expected payload schema. |
| `runtime://{node}/capability/command/call` | Dispatch through the registry. **Dry-run by default** (validate + show what would run); `execute=true` invokes the mock-backed handler. |

## Install

```bash
pip install -e .
# serve it (installed connectors are NOT auto-served):
urirun node serve --name host --allow 'runtime://**'
```

Part of the ifURI solution · Author: Tom Sapletta · Apache-2.0
