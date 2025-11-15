# Crypto Capabilities Manifest

This document defines the `crypto_capabilities` payload referenced by the "Activation Beyond Quantum-Resistant Encryption" RFC ([`rfcs/rfc.crypto_activation.md`](../rfcs/rfc.crypto_activation.md)). The manifest provides a structured way for ACP services to declare supported post-quantum (PQ) and hybrid cryptographic suites, fallback behavior, and activation policy metadata.

## Object Definition
The manifest is represented as a JSON object with the following top-level fields:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `version` | string | Yes | Semantic version of the capability schema (`semver`), starting at `1.0.0`. |
| `entity` | object | Yes | Describes the publishing service: `{ id: string, role: enum, environment: enum }`. |
| `suites` | array | Yes | List of supported cryptographic suites (see below). |
| `fallback_policies` | object | Yes | Rules describing downgrade behavior when negotiation fails. |
| `attestation` | object | Optional | Requirements for hardware/software attestation binding. |
| `telemetry` | object | Optional | Identifiers for telemetry channels emitting activation signals. |
| `metadata` | object | Optional | Free-form extension point for deployment-specific annotations. |

### Suite Objects
Each item in `suites` is an object with the following properties:

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `suite_id` | string | Yes | Unique identifier for the suite (e.g., `pq-hybrid-kyber-mlkem768-ed25519`). |
| `kem_algorithms` | array | Yes | Ordered preference of supported KEMs (e.g., `['ML-KEM-768', 'X25519-KYBER768-D00']`). |
| `signature_algorithms` | array | Yes | Ordered preference of supported signature schemes (e.g., `['Dilithium3', 'Ed25519']`). |
| `hash_functions` | array | Optional | Digest algorithms required for this suite (e.g., `['SHA3-512']`). |
| `hybrid_modes` | array | Optional | Enumerates hybridization strategies such as `"kem-combine"`, `"signature-dual"`. |
| `min_protocol` | string | Optional | Lowest ACP protocol version compatible with the suite. |
| `activation_modes` | array | Optional | Supported activation channels (`"shadow"`, `"canary"`, `"full"`). |
| `dependencies` | array | Optional | External prerequisites (e.g., attestation profile IDs, hardware revisions). |

### Fallback Policies
The `fallback_policies` object captures downgrade expectations:

```json
{
  "default_suite": "pq-hybrid-kyber-mlkem768-ed25519",
  "allow_classical": true,
  "downgrade_conditions": [
    {
      "reason": "peer-incompatible",
      "fallback_suite": "classical-tls13",
      "telemetry_event": "crypto.rollback.executed"
    },
    {
      "reason": "attestation-failed",
      "fallback_suite": "blocked",
      "telemetry_event": "crypto.attestation.binding"
    }
  ]
}
```

### Attestation Binding
The optional `attestation` block associates capability activation with hardware or software proofs:

| Field | Type | Description |
| --- | --- | --- |
| `required` | boolean | Whether attestation is mandatory to activate the suite. |
| `profiles` | array | List of acceptable attestation profile identifiers. |
| `evidence_retention_days` | integer | Minimum number of days to retain attestation evidence. |

### Telemetry Channels
Implementers MAY include telemetry routing hints:

| Field | Type | Description |
| --- | --- | --- |
| `pubsub_topic` | string | Topic name for activation events. |
| `metrics_namespace` | string | Metrics namespace / prefix. |
| `audit_log_stream` | string | Audit log stream identifier for compliance storage. |

## Example Manifest
```json
{
  "version": "1.0.0",
  "entity": {
    "id": "payments-clearing-eu",
    "role": "clearinghouse",
    "environment": "production"
  },
  "suites": [
    {
      "suite_id": "pq-hybrid-mlkem768-ed25519",
      "kem_algorithms": ["ML-KEM-768", "X25519-KYBER768-D00"],
      "signature_algorithms": ["Dilithium3", "Ed25519"],
      "hash_functions": ["SHA3-512"],
      "hybrid_modes": ["kem-combine", "signature-dual"],
      "min_protocol": "4.2",
      "activation_modes": ["shadow", "canary", "full"],
      "dependencies": ["attestation-profile-v3", "hsm-fw-9.1"]
    },
    {
      "suite_id": "pq-only-mlkem1024-sphincsplus",
      "kem_algorithms": ["ML-KEM-1024"],
      "signature_algorithms": ["SPHINCS+-SHAKE-256s"],
      "hash_functions": ["SHAKE256"],
      "activation_modes": ["shadow"],
      "dependencies": ["attestation-profile-v4"]
    }
  ],
  "fallback_policies": {
    "default_suite": "pq-hybrid-mlkem768-ed25519",
    "allow_classical": true,
    "downgrade_conditions": [
      {
        "reason": "peer-incompatible",
        "fallback_suite": "classical-tls13",
        "telemetry_event": "crypto.rollback.executed"
      },
      {
        "reason": "attestation-failed",
        "fallback_suite": "blocked",
        "telemetry_event": "crypto.attestation.binding"
      }
    ]
  },
  "attestation": {
    "required": true,
    "profiles": ["attestation-profile-v3", "attestation-profile-v4"],
    "evidence_retention_days": 365
  },
  "telemetry": {
    "pubsub_topic": "acp.crypto.activation",
    "metrics_namespace": "acp.crypto",
    "audit_log_stream": "gcs://acp-crypto-activation"
  },
  "metadata": {
    "contact": "crypto-operations@acp.example",
    "change_ticket": "CRQ-4821"
  }
}
```

## Negotiation Semantics
1. Peers exchange capability hashes (e.g., SHA-256 over canonical JSON) during session setup.
2. Each peer validates the counterpart manifest against the schema and compares suite support.
3. The highest-preference suite shared by both parties is selected, subject to attestation requirements.
4. Activation proceeds only if attestation (when required) succeeds and telemetry channels are reachable.
5. Downgrades MUST emit the referenced telemetry events and record the fallback reason for audit review.

## Versioning & Compatibility
- Schema revisions increment `version`. Minor bumps denote backward-compatible additions; major bumps denote breaking changes.
- Manifests SHOULD be retrievable via stable URLs that embed the schema version.
- Implementations MUST ignore unknown optional fields to preserve forward compatibility.

## Security Considerations
- Capability manifests MUST be integrity-protected (e.g., signed or delivered over mutually authenticated channels).
- Operators SHOULD monitor for downgrade attempts by correlating negotiation outcomes with attestation signals.
- Consider limiting manifest lifetime (e.g., TTLs) to reduce replay risk of stale capability declarations.
