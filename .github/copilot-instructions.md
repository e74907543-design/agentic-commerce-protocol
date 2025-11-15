# AI Agent Instructions for Agentic Commerce Protocol

## Project Overview

The **Agentic Commerce Protocol (ACP)** is an open standard (maintained by OpenAI & Stripe) defining how AI agents interact with merchant commerce systems. The repo contains:

- **RFCs** (`rfcs/`): Human-readable design docs (status, scope, message flows, rationale)
- **OpenAPI specs** (`spec/openapi/`): HTTP API contracts for integrations
- **JSON Schemas** (`spec/json-schema/`): Data models and payload validation
- **Examples** (`examples/`): Real request/response samples
- **Changelog** (`changelog/`): Version history and breaking changes

This is a **specification repo**, not a runtime service. Changes affect how merchants and agents implement commerce interactions.

---

## Architecture & Key Concepts

### Protocol Layers

ACP is multi-layered; understand each before making spec changes:

1. **Agentic Checkout** (`rfc.agentic_checkout.md`, `openapi.agentic_checkout.yaml`)

   - REST API merchants implement for session lifecycle (create → update → retrieve → complete → cancel)
   - Agent (ChatGPT) calls merchant endpoints; merchant remains system of record
   - Idempotency via `Idempotency-Key`; request signing via `Signature` + `Timestamp`

2. **Delegate Payment** (`rfc.delegate_payment.md`)

   - Optional flow for agents to collect payment tokens and delegate to PSP
   - Complements checkout; merchant can choose to use delegated or keep on own rails

3. **Argus C2** (`rfc.argus_c2.md`) — **Newest / Research Phase**
   - Real-time pub/sub command-and-control bus (WebSocket or HTTPS/2 push)
   - Channels: `commands.<workflow>`, `events.<workflow>`, `alerts.<workflow>`, `audit.<workflow>`
   - Enables low-latency state sync and escalation beyond REST polling

**Why the layering?** Each protocol is optional; merchants can implement only what they need. Argus C2 is RECOMMENDED but not required.

### Request Signing & Versioning

- All requests carry `API-Version: 2025-09-29` (or current) — **MUST validate version support**
- Optional request signing: `Signature: <base64url>` over canonical JSON + `Timestamp`
- Error shape is flat: `{type, code, message, param}` where `param` uses RFC 9535 JSONPath

---

## Development Workflow

### Building & Validation

```bash
# Compile and validate all JSON Schemas (AJV)
pnpm install
pnpm run compile:schema

# CI runs on: push to main, all PRs
# See: .github/workflows/main.yml
```

**What CI validates:**

- JSON Schema compilation against draft2020 spec
- No syntax errors in YAML OpenAPI files (via linting in PR checks)

### Change Requirements

**Every PR must include** (per `CONTRIBUTING.md`):

1. **OpenAPI + JSON Schema updates** — If spec behavior or payloads change:

   - Update `spec/openapi/openapi.*.yaml`
   - Update `spec/json-schema/schema.*.json`
   - Run `pnpm run compile:schema` locally before pushing

2. **Examples** — Add/update `examples/examples.*.json` with real request/response pairs

   - Keep examples in sync with schema changes
   - Include multiple scenarios (e.g., minimal vs. with-address)

3. **Changelog entry** — Add to `changelog/unreleased.md`:

   - Describe what changed (breaking vs. non-breaking)
   - Reference the RFC or feature name

4. **RFC updates** — If behavior/semantics change, update relevant RFC in `rfcs/`:
   - Increment version and status (Draft → Stable, if releasing)
   - Update examples, message flows, error cases

### Version Strategy

- **Semantic versioning not used**; instead versions are **dates**: `2025-09-29`
- Breaking changes → new version number
- Non-breaking additions → same version (document in unreleased changelog)
- Major spec changes require lead maintainer approval (OpenAI or Stripe)

---

## Spec Authoring Patterns

### Normative Language

Use RFC 2119/8174 keywords in all specs:

- **MUST** — Mandatory requirement (implementation MUST do this)
- **MUST NOT** — Forbidden
- **SHOULD** — Recommended (implementation SHOULD do this unless strong reason not to)
- **MAY** — Optional
- Avoid "should" (lowercase) in specs; use SHOULD or MUST

Example from `rfc.agentic_checkout.md`:

> "Server **MUST** validate support (e.g., `2025-09-29`)" — clear, verifiable requirement

### OpenAPI Structure

- Use `components/schemas` for reusable data models
- Use `components/parameters` for shared request headers (e.g., `Authorization`, `API-Version`)
- Each operation includes `operationId`, clear `description`, and examples for common scenarios
- Error responses reference shared `Error` schema

Example from `openapi.agentic_checkout.yaml`:

