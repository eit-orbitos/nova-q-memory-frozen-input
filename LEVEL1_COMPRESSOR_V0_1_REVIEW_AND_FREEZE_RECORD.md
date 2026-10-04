# NOVA Q / EIT — LEVEL1_COMPRESSOR_V0.1 LEAKAGE REVIEW AND FREEZE RECORD

Author / Founder / Architect / Final governance: Toni Mladenovski
Compressor implementation: ChatGPT. Source review (protocol section 34): Claude.

Protocol: LEVEL1_PROTOCOL_V0.4
  commit 6ce264c71c3e8facf6b77de277fb520497f06d7c
  sha256 627388d26e451dc8d0410ca16b6d2c3fcd5389813c75f86cdeef28685b58bce1

## Reviewed files (exact bytes)

0ed99cb21048e8e1f8c9e526469c23697d5b6b414401e85120f5c26e360dba81  level1_compressor_v0_1.py
a9dad00222a62faeedbef1c7a2ed7d5ffd6d0b3d582a800deedf0fe53eeb0450  LEVEL1_COMPRESSOR_V0_1_DELIVERY_NOTE.txt
044d9b9e282379de9472b5c75b97bb5afe7df38f38052da118c7288a6eaf1c40  SHA256SUMS_LEVEL1_COMPRESSOR_V0_1.txt

All three reproduce the hashes stated by the implementer.

## Review outcome

LEAKAGE_REVIEW = PASS
SHARED_PARSER_LIMITATION = False (own parser built from the grammar JSON;
level0_extract_v0_4.py and level0_compare_v0_4.py are not imported)

Static findings:
- no fixture values or subjects from M_0 / V in the source
- no M_0 or control fingerprint; the only hash constant is the grammar hash
- no known 481-character text
- no access to V, Q or the comparator
- imports: argparse, datetime, hashlib, itertools, json, os, pathlib, re, sys,
  typing, unicodedata; no network-capable module, no subprocess
- reads only --grammar and --input; writes only --out
- no persisted state, no randomness

Dynamic pre-check (level1_compressor_precheck_claude.py, seed 4242; these are
NOT the held-out controls and are not part of the Level 1 verdict):
- original M_0: exit 0, 481 characters, TWIN_VALID under evaluator V0.4
- 400 random valid REV3 inputs, expected V' built directly from the generating
  facts: 400/400 TWIN_VALID against V'; 0 TWIN_VALID against the original V;
  400/400 byte-identical under different PYTHONHASHSEED values
- 11 invalid inputs: exit 2, stdout empty, no output file
Python 3.13.16, Linux.

## Notes (non-blocking)

1. The output for M_0 is byte-identical to the public MINIMUM_COMPACT_REV3.txt.
   Both apply the same shortest-rendering rule; the source does not contain
   that text.
2. 39 of the 400 random inputs cannot reach ratio < 0.70 because they are
   already short. This is why the protocol requires a feasibility witness for
   every held-out control.
3. The approximation words are a hardcoded second copy of grammar vocabulary;
   "import os" is unused.
4. Evaluator V0.4 property found here: an integer above 4300 digits is accepted
   by the compressor but UNRESOLVED in the evaluator (Python integer-string
   limit). Fail-closed; such inputs are outside the control envelope
   (section 7 requires extractor status PARSED). The evaluator is not changed.
5. NETWORK_ISOLATION = NOT_ENFORCED_AT_OS_LEVEL in the review environment
   (methodological limitation, protocol section 21).
6. Role concentration (protocol section 28): Claude is reviewer, control author,
   operator and scorer.

## Freeze

COMPRESSOR_FREEZE_STATUS = FROZEN on the author's own commit of this record.
FROZEN_BY = Toni Mladenovski
EXTERNAL_TIMESTAMP = PENDING_GIT_COMMIT
Any change to the source after this review invalidates the review.
Held-out controls are authored only after this commit.

Boundaries: restricted-language pipeline only; not a MEMORY claim.
AI agreement is not validation.
