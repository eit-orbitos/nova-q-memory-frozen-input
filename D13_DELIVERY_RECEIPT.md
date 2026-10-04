# D13 V0.1 — exact candidate source delivery

Artifact: `EIT_13D_AUTONOMOUS_EVOLUTIONARY_VECTOR_V0.1`

## Current byte checks

- Original archived ZIP hash matched before archive inspection.
- Exactly 12 source entries; no cache, bytecode, build, or dist entries.
- All 12 extracted sources match the archived inventory hashes and sizes.
- All 12 also match the stored source directory byte-for-byte.
- Saved release-report and inventory-file hashes match their detached hash record.
- SOURCE_INVENTORY_SHA256 recomputed using the original canonical JSON recipe.
- No source rewritten, renamed, regenerated, or reconstructed. No tests rerun in this delivery.

## Final per-file SHA256 table

| File | Bytes | SHA256 |
|---|---:|---|
| d13_semantic_contract.py | 8729 | `1648532afc072354393bdf6ac42153e4b9b028208093883402890ca0a204c763` |
| information_fluid_state.py | 5709 | `0a266f2d9a015999adc628da67812e62b422c69483444d16c04e33a7fc3873a6` |
| novelty_operator.py | 5472 | `82388be0570144339165eb3a83d4e0365a19dd8fa7d46a9d69c0f37847d14ef3` |
| validation_operator.py | 3524 | `35cf98db7128071bbaa88107d1c632a932b874aff94dbc8c178e293e804b043a` |
| autonomy_gate.py | 3560 | `8ece90c6d61f0caccfc5ddd0b31f248002cc835624ae88932b56419e470a04ed` |
| provenance_graph.py | 5015 | `a103487a1580f6f81a3ab3c9ce045326d691d1644caa6536aba67c6c9dfb9bd8` |
| falsification_gate.py | 4177 | `891bb6e965ecb47a453e49d186537e718727b44dc24e29887c50d639d39809d7` |
| aev_frequency.py | 8664 | `d72afe897c1ccc2837011fc262a88bef00639d4fdd134b7696167df5e4383ce0` |
| counterexample_families.py | 13975 | `937aafefbc807b2ae4b1c59b14ea644d7532e2343d4c72ebdcdfdfe0753b47c2` |
| audit.py | 11709 | `465c3624572607643494f42b3a7ede03456af4ad765147cf4f0fd78d2a5159ea` |
| manifest.py | 7373 | `b986a9b0f26dec9e2df9298e5a521ac1b999bffff78cb4f9296bcbca5ce44686` |
| test_d13_full.py | 7825 | `7b5e82b390df4c865f4908d44246f6a20bd0991b67a20d5168024b2a98f188b1` |

## Release identities

- CONTENT_MANIFEST_SHA256: `bf338d58625aa9c187928013a8bd83fa4b061da1e4deddf1ecb22e849d6176da` (recorded in hash-checked original release report; not recomputed in this delivery)
- SOURCE_TREE_MANIFEST_SHA256: `b9e3a1eab4dc0b666392241930e04868a5179c28368a94e157ad3f4edfa2cef3` (recorded in hash-checked original release report; not recomputed in this delivery)
- ZIP_SHA256: `0087fde8ef599bed5ef8c2367954ba1967a2988fd0b578805c8dff9c9404f7b8` (recomputed from original ZIP bytes)
- SOURCE_INVENTORY_SHA256: `8e75f5b3cf01f4911a8b6ae49ee537d57a6bfd403a773ba87333630082b561c6` (recomputed; not the hash of the newline-terminated inventory file)

## Prior Tasklet-local execution record

Confirmed as recorded in the saved release-build report, not as a new execution:
- audit: 28/28 PASS
- full suite: 20/20 PASS
- extracted build 1: 20/20 PASS
- extracted build 2: 20/20 PASS
- second rebuild byte-identical: true
- Scope: two clean temporary directories in the same Tasklet sandbox; not independent-environment reproduction.

## Retained status

```text
D13_STATUS = EXTENSION_CANDIDATE
D_INT_CONTRIBUTION = UNRESOLVED
PROMOTION_STATUS = NOT_YET_PROMOTED
PHYSICAL_HZ_CLAIM = PROHIBITED
AI_CONSCIOUSNESS_CLAIM = NOT_ESTABLISHED
SCIENTIFIC_TRUTH = NOT_ESTABLISHED
```

## AIAssessmentReceipt

- Reviewer: Tasklet
- Scope: exact-byte recovery and delivery; no scientific or promotion assessment.
- Verdict: PASS_WITH_NOTES
- Evidence: original ZIP, inventory, release report, detached hash record, and stored source directory.
- Notes: manifest identities and prior test/rebuild outcomes retain the recorded scope above. Hash identity does not establish scientific truth or authorial priority.
- Freeze/promotion authority exercised: none.
- Receipt SHA256: detached in DELIVERY_RECEIPT_SHA256.txt.
