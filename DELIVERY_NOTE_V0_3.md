# NOVA Q / EIT — LEVEL 0 EVALUATOR V0.3 DELIVERY NOTE

Author / Founder / Architect: Toni Mladenovski
Implementation role: ChatGPT
Target grammar: LEVEL0_CONSTRAINED_LANGUAGE_V0.1_REV3
Frozen grammar SHA-256:
d7a68615f38beac2808936bea9591c2a68fc22e0ae10024159d2a49682252852

STATUS:
SOFTWARE_CANDIDATE
READY_FOR_INDEPENDENT_REVIEW
NOT_HELD_OUT_VALIDATED
NOT_MEMORY_MODEL_PROOF

## Architecture

1. `level0_extract_v0_3.py`
   - reads only the frozen grammar and candidate text;
   - never reads V or Q;
   - verifies the grammar SHA-256 before parsing;
   - obtains every production regex from the grammar JSON;
   - uses `fullmatch`;
   - any clause matching zero or more than one production causes whole-text
     `UNRESOLVED`;
   - duplicate parsed facts cause `UNRESOLVED`;
   - no unknown suffix/prefix/comment is discarded.

2. `level0_compare_v0_3.py`
   - reads extractor output and V;
   - never needs Q;
   - computes:
       parsed facts - V = FACT_INVENTED
       V - parsed facts = missing invariant
   - verdict order:
       extractor UNRESOLVED -> UNRESOLVED
       any invented fact -> FACT_INVENTED / INVALID_TRANSFORMATION
       otherwise any missing fact -> INVARIANT_LOST
       otherwise -> TWIN_VALID

## Explicit unit class per production

The extractor contains `PRODUCTION_UNIT_CLASS`, covering all 32 frozen
productions:

- memory_capacity -> DATA_UNIT
- state -> no captured unit; production default `state`
- node_count -> no captured unit
- max_latency -> TIME_UNIT
- region -> no captured unit
- bandwidth -> RATE_UNIT
- duplex -> no captured unit; production default `state`
- temperature -> TEMP_UNIT
- calibration_date -> no captured unit
- depth -> ENTRY_UNIT
- policy -> no captured unit; production default `state`
- capacity -> DATA_UNIT
- schedule -> no captured unit
- retention -> DAY_UNIT
- mode -> no captured unit; production default `state`
- firmware_version -> no captured unit

At startup, this table is checked against the actual frozen production
templates. Drift is a BLOCKER.

## Explicit validators

NUMBER:
- production lexical matching comes from frozen grammar JSON;
- `parse_number()` re-validates against `token_classes.NUMBER.regex`;
- English number words come from `grammar.number_words`;
- conversion uses Decimal;
- canonical decimal text is retained for exact comparator semantics.

DATE:
- production lexical matching comes from frozen grammar JSON;
- `parse_date()` re-validates against `token_classes.DATE.regex`;
- Gregorian calendar validity is checked with Python `datetime`;
- output canonicalizes to ISO `YYYY-MM-DD`.

Regex:
- evaluator requires the frozen declaration `Python re` + `re.ASCII`;
- evaluator refuses another dialect declaration.

## No second regex grammar

There is no hardcoded second copy of the 32 production regexes.
`regex_template`, placeholders, token classes, aliases, semantic maps,
clause-boundary rules, value classes, relation, operator and defaults are read
from the frozen JSON.

The only production-specific table in evaluator code is the explicitly
requested unit-token-class table. It is a contract check, not a regex copy.

## Public test boundary

`test_level0_v0_3_public.py` contains only structural/comparator smoke tests.
It intentionally contains no new held-out corruption set.

Independent held-out cases must be created after grammar freeze and should not
be disclosed to the implementer before evaluation.

Required acceptance boundary:
FALSE_ACCEPTS = 0

A public/held-out pass validates this evaluator only within the frozen
restricted-language test domain. It does not establish a general theory of
memory, unrestricted natural-language preservation, AGI, ASI, or a physical
law.
