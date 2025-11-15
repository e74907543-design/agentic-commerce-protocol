# RFC: Creation Codex — Mass Generation Protocol

**Status:** Draft  
**Version:** 2025-03-01  
**Scope:** Standardized interface for orchestrating large batch content generation safely across agentic commerce surfaces.

The **Creation Codex** defines a **Mass Generation Protocol (MGP)** that lets buyer agents request, audit, and fulfill large numbers of creative artifacts (e.g., marketing blurbs, catalog descriptions, product media) from merchant-controlled generation services. It focuses on **traceability, policy enforcement, and throughput** when hundreds or thousands of assets must be produced in a single session.

---

## 1. Problem Statement & Goals

### 1.1 Challenges

- **Unbounded fan-out.** Merchants frequently need thousands of SKUs localized or personalized. Ad-hoc API calls make it hard to coordinate throttling, retries, and billing.
- **Policy drift.** Generated assets must comply with both merchant policy and platform safety rules. Without explicit auditing hooks, agents cannot confidently deliver the content to buyers.
- **Attribution gaps.** Downstream payment or licensing flows require proof of which prompts, models, and human reviewers touched each artifact.

### 1.2 Goals

1. Provide a **stateful session layer** that batches many generation tasks while preserving idempotency.
2. Offer **structured audit trails** that bind prompts, models, reviewers, and delivery targets into a single record.
3. Support **parallel execution** hints so agents can distribute work across multiple model providers without violating quotas.
4. Enable **policy guardrails** where platforms can inject validation callbacks before artifacts leave the merchant boundary.

### 1.3 Non-Goals

- Selecting specific foundation models.
- Governing intellectual property licenses—merchants remain responsible for downstream agreements.
- Defining rendering formats beyond JSON payloads referenced via URIs.

---

## 2. Actors & Concepts

| Actor / Object | Description |
| -------------- | ----------- |
| **Generation Client** | The agent (e.g., ChatGPT) orchestrating the mass request on behalf of a buyer or operator. |
| **Generation Server** | Merchant- or partner-hosted service implementing this protocol. |
| **Batch Session** | Top-level container describing objectives, policy packs, and throughput caps. |
| **Task** | Individual asset request (prompt, locale, target SKU). |
| **Artifact** | Output payload (text, image, audio, etc.) along with provenance metadata. |
| **Policy Pack** | Declarative rules referencing merchant / platform compliance requirements. |

---

## 3. Protocol Overview

```
Client ──POST /generation_sessions──────────────▶ Server
      ◀──201 + session──────────────
Client ──POST /generation_sessions/{id}/tasks──▶ Server
      ◀──202 accepted────────────────
Server ──emit `artifact.ready` webhooks──────▶ Platform / Client
Client ──GET /generation_sessions/{id}────────▶ Server
```

Key primitives:

1. **Session Creation.** Defines quotas, policy packs, reviewer requirements, and expected completion deadline.
2. **Task Submission.** Each task references the session, declares prompt templates, structured variables, and optional dependencies.
3. **Artifact Delivery.** Server pushes artifact metadata to the client via webhook (recommended) or pull via polling.
4. **Finalization.** Client marks session `accepted`, `needs_changes`, or `canceled`, enabling billing and retention policies.

---

## 4. HTTP Interface

### 4.1 Common Headers

- `API-Version: 2025-03-01` (REQUIRED)
- `Authorization: Bearer <token>` (REQUIRED)
- `Idempotency-Key` (REQUIRED on POST)
- `Signature` / `Timestamp` (RECOMMENDED for HMAC/ECDSA signatures)
- `Codex-Policy-Pack: <opaque-id>` (OPTIONAL shortcut when a default pack is negotiated out-of-band)

All responses MUST be JSON encoded with UTF-8 and use standard ACP error shapes.

### 4.2 `POST /generation_sessions`

Creates a new batch session.

```json
{
  "objective": "Localize spring catalog copy",
  "policy_pack_id": "pp_2025_localized",
  "max_tasks": 5000,
  "throughput": {
    "max_parallel_tasks": 200,
    "rate_per_minute": 600
  },
  "review": {
    "requires_human": true,
    "sla_minutes": 60
  },
  "metadata": {
    "campaign_id": "cmp_987"
  }
}
```

Response:

```json
{
  "id": "gsn_123",
  "status": "accepting_tasks",
  "policy_pack_id": "pp_2025_localized",
  "quotas": {
    "max_tasks": 5000,
    "submitted": 0,
    "completed": 0
  },
  "webhook": {
    "artifact_ready": "https://client.example/webhooks/artifacts"
  }
}
```

Servers MUST transition the session to `closed` when `max_tasks` is met or the session is explicitly finalized.

### 4.3 `POST /generation_sessions/{id}/tasks`

Adds tasks to the session. Body (array up to 100 per call):

