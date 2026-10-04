# NOVA Q / EIT — LEVEL 0 EVALUATOR V0.4 FREEZE RECORD

Author / Founder / Architect / Final governance: Toni Mladenovski
Implementation: ChatGPT. Adversarial review and held-out rounds: Claude.

FREEZE_STATUS = FROZEN
FROZEN_BY = Toni Mladenovski
FROZEN_ON = 2026-10-04
The freeze takes effect on the author's own commit of this record.
EXTERNAL_TIMESTAMP = PENDING_GIT_COMMIT

## Target grammar (unchanged)

LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3
sha256 d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852
public commit 56be3b116000c1add857e436ef09171d13511286 (2026-10-04T08:59:20-04:00)

## Frozen evaluator files

17605981e658565fb5bb0d00798dfad1979436e311d3d117a540e223fe397ff0  level0_extract_v0_4.py
72788e986723fd8ab2f649809eae6c6d256d7da7f52f81c5f6ad6e3c6b157f61  level0_compare_v0_4.py
9227f79e3b2f0b97d85dd5e00c84482dcb20fb22868f1276b34fb4c3b6f0d3f3  test_level0_v0_4_public.py
ed4c26f472705b42fcbbe0b7efe93f4a6e383f6d2223a880e21ba2aa04db3778  DELIVERY_NOTE_V0_4.md
9ec9959cd25685007b980a945ee46629ea0cd61a6731117726cc42279ee4787a  SHA256SUMS_V0_4.txt

## Validation of V0.4

Public regression test: PASS
Regression on disclosed round 2: 80 must-fail, 16 must-pass, FALSE_ACCEPTS 0, FALSE_REJECTS 0, CRASHES 0
Held-out round 3 (written after V0.4 delivery, not disclosed before the run):
  MUST_FAIL 84, CORRECT_REJECTS 84, FALSE_ACCEPTS 0
  MUST_PASS 22, CORRECT_ACCEPTS 22, FALSE_REJECTS 0
  CRASHES_OR_BLOCKERS 0
Fuzz: seed 20261004, 118746 mutants, 696 accepted, 0 crashes.
  380 accepted mutants differ only in separators or spacing.
  316 were not resolved by the first oracle and were resolved by fuzz_inspect.py:
  a period instead of a newline between two sentences, or one of four
  grammar-allowed renderings (30 day, 21.50, 2,048, 4,096). No fact change found.
CLI error cases: 6, unhandled failures 0.

## Preserved failure: V0.3

STATUS = FAILED_HELD_OUT. Kept as historical evidence, not overwritten.
Round 2: 80 must-fail -> 74 correct rejects, 5 FALSE_ACCEPTS, 1 crash; 16 must-pass -> 16 correct.
Root cause: Decimal.normalize()/quantize() rounded at 28 significant digits and
raised InvalidOperation on very large integers.
Provenance note: the V0.3 .py files here are the bytes reconstructed from the text
ChatGPT printed (re-wrapped lines). They do NOT reproduce the SHA-256 values ChatGPT
stated for V0.3 (3dd8dee6..., df10dae4..., 162115bc...). These are the bytes that
were actually tested. DELIVERY_NOTE_V0_3.md does reproduce its stated hash.

## Known properties (not scored)

- U+037E (Greek question mark) is accepted as ';' because CANON_SPEC requires NFC.
- CRLF line endings and a leading BOM give UNRESOLVED. A compressor must emit LF, no BOM.
- Result files are stored here with a .txt extension; the scripts write the same
  bytes under the .json names shown inside them.

## Boundaries

RESTRICTED_LANGUAGE_ONLY
FINITE_TEST_VALIDATION_ONLY
NOT_GENERAL_NATURAL_LANGUAGE_VALIDATION
NOT_MEMORY_MODEL_PROOF
NOT_PHYSICAL_VALIDATION
NOT_GENERAL_THEOREM
Passing Level 0 gives no right to stronger MEMORY claims. AI agreement is not validation.
