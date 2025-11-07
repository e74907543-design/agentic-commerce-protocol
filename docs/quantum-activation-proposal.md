# RFC: Activation Beyond Quantum-Resistant Encryption

## Executive Summary
This proposal introduces an activation and governance lifecycle for enabling post-quantum (PQ) and hybrid cryptography across Agentic Commerce Protocol (ACP) deployments. The intent is to provide a shared lexicon, telemetry expectations, and operator guidance so platforms can safely negotiate and progressively enable stronger cryptographic suites without disrupting existing classical endpoints.

* Establishes the `crypto_capabilities` declaration for services to advertise supported key encapsulation mechanisms (KEMs), signature schemes, and hybrid bundles.
* Defines an activation lifecycle with discovery, negotiation, staging, activation, validation, and rollback checkpoints.
* Recommends telemetry events, attestation hooks, and operator runbooks to monitor adoption while preserving backward compatibility.

## Background & Motivation
Modern ACP deployments already support lattice-based PQ algorithms in isolated pilots, but lack a standardized way to signal readiness, negotiate compatible modes, and capture rollout telemetry. As operators ramp PQ adoption, inconsistent semantics and missing observability make it difficult to coordinate staged activation between marketplaces, wallets, and clearing services. A unified proposal is required so SDK maintainers, integrators, and operators can collaborate on an incremental path to hybrid and PQ-only traffic.

## Goals
1. Codify extensible capability descriptors for PQ and hybrid cryptography across ACP services.
2. Provide an activation lifecycle that allows gradual enablement with rollback guardrails.
3. Supply implementation-neutral telemetry, attestation, and operator workflows to reduce rollout risk.

## Non-Goals
- Mandating specific KEM or signature algorithms; profiles remain deployment-defined.
- Replacing existing TLS 1.3 handshakes; this proposal layers on top of the current transport security model.
- Delivering production automation scripts; the scope is a specification and operational guidance.

## Capability Model Overview
Services surface a `crypto_capabilities` object that enumerates supported suites, fallback behavior, and validation requirements. Negotiation proceeds when both peers confirm compatible profiles:

1. **Discovery** – Services publish capability metadata via control-plane APIs, service registries, or embedded manifests.
2. **Negotiation** – During session establishment, peers exchange capability hashes referencing the published payload.
3. **Commitment** – Once a stable tuple is selected, endpoints persist the negotiated bundle, bind it to session attestation, and emit activation telemetry.

See [`spec/crypto-capabilities.md`](../spec/crypto-capabilities.md) for normative field definitions and payload examples.

## Activation Lifecycle
| Phase | Trigger | Responsible Parties | Outputs |
| --- | --- | --- | --- |
| Discovery | Capability payload published | Service owners, SDK maintainers | Signed capability manifest, schema validation evidence |
| Negotiation | Peer capabilities exchanged | Clients, relays, clearinghouses | Negotiated suite identifier, compatibility decision |
| Staging | Suite deployed in shadow/dual-stack | Operators, SRE | Telemetry gating metrics, attestation snapshot |
| Activation | Traffic migrated to PQ/hybrid suite | Operators, change management | Activation event log, key lifetimes, rollback bookmark |
| Validation | Post-activation health review | Observability, compliance | Telemetry dashboard capture, attestation verification |
| Rollback | Triggered by error budget breach or incompatibility | Operators | Reversion log, fallback suite confirmation |

### Safety Guardrails
- **Dual-path readiness**: Maintain classical fallback channels until activation success is demonstrated for the full partner graph.
- **Operator approval workflow**: Require multi-party sign-off before flipping traffic control knobs.
- **Attestation binding**: Link negotiated suites to hardware/software attestation checksums to catch downgrade attempts.

## Telemetry & Attestation Hooks
| Signal | Purpose | Recommended Fields |
| --- | --- | --- |
| `crypto.capability.published` | Verify manifest reachability and schema compliance | capability_hash, suites[], timestamp, signer_id |
| `crypto.negotiation.attempt` | Track negotiation success rate | session_id, peer_id, requested_suite, result_code |
| `crypto.activation.state` | Observe live activation gates | environment, suite_id, traffic_share, operator_approval |
| `crypto.attestation.binding` | Confirm attestation check coverage | suite_id, attestation_type, hardware_quote_id |
| `crypto.rollback.executed` | Audit rollbacks and fallbacks | suite_id, reason_code, fallback_suite, operator_id |

Telemetry MUST be exportable to long-term audit storage and joined with change management systems. Implementers SHOULD integrate these hooks with existing metrics/trace pipelines rather than invent new transports.

## Operator Workflow Checklist
1. Confirm `crypto_capabilities` manifest is signed, versioned, and published to discovery endpoints.
2. Validate negotiation interoperability with all downstream peers via the conformance matrix (see [`test/interop/crypto-matrix.txt`](../test/interop/crypto-matrix.txt)).
3. Stage PQ/hybrid suites behind feature flags with traffic shadowing and telemetry monitors.
4. Schedule activation window with operator on-call, change manager, and compliance observers.
5. Execute activation change, capture attestation binding evidence, and monitor telemetry for at least 2x the typical session duration.
6. Archive activation report including activation state metrics, attestation artifacts, and operator approvals.

## Integration & Conformance Testing Plan
The interoperability harness exercises negotiation across supported suites, fallback paths, and attestation requirements. Test scenarios are enumerated in `test/interop/crypto-matrix.txt` and SHOULD be automated in CI/CD environments. SDK owners are encouraged to add contract tests that assert capability parsing, validation, and downgrade protection logic.

## Open Questions
- Should the capability manifest support per-suite rollout percentages or rely on external traffic shaping controls?
- Do we need a first-class signal for hardware-bound key lifetimes within `crypto_capabilities`?
- How should we represent hybrid signature combinations where classical keys are retained solely for auditing purposes?

Feedback is requested from security reviewers, spec maintainers, SDK integrators, and operational teams.