```json
[
  {
    "task_id": "task_sku123_en",
    "prompt_template": "Write a playful description for {{sku_name}} in {{locale}}",
    "variables": {
      "sku_name": "Cloudweave Hoodie",
      "locale": "en-GB"
    },
    "channels": ["product_page", "email"],
    "guardrails": {
      "max_tokens": 180,
      "temperature": 0.6
    }
  }
]
```

Response:

```json
{
  "accepted": ["task_sku123_en"],
  "rejected": []
}
```

Servers MUST return `409 conflict` when submitting a duplicate `task_id` unless the payload is byte-identical (idempotent retry).

### 4.4 `GET /generation_sessions/{id}`

Returns aggregate state and summaries:

```json
{
  "id": "gsn_123",
  "status": "producing",
  "counts": {
    "pending": 840,
    "in_progress": 120,
    "completed": 4040,
    "failed": 0
  },
  "next_webhook_retry_at": null,
  "last_error": null
}
```

### 4.5 Webhook `artifact.ready`

Payload:

```json
{
  "event": "artifact.ready",
  "session_id": "gsn_123",
  "task_id": "task_sku123_en",
  "artifact": {
    "type": "text",
    "uri": "https://cdn.example/gsn_123/task_sku123_en.txt",
    "hash": "sha256:...",
    "bytes": 2048
  },
  "provenance": {
    "model": "gpt-5.1-large",
    "prompt": {
      "template": "Write a playful description for {{sku_name}} in {{locale}}",
      "rendered": "Write a playful description for Cloudweave Hoodie in en-GB"
    },
    "moderation": {
      "policy_pack_id": "pp_2025_localized",
      "result": "pass"
    },
    "reviewers": [
      { "id": "user_abc", "timestamp": "2025-03-01T08:42:00Z" }
    ]
  }
}
```

Clients MUST respond with `2xx` within 5 seconds. Otherwise the server MUST retry with exponential backoff for at least 24 hours.

---

## 5. State Machine

```
accepting_tasks → producing → awaiting_approval → (accepted | needs_changes | canceled)
```

- `accepting_tasks`: Created, under quota.
- `producing`: All tasks submitted; server now focused on fulfillment.
- `awaiting_approval`: Server delivered all artifacts and awaits final confirmation from the client.
- `accepted`: Client acknowledges delivery; retention clock starts (server MAY purge after `retention_days`).
- `needs_changes`: Client requests modifications; server MAY reopen or spawn follow-up sessions referencing the prior session ID.
- `canceled`: Client or server terminates early. All in-progress tasks MUST halt.

---

## 6. Policy Packs

Policy packs are JSON documents stored by the server and referenced via `policy_pack_id`. Each pack contains:

```json
{
  "id": "pp_2025_localized",
  "version": "2025-02-10",
  "rules": [
    { "type": "forbidden_terms", "values": ["clearance", "fire sale"] },
    { "type": "style_guide", "path": "https://cdn.example/style_guides/2025.pdf" }
  ],
  "moderation_hooks": [
    {
      "name": "platform_safety",
      "endpoint": "https://platform.example/hooks/moderate",
      "timeout_ms": 2500,
      "retries": 2
    }
  ]
}
```

Servers MUST version packs immutably; clients SHOULD pin a specific version during certification.

---

## 7. Security & Compliance

- **Authentication:** OAuth2 client credentials or mutually authenticated TLS certificates. Rotating credentials MUST be supported.
- **Integrity:** All artifacts SHOULD include content hashes; CDN objects MUST be served over HTTPS with signed URLs.
- **Privacy:** Personal data appearing in prompts MUST be scoped to the campaign and redacted from logs when `retain_personal_data=false` on the session.
- **Audit:** Servers MUST be able to export a `session_audit` bundle containing prompts, rendered inputs, model selection, reviewer actions, and timestamps for at least 90 days.

---

## 8. Operational Considerations

| Concern | Recommendation |
| ------- | -------------- |
| **Throughput** | Support per-session backpressure (HTTP 429 with `Retry-After`) when clients exceed `rate_per_minute`. |
| **Versioning** | Breaking changes MUST bump `API-Version`. Clients SHOULD include `Accept-Version` negotiation headers during beta. |
| **Monitoring** | Emit metrics per session (`tasks.completed`, `webhook.failures`) and expose health probes for readiness/liveness. |
| **Billing** | Billable units MAY be task-based, token-based, or reviewer-minutes but MUST be reported in the `session_audit`. |

---

## 9. Certification Checklist

1. ✅ Session creation enforces max quotas and idempotency.
2. ✅ Duplicate `task_id` submissions are rejected unless identical.
3. ✅ Webhook retry policy proven via chaos testing (disconnects, HTTP 500).
4. ✅ Policy pack validation ensures every artifact references a `moderation` result.
5. ✅ Audit export demonstrated for random sample sessions.

---

## 10. Future Work

- **Streaming artifacts** using SSE for near-real-time previews.
- **Dependency graphs** so later tasks can depend on artifacts from earlier tasks.
- **On-device guardrails** for privacy-sensitive industries where prompts cannot leave the merchant VPC.

