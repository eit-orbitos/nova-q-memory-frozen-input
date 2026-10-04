# NOVA Q / EIT — LEVEL 1 RESULT (LEVEL1_PROTOCOL_V0.4)

Author / Founder / Architect / Final governance: Toni Mladenovski
Compressor: ChatGPT. Control author, operator, scorer: Claude (role concentration, protocol section 28).

## Result

LEVEL1_PRIMARY_PASS

| Run | Input | Input chars | Output chars | Ratio | vs own V_i | vs original V | Deterministic | Status |
|---|---|---|---|---|---|---|---|---|
| L1_R01 | ORIGINAL_M0 | 789 | 481 | 0.6096 | TWIN_VALID | NOT_APPLICABLE | True | PASS |
| L1_R02 | HELD_OUT_CONTROL_1 | 783 | 479 | 0.6118 | TWIN_VALID | INVALID_TRANSFORMATION | True | PASS |
| L1_R03 | HELD_OUT_CONTROL_2 | 393 | 184 | 0.4682 | TWIN_VALID | INVALID_TRANSFORMATION | True | PASS |
| L1_R04 | HELD_OUT_CONTROL_3 | 1323 | 733 | 0.5540 | TWIN_VALID | INVALID_TRANSFORMATION | True | PASS |
| L1_R05 | HELD_OUT_CONTROL_4 | 876 | 503 | 0.5742 | TWIN_VALID | INVALID_TRANSFORMATION | True | PASS |

Invalid-input control: exit code 2, stdout 0 bytes, candidate created: False -> PASS

## Chain of commitments

- protocol frozen: commit 6ce264c71c3e8facf6b77de277fb520497f06d7c
- compressor frozen: commit 2516d18f2213891ac056108f8a65f9dd4566a098 (sha256 0ed99cb2...ba81)
- control package hash committed: commit d8f3b7bc7fbfa633d42bb6953367e8b7036a9783 (2026-10-04T14:34:01-04:00)
- executions started after that commit: first start 2026-10-04T18:35:22.315+00:00 (UTC)
- revealed package LEVEL1_CONTROL_PACKAGE_V0_1.txt: sha256 fae2f3bc59c847855b1256739ade8b10bf9257646637910002cde08d4bc9c257
- CONTROL_COMMITMENT_VALID = True
- scoring source: fresh clone at d8f3b7bc7fbfa633d42bb6953367e8b7036a9783; frozen file hashes checked before the run

## Feasibility witnesses and reference checks

All four witnesses TWIN_VALID against V_i with ratio below 0.70; every V_i differs from the original V. PROTOCOL_ERROR = False

## Environment

Python 3.13.16; Linux-6.18.44-fc-v64-x86_64-with-glibc2.39
NETWORK_ISOLATION = ENFORCED_AT_OS_LEVEL (unshare -n)
SHARED_PARSER_LIMITATION = False

## Observations

- For all four controls the compressor output is byte-identical to the control author's feasibility witness.
  Both were produced independently (the witness by the authoring script, before any compressor run on the
  controls) and both apply the shortest-rendering rule of the grammar, so identical output is expected.
- The output for the original M_0 equals the already public 481-character rendering.

## Permitted conclusion (protocol section 38)

Under frozen LEVEL1_PROTOCOL_V0.4, the frozen deterministic compressor produced byte-deterministic outputs
for five distinct valid REV3 inputs. Each output was shorter than 70% of its corresponding input and was
judged TWIN_VALID against its input-specific reference by frozen evaluator V0.4. For the four held-out
controls, the outputs were not TWIN_VALID against the original V. The compressor also failed closed on the
declared invalid-input control.

## Limits

Restricted language only. Five inputs are a finite protocol set, not a success rate. The task is easy by
construction (grammar-derived rewriting); no difficulty claim. The commitment proves the controls did not
change after commitment, not that they were authored without bias. Not a MEMORY claim, not a general
compression claim. AI agreement is not validation.

## Files

LEVEL1_CONTROL_PACKAGE_V0_1.txt       revealed package (exact committed bytes; JSON content)
level1_author_controls_claude.py      authoring script (committed in the commitment file as author_controls.py)
level1_run_and_score.py               execution and scoring script
LEVEL1_RESULT_RECORD.txt              full per-run records (JSON content)
LEVEL1_EVIDENCE_BUNDLE_V0_1.txt       all inputs, V_i, 10 outputs, witnesses, extractor and comparator outputs
