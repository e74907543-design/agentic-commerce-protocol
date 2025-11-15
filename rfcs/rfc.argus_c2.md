# RFC: Argus C2 Protocol — Agent Command & Control Bus

**Status:** Draft
**Version:** 2025-11-15
**Scope:** Secure command-and-control channel between agent surfaces, merchant services, and payment providers

The **Argus Command & Control (C2) Protocol** defines a real-time messaging fabric that coordinates long-running commerce tasks
across heterogeneous services. It introduces a publish/subscribe control plane that complements existing REST APIs by enabling
low-latency state synchronization, escalation handling, and delegated automation.

Argus C2 is optional but **RECOMMENDED** for merchants and platforms that operate multiple automations simultaneously or need to
share authoritative status updates beyond what the checkout APIs provide.

---

## 1. Objectives & Principles

- Provide a **low-latency** (< 500 ms end-to-end) channel for lifecycle events that supplements polling-based integrations.
- Guarantee **strong ordering** within each workflow via sequence numbers and acknowledgements.
- Allow **auditable replay** through durable event logs.
- Maintain **protocol neutrality** by supporting JSON payloads and optional binary attachments.
- Preserve **merchant control**: merchants remain system of record for order, fulfillment, and compliance data.

### 1.1 Normative Language

Key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** follow RFC 2119/8174.

---

## 2. Topology & Roles

Argus C2 defines three logical roles:

1. **Command Originator** — Typically an AI agent. Issues intents such as `create_checkout`, `apply_offer`, `cancel_order`.
2. **Merchant Coordinator** — Merchant middleware that validates commands, enforces policy, and enriches domain data.
3. **Payment Orchestrator** — Optional PSP or delegated payment service that consumes payment tokens and provides status.

Each role connects to a shared message broker using mutually authenticated WebSockets (or HTTPS/2 with server push). Messages are
delivered over logical **channels**:

| Channel                 | Direction                | Purpose                                                |
| ----------------------- | ------------------------ | ------------------------------------------------------ |
| `commands.<workflow>`   | Originator → Coordinator | Issue intents and control actions.                     |
| `events.<workflow>`     | Coordinator → Originator | Publish authoritative state snapshots.                 |
| `alerts.<workflow>`     | Any → Any                | Escalations, SLA violations, human takeover signals.   |
| `audit.<workflow>`      | Coordinator → Broker     | Immutable ledger for regulatory replay.                |

Workflows are scoped via UUIDs (e.g., `workflow: checkout_session_id`). A single workflow corresponds to a checkout session or
post-purchase flow.

---

## 3. Message Contract

All messages share a common envelope:

```json
{
  "id": "msg_123",
  "workflow_id": "wfl_abc",
  "channel": "commands.checkout",
  "sequence": 15,
  "timestamp": "2025-11-15T18:03:55Z",
  "type": "command.create_checkout",
  "payload": { "checkout_session_id": "cs_123", "line_items": [] },
  "attachments": [
    {
      "id": "att_789",
      "type": "application/pkcs7-signature",
      "integrity": {
        "hash": "sha256:57e3...",
        "length": 2048
      },
      "expires_at": "2025-11-15T18:33:55Z",
      "url": "https://example.com/attachments/att_789"
    }
  ]
}
```

### 3.1 Constraints

- `sequence` **MUST** increase monotonically for each (`workflow_id`, `channel`) tuple. Gaps signal message loss.
- Receivers **MUST** respond with an acknowledgement containing the highest contiguous sequence seen.
- `timestamp` **MUST** be RFC 3339 with UTC.
- `type` **MUST** be a dot-delimited taxonomy (`command.*`, `event.*`, `alert.*`).
- `payload` **MUST** validate against the Argus JSON Schemas defined per message type (to be published separately).
- `attachments[]` **MAY** be omitted when not required.

### 3.2 Error Handling

Receivers respond on `events.<workflow>` with an error envelope when validation fails:

```json
{
  "id": "msg_124",
  "workflow_id": "wfl_abc",
  "channel": "events.checkout",
  "sequence": 16,
  "type": "event.command_rejected",
  "payload": {
    "ref": "msg_123",
    "reason": "invalid_request",
    "details": "line_items[0].quantity must be >= 1"
  }
}
```

Error responses **MUST** reference the offending message ID via `payload.ref` and **SHOULD** include a machine-readable `reason`.

---

## 4. Reliability & Delivery Semantics

- Brokers **MUST** implement **exactly-once** delivery semantics per connection using acknowledgement offsets.
- Clients **MUST** persist the highest acknowledged sequence and **MUST** resume using the `Resume-Token` header when reconnecting.
- Originators **SHOULD** implement exponential backoff when publishing fails.
- Coordinators **MUST** support **idempotent** command handling using `id` and `workflow_id` as deduplication keys.

### 4.1 Heartbeats

- Each side **MUST** send `event.heartbeat` every 30 seconds with `status: ok`.
- Missing heartbeats for 90 seconds **MUST** transition the connection state to `degraded` and trigger an alert.

---

## 5. Security & Compliance

- Connections **MUST** use TLS 1.3 with mutual authentication (mTLS). Certificates **MUST** be rotated at least every 90 days.
- Messages **MUST** include a detached signature attachment (`type: application/pkcs7-signature`) covering the canonicalized
  envelope.
- Brokers **MUST NOT** retain payloads longer than the configured data residency policy (default 30 days).
- Coordinators **MUST** redact PCI/PII fields before publishing to `alerts`.
- Audit channels **MUST** be WORM (write-once, read-many) storage with tamper-evident hashing.

---

## 6. Integration with ACP

Argus C2 complements existing ACP components:

- Checkout lifecycle events (`event.checkout.updated`) **SHOULD** mirror the REST `GET /checkout_sessions/{id}` payload.
- Delegated payment flows **SHOULD** propagate `event.payment.status_changed` messages prior to webhook delivery.
- Merchants **MAY** drive human handoff by publishing `alert.checkout.handoff` with `target: "human"`.
- AI agents **SHOULD** subscribe to `events` and `alerts` to present real-time status within the conversation.

---

## 7. Certification Checklist

A platform claiming Argus C2 compatibility **MUST** satisfy the following:

1. **Connectivity** — Demonstrate mutual TLS handshake with broker, including certificate rotation procedure.
2. **Ordering Guarantees** — Provide proof (logs) of sequence enforcement and duplicate suppression.
3. **Failure Recovery** — Simulate broker disconnect and show resume from `Resume-Token` without message loss.
4. **Security Controls** — Provide signing keys management policy and audit storage verification.
5. **Interoperability** — Execute reference workflow using ACP checkout API with Argus C2 events mirroring state transitions.

Upon certification, implementers **SHOULD** publish their capability descriptor in `/.well-known/argus-c2.json` detailing broker
endpoints, supported message types, and contact information.

---

## 8. Future Work

- Define canonical JSON Schemas for core message types and integrate them into the `spec/json-schema` directory.
- Publish reference broker configuration (Kafka, NATS JetStream) with recommended retention and encryption defaults.
- Expand interoperability tests covering delegated payments, subscription renewals, and dispute workflows.

