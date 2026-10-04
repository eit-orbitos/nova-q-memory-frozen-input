# NOVA Q / EIT — CANON_SPEC_V0.1

**Artifact:** CANON_SPEC_V0.1 (canonicalization specification)
**Parent:** MEMORY_NONTRIVIAL_TWIN_TEST_PROTOCOL_V0.1-REV §7
**Author / Founder / Architect:** Toni Mladenovski
**Project:** NOVA Q / EIT / TIE
**Status:** PRE-FREEZE_CANDIDATE — NOT_PROOF — NOT_AI_PERFORMANCE_CLAIM

---

## 1. Encoding and text normalization

- All canonical bytes are **UTF-8**.
- All strings are normalized to **Unicode NFC** before serialization.
- No leading/trailing whitespace is permitted inside canonical string values; internal runs of whitespace are collapsed to a single ASCII space (U+0020).
- Line endings: not applicable (canonical form contains no whitespace outside string values).

## 2. Serialization format

- Canonical serialization is **JSON** with:
  - object keys sorted lexicographically (by Unicode code point),
  - no insignificant whitespace (`separators=(",", ":")`),
  - `ensure_ascii=false` (non-ASCII characters serialized directly as UTF-8).
- `V` serializes as a JSON **array** of fact objects in ascending `fact_id` order.
- Each fact object has exactly these keys: `fact_id`, `subject`, `relation`, `value`, `unit`, `qualifier`.
- `Q` serializes as a JSON array of query objects (`fact_id`, `subject`, `relation`) in the same order.

## 3. Fact schema

```
FACT = ( fact_id, subject, relation, value, unit, qualifier )
```

- `fact_id`: string, pattern `F[0-9]{2}`, unique, ascending order defines V order.
- `subject`: string, lowercase snake_case identifier.
- `relation`: string, lowercase snake_case identifier.
- `value`: JSON number or JSON string (see §4–§6).
- `unit`: string; empty string `""` means unitless; `"state"` marks enumerated state values (§6).
- `qualifier`: string enum — `EXACT` | `APPROX`.

### 3.1 Qualifier semantics (FIXTURE_01 requirement)

- `EXACT`: the value must be recovered exactly per §4–§6 rules. **Approximation markers are invalid for EXACT facts.**
- `APPROX`: the source itself declares approximation. An approximation marker is **mandatory** and canonicalizes into `qualifier=APPROX`, while the numeric value itself is still compared **exactly** under the numeric canonicalization rules (§4). An extraction that drops the marker (or adds one to an EXACT fact) yields a qualifier mismatch → **INVARIANT_LOST**.
- Therefore `(64, Mi, EXACT)` and `(64, Mi, APPROX)` are **different invariants**, while `about 21.5 °C` and `approximately 21.5 °C` canonicalize to the same tuple `(21.5, degC, APPROX)`.
- **String literals without an explicit alias table are case-sensitive** after NFC + whitespace normalization: `eu-central` → PASS, `EU-CENTRAL` → FAIL, `Eu-Central` → FAIL. Any case alias must be added explicitly in a future CANON_SPEC version.

## 4. Numbers

- Canonical numeric form: JSON number; integers without decimal point; non-integers in shortest decimal form (no exponent for values in [1e-6, 1e21)).
- Accepted surface forms that canonicalize to the same number (V0.1 is **English-only**):
  - ASCII digits (`64`),
  - quoted digits (`"64"`),
  - digits with thousands separators when grouping is exactly 3 digits (`4,096` → `4096`, `1,000` → `1000`),
  - a trailing `.0` on an integer value (`64.0` → `64`),
  - English number words for integers 0–100 (`"sixty-four"`, `"twelve"`).
- **Decimal comma is NOT accepted in V0.1**: `21,5` does not canonicalize to `21.5`.
- **Approximation markers apply only to qualifier logic (§3.1), never to the number itself.** V0.1 is ENGLISH_ONLY; the frozen approximation marker set is exactly:

  `about`, `approximately`, `approx.`, `around`, `roughly`, `approximately equal to`, `~`

  No other word is treated as APPROX unless explicitly added in a future CANON_SPEC version. For EXACT facts: presence of any frozen APPROX marker → qualifier mismatch → INVARIANT_LOST. For APPROX facts: presence of one frozen APPROX marker is mandatory. In both cases the numeric value is compared exactly after parsing. EXACT does **not** require the word `exactly` — EXACT means *no approximation marker present*.
- `63.9`, `65`, `64.0 MB` (wrong unit) never equal `INTEGER(64)` under the frozen rules.

## 5. Units

