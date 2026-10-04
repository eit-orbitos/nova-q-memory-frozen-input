# NOVA Q / EIT MEMORY — Frozen Input Package V0.1

Author / Founder / Architect: Toni Mladenovski (EITNetworks LLC)
License: CC BY 4.0
Frozen on: 2026-10-03

## What this is

The fixed input data for a test of one narrow claim: a memory text can change
form while a pre-declared set of 20 facts stays recoverable.

This repository fixes the inputs. **No test has been run on them yet.**

    FREEZE = INPUT_BYTES_FIXED
    FREEZE != TEST_PASSED / MEMORY_MODEL_VALIDATED / NOVELTY_ESTABLISHED

## Frozen artifacts

| Artifact | File | SHA-256 |
| --- | --- | --- |
| V (20 facts, canonical JSON) | NOVA_Q_FIXTURE_01_REVIEW_DRAFT.json | 4898726e8f5425ce50930d14161940a845a2ec941e601a1988ca4d6c6e046eb4 |
| Q (20 queries, canonical JSON) | NOVA_Q_FIXTURE_01_REVIEW_DRAFT.json | 8aa788a8bff223c97bac04de02171da28e9d9b8be9415f45a17e71614bd97b19 |
| M_0 v0.1-v4 (source text) | NOVA_Q_FIXTURE_01_M0_SOURCE.txt | c0f1ffc9bc2679380ee8da77a8e98a0fb2987b606f8b0aaa69a40d4be758d439 |
| CANON_SPEC V0.1 | NOVA_Q_CANON_SPEC_V0.1.md | 9760b32d23ab1db4639e49211d75c0116726f7060fff6d199ef1e554cb760e92 |
| ORIGIN V0.1 (patched) | NOVA_Q_ORIGIN_V0.1_PATCHED.md | 58eff4b31017cdd47fea487926c7936db2212fb71512f55648dcb9b372d10c20 |

V and Q hashes are over canonical JSON bytes (sorted keys, no insignificant
whitespace, UTF-8, NFC). The other hashes are over the raw file bytes.
`NOVA_Q_FREEZE_RECORD.json` holds the same values and the change log.

Known note: the fixture JSON keeps the file name and internal status
`REVIEW_DRAFT`; the freeze record binds its V and Q arrays, not the whole file.

## Verify it yourself

    python3 check_fixture.py .

Prints every file hash and recomputes the V and Q hashes. Python 3, no packages.

## Status of the test

- Level 0 (measuring instrument) V0.1: **FAILED_CALIBRATION**.
  On the frozen M_0 it recovered 16 of 20 facts, and in an adversarial set of
  24 cases it accepted a corrupted fact as correct in 14.
  `attack_level0.py` is that adversarial set.
- Level 0 V0.2: not written yet.
- Compression experiment: not run.
- Test protocol: not frozen (no mechanism yet for detecting invented facts).

## Claim boundary

The individual components (fact tuples, provenance records, question-based
fact checking, negative controls) are prior art. Whether their combination into
one fail-closed protocol is distinct is an open question. Nothing here supports
any claim about AI performance, hallucination reduction, AGI or ASI.

## Roles

Human governance and final decisions: Toni Mladenovski.
AI systems contributed under human direction and are not authors:
ChatGPT (formalization, implementation), Claude (adversarial review),
Kimi (semantic audit, provenance). AI agreement is not validation.