```yaml
paths:
  /checkout_sessions:
    post:
      summary: Create a checkout session
      parameters:
        - $ref: "#/components/parameters/APIVersion"
        - $ref: "#/components/parameters/Signature"
      requestBody:
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CheckoutSessionCreateRequest"
            examples:
              minimal: ...
              with_address: ...
```

### JSON Schema Constraints

- Validate with AJV: `ajv compile --spec=draft2020 -c ajv-formats -s spec/json-schema/**/*.json`
- Use `$defs` for reusable schemas (e.g., `Address`, `Money`)
- Required fields go in `required: [...]` array
- Document field constraints in `description` (e.g., "MUST be 2-letter ISO code")

### RFC Structure (from existing RFCs)

1. **Header** — Status (Draft/Stable), Version, Scope
2. **Objectives & Principles** — Why this protocol exists, normative language definition
3. **Topology & Roles** — Who talks to whom
4. **Message Contract** — Payload structure with constraints
5. **Channels/Endpoints** — Each operation with request/response shape
6. **Examples** — Real flows (happy path + error scenarios)
7. **Security** — Auth, signing, encryption, rate limits
8. **Rollout Plan** — Phase-in timeline for deprecations

---

## Common Tasks

### Adding a New Endpoint

1. **RFC**: Add section describing the endpoint's purpose, request/response, error cases, examples
2. **OpenAPI**: Add operation under appropriate path with `operationId`, `summary`, parameter refs, request/response schemas
3. **JSON Schema**: Define request and response schemas with constraints and `description`
4. **Examples**: Add request/response pair in `examples/examples.*.json`
5. **Changelog**: "Added `POST /checkout_sessions/{id}/new-action` endpoint"
6. **Validation**: Run `pnpm run compile:schema` — must pass with no errors

### Modifying a Payload Field

1. **JSON Schema**: Edit field in `schema.*.json` (add `description`, change `type`, add `examples`)
2. **OpenAPI**: Mirror the change in the operation's requestBody/response schema
3. **Examples**: Update all relevant examples to match new structure
4. **RFC**: Update message contract section with rationale if semantics changed
5. **Changelog**: "Modified `field_name` to `type` (was: `old_type`) — breaking change"

### Deprecating a Field

1. **RFC**: Document deprecation timeline and replacement (e.g., "Deprecated in version X; use `new_field` instead")
2. **JSON Schema**: Mark field optional if not already; add `deprecated: true` and `description: "Deprecated since version X; use new_field"`
3. **Examples**: Show old field with note; add new field examples
4. **Changelog**: "Deprecated `old_field`; migrate to `new_field` by [date]"

---

## Debugging & Validation Checklist

When reviewing spec PRs, verify:

- [ ] Normative language (MUST/SHOULD/MAY) is consistent and precise
- [ ] OpenAPI examples compile and match JSON Schema
- [ ] `pnpm run compile:schema` passes with zero errors
- [ ] Idempotency and versioning semantics are preserved (if checkout-related)
- [ ] All error types used in examples are defined in Error schema
- [ ] Changelog entry explains breaking vs. non-breaking change
- [ ] RFC section headers match OpenAPI operation grouping (tags)
- [ ] Request/response examples in RFC match examples/\*.json

---

## Key Files Reference

| File                                            | Purpose                                                       |
| ----------------------------------------------- | ------------------------------------------------------------- |
| `rfcs/rfc.agentic_checkout.md`                  | Checkout REST API contract (session lifecycle)                |
| `rfcs/rfc.delegate_payment.md`                  | Delegated payment flow (optional PSP delegation)              |
| `rfcs/rfc.argus_c2.md`                          | Real-time C2 bus for command/event/audit channels             |
| `spec/openapi/openapi.agentic_checkout.yaml`    | Merchant REST endpoints (machine-readable)                    |
| `spec/json-schema/schema.agentic_checkout.json` | Payload validation schemas (CheckoutSession, etc.)            |
| `examples/examples.agentic_checkout.json`       | Real request/response samples for checkout                    |
| `changelog/unreleased.md`                       | Pending version changes (merged to versioned file on release) |
| `CONTRIBUTING.md`                               | PR requirements, branching, spec review process               |
| `.github/workflows/main.yml`                    | CI: schema compilation validation                             |

---

## Notes for AI Agents

- **Not a runtime repo**: Focus on spec correctness, not feature implementation
- **Schema-first approach**: Changes propagate: RFC → OpenAPI → JSON Schema → Examples → Changelog
- **Maintenance governance**: OpenAI & Stripe are lead maintainers; major changes require their approval
- **Backward compatibility**: Document breaking changes clearly; use version numbers (dates) to signal compatibility
- **Security-first specs**: Request signing, idempotency keys, and versioning are non-negotiable for checkout & payments