Frozen alias table (equivalence classes):

| Canonical | Accepted aliases |
|---|---|
| `Mi` | `Mi`, `MiB`, `mebibytes` |
| `Gi` | `Gi`, `GiB`, `gibibytes` |
| `MB` | `MB`, `megabytes` |
| `GB` | `GB`, `gigabytes` |
| `ms` | `ms`, `milliseconds` |
| `Mbps` | `Mbps`, `mbps` |
| `degC` | `degC`, `°C`, `degrees Celsius` |
| `days` | `days`, `day` |
| `entries` | `entries`, `entry` |
| `state` | `state` |
| `""` | unitless |

- **`MB`/`GB` are KNOWN but NOT equivalent to `Mi`/`Gi`** in V0.1. `64 Mi → 64 MB` = INVARIANT_LOST; `2048 Gi → 2048 GB` = INVARIANT_LOST.
- Distinction: **KNOWN_WRONG_UNIT → INVARIANT_LOST**; **UNKNOWN_UNIT (string not in this table) → UNRESOLVED** at extraction, and the trial verdict is UNRESOLVED (single verdict; it does not also become INVARIANT_LOST).
- The bare alias `C` was removed: it collides with the subject literal `Node C`.

### 5.1 Unitless and state facts

- When frozen V has `unit = ""` (unitless), the extracted surface expression may contain a descriptive noun (`nodes`, `items`, `records`, ...) without that noun becoming a compared canonical unit. Only the declared VALUE is compared. Example: `"twelve nodes"` → value = 12, unit comparison = NOT_APPLICABLE.
- When frozen V has `unit = "state"`, the lexical state token is canonicalized under §6 and physical/unit comparison is not performed. Example: `"currently active"` → state = ACTIVE, unit comparison = NOT_APPLICABLE.

## 6. State / boolean values

| Canonical | Accepted aliases |
|---|---|
| `ACTIVE` | `ACTIVE`, `active`, `currently active` |
| `STANDBY` | `STANDBY`, `standby` |
| `DISABLED` | `DISABLED`, `disabled` |
| `FULL` | `FULL`, `full`, `full duplex`, `full-duplex` |
| `FIFO` | `FIFO`, `fifo`, `first-in, first-out`, `first-in first-out` |

### 6.1 String literal aliases

String literals without an entry here or in §5/§6 are case-sensitive and alias-free (§3.1). Explicit exceptions:

| Canonical | Accepted aliases |
|---|---|
| `daily` | `daily`, `every day` |
| `PRODUCTION` | `PRODUCTION`, `production` |

- Negations (`NOT_ACTIVE`, `INACTIVE`, `not active`, `неактивен`) never canonicalize to `ACTIVE`.
- State comparison is on the canonical state token, case-sensitive after canonicalization.

## 7. Dates

- Canonical date form: ISO 8601 `YYYY-MM-DD` strings only. Time components are out of scope for fixture #1.
- Accepted surface forms that canonicalize to the ISO date: `YYYY-MM-DD`, `D Month YYYY` (English month names, e.g. `18 April 2026` → `2026-04-18`). Any other date surface form → UNRESOLVED at extraction.

## 8. Ordering

- V and Q order is strictly ascending `fact_id`. Reordering of surface text does not affect V.

## 9. Hashing

- `V_SHA256 = SHA256(canonical_bytes(V))`
- `Q_SHA256 = SHA256(canonical_bytes(Q))`
- `CANON_SPEC_SHA256 = SHA256(UTF-8 bytes of this document, NFC)`.
- **Hashes are never written back into the artifact they hash.** All hashes live in a separate `FREEZE_RECORD.json` = { artifact, version, sha256, byte_length, timestamp, external_timestamp }.
- Any hash is valid only together with `CANON_SPEC_V0.1` and its hash.

## 10. Verdicts and scoring (Experiment D)

- UNRESOLVED remains a distinct diagnostic verdict.
- For compressor performance scoring in Experiment D: **UNRESOLVED → TRIAL_NOT_SUCCESSFUL**. It must not count as TWIN_VALID and must not serve as an escape from failure.
- Record separately: `twin_valid_count`, `invariant_lost_count`, `unresolved_count`, `transformation_invalid_count`.
- **SUCCESS_COUNT = TWIN_VALID only.**

## 11. Change rule

Any change to this specification requires a new version (`CANON_SPEC_V0.2`), a new hash, a parent link, and a changelog. Frozen V/Q hashes are never recomputed under a new spec and retroactively claimed as V0.1 results.

---
END — CANON_SPEC_V0.1 (PRE-FREEZE_CANDIDATE)
