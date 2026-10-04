# NOVA Q / EIT — LEVEL 0 EVALUATOR V0.4 DELIVERY NOTE

Author / Founder / Architect: Toni Mladenovski
Implementation role: ChatGPT

Target grammar:
LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3

Frozen grammar SHA-256:
d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852

V0.3 status:
FAILED_HELD_OUT

V0.3 held-out round 2:
- must-fail: 80
- correct rejects: 74
- false accepts: 5
- crashes: 1
- must-pass: 16
- false rejects: 0

V0.4 status:
SOFTWARE_CANDIDATE
READY_FOR_NEW_HELD_OUT_ROUND_3
NOT_HELD_OUT_VALIDATED
NOT_MEMORY_MODEL_PROOF

## Change scope

V0.4 changes only numeric canonicalization behavior and fail-closed exception
handling. The frozen REV3 grammar is unchanged.

### Root cause removed

V0.3 used context-dependent Decimal operations:
- Decimal.normalize()
- Decimal.quantize()

Those operations were capable of:
- rounding away distinctions after the active Decimal context precision;
- raising InvalidOperation for sufficiently large integers.

V0.4 performs numeric canonicalization lexically:
1. remove grouping commas;
2. if a decimal point exists, strip trailing zeros from the fractional part;
3. if the fractional part becomes empty, drop the decimal point;
4. otherwise preserve every remaining digit exactly.

No normalize(), quantize(), or context-dependent Decimal arithmetic is used.

Examples:
- 21.5000 -> 21.5
- 64.000 -> 64
- 21.50000000000000000000000000001
  -> 21.50000000000000000000000000001

### Extractor numeric representation

- integer values are emitted as arbitrary-precision Python integers;
- non-integer numeric values are emitted as exact canonical decimal strings;
- every numeric fact also carries `number_canonical`;
- comparator semantics use `number_canonical`, not binary floating point.

### Fail-closed behavior

Candidate-text parsing failures return UNRESOLVED JSON.
Configuration/environment/comparator failures return BLOCKER JSON.
Top-level exception handling prevents uncaught candidate-input failures from
terminating without JSON.

### Architecture unchanged

Extractor reads:
- frozen grammar
- candidate text

Extractor does NOT read:
- V
- Q

Comparator reads:
- extraction result
- V

Comparator does NOT read Q.

### Unit-class contract

`PRODUCTION_UNIT_CLASS` is unchanged from V0.3 and remains an explicit
per-production implementation contract checked against the frozen production
templates at startup.

### Acceptance boundary

Round 2 is now disclosed and therefore is regression material, not a valid new
blind test.

Claude should create a new post-V0.4 held-out round 3 without disclosing it
before execution.

Required acceptance target:
FALSE_ACCEPTS = 0

Passing round 3 would validate V0.4 only inside the frozen restricted-language
domain. It would not establish unrestricted natural-language memory
preservation or a general memory theory.
