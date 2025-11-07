# RFC: Activation Beyond Quantum-Resistant Encryption

**Status:** Proposed  
**Version:** 2025-11-07  
**Scope:** PQ/hybrid capability negotiation, activation lifecycle, and operator guardrails

---

## 1. Overview
This RFC defines the lifecycle, governance, and observability expectations for enabling post-quantum (PQ) and hybrid cryptography across Agentic Commerce Protocol (ACP) deployments. The goal is to provide a shared lexicon for capability negotiation and a safe activation runway so marketplaces, wallets, and clearing services can adopt stronger cryptographic suites without disrupting classical peers.

The proposal introduces three core pillars:

- A `crypto_capabilities` manifest that advertises the key encapsulation mechanisms (KEMs), signature algorithms, and hybrid bundles each service supports.
- A staged activation lifecycle—discovery, negotiation, staging, activation, validation, rollback—so operators can roll out PQ/hybrid traffic with explicit checkpoints.
- Telemetry and attestation hooks that surface rollout health, downgrade events, and operator approvals to downstream audit systems.

Normative field definitions for the manifest live in [`spec/crypto-capabilities.md`](../spec/crypto-capabilities.md).

---

## 2. Problem Statement & Goals
Modern ACP deployments run small PQ pilots, yet they lack a standardized way to broadcast readiness, negotiate compatible modes, and capture rollout telemetry. Inconsistent semantics and missing observability make it difficult to coordinate staged activation between independent participants.

**Goals**
1. Provide extensible capability descriptors for PQ and hybrid cryptography across ACP services.
2. Define an activation lifecycle that supports incremental enablement and rapid rollback.
3. Supply implementation-neutral telemetry, attestation, and operator workflows to reduce rollout risk.

**Non-Goals**
- Mandating specific KEM or signature algorithms; profiles remain deployment-defined.
- Replacing the existing TLS 1.3 transport. The manifest augments, not replaces, transport security.
- Shipping automation code; the scope is specification and operational guidance.

---

## 3. Capability Manifest Exchange
Services MUST publish a `crypto_capabilities` object via control-plane APIs, service registries, or embedded manifests. Negotiation proceeds in three stages:

1. **Discovery** – Services publish signed manifests and expose stable URLs for retrieval.
2. **Negotiation** – During session setup peers exchange capability hashes (e.g., SHA-256 over canonical JSON) that reference the published payloads.
3. **Commitment** – Once a mutually supported tuple is selected, endpoints persist the suite binding, attach attestation evidence, and emit activation telemetry.

Implementers MUST validate manifest signatures, schema compliance, and compatibility before activating traffic. Downgrade behavior, attestation requirements, and telemetry channels are codified directly in the manifest. See [`spec/crypto-capabilities.md`](../spec/crypto-capabilities.md) for field definitions and an illustrative JSON example.

---

## 4. Activation Lifecycle
| Phase      | Trigger                                | Responsible Parties                | Outputs                                                    |
| ---------- | -------------------------------------- | ---------------------------------- | ---------------------------------------------------------- |
| Discovery  | Capability payload published           | Service owners, SDK maintainers    | Signed manifest, schema validation evidence                |
| Negotiation| Peer manifests exchanged               | Clients, relays, clearinghouses    | Negotiated suite identifier, compatibility decision        |
| Staging    | Suite deployed in shadow/dual-stack    | Operators, SRE                     | Telemetry gating metrics, attestation snapshot             |
| Activation | Traffic migrated to PQ/hybrid suite    | Operators, change management       | Activation log, key lifetimes, rollback bookmark           |
| Validation | Post-activation health review          | Observability, compliance          | Telemetry dashboard capture, attestation verification      |
| Rollback   | Triggered by error budget breach       | Operators                          | Reversion log, fallback suite confirmation                 |

### 4.1 Safety Guardrails
- **Dual-path readiness:** Maintain classical fallback channels until every partner validates the PQ/hybrid path.
- **Operator approvals:** Require multi-party sign-off (runbook owner, on-call, change manager) before adjusting traffic controls.
- **Attestation binding:** Link negotiated suites to hardware/software attestation checksums to detect downgrade attempts.

---

## 5. Telemetry & Attestation Hooks
| Signal                      | Purpose                               | Recommended Fields                                                    |
| --------------------------- | ------------------------------------- | -------------------------------------------------------------------- |
| `crypto.capability.published` | Verify manifest reachability & schema | `capability_hash`, `suites[]`, `timestamp`, `signer_id`               |
| `crypto.negotiation.attempt`  | Track negotiation success rate        | `session_id`, `peer_id`, `requested_suite`, `result_code`             |
| `crypto.activation.state`     | Observe live activation gates         | `environment`, `suite_id`, `traffic_share`, `operator_approval`       |
| `crypto.attestation.binding`  | Confirm attestation coverage          | `suite_id`, `attestation_type`, `hardware_quote_id`                   |
| `crypto.rollback.executed`    | Audit downgrades and fallbacks        | `suite_id`, `reason_code`, `fallback_suite`, `operator_id`            |

Telemetry MUST be exportable to long-term audit storage and SHOULD integrate with existing metrics/trace pipelines. Attestation evidence retention periods are negotiated per deployment but SHOULD align with the manifest’s `attestation` block.

---

## 6. Operator Workflow Checklist
1. Confirm the manifest is signed, versioned, and published to discovery endpoints.
2. Validate negotiation interoperability with downstream peers using the conformance matrix in [`test/interop/crypto-matrix.txt`](../test/interop/crypto-matrix.txt).
3. Stage PQ/hybrid suites behind feature flags with traffic shadowing and telemetry monitors.
4. Schedule the activation window with on-call operators, change management, and compliance observers.
5. Execute the activation change, capture attestation evidence, and monitor telemetry for twice the typical session duration.
6. Archive the activation report, including activation-state metrics, attestation artifacts, and operator approvals.

---

## 7. Conformance Testing
The interoperability harness exercises negotiation across supported suites, fallback paths, and attestation requirements. Test scenarios enumerated in `test/interop/crypto-matrix.txt` SHOULD run in CI/CD. SDK owners are encouraged to add contract tests that assert capability parsing, validation, and downgrade protection logic.

---

## 8. Open Questions
- Should the manifest encode per-suite rollout percentages or delegate traffic shaping to external systems?
- Do we need a first-class signal for hardware-bound key lifetimes within `crypto_capabilities`?
- How should hybrid signature combinations be represented when classical keys are retained solely for audit trails?

Feedback is requested from security reviewers, spec maintainers, SDK integrators, and operators.
