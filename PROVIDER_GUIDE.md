# Provider integration (DRA v3.0 engine)

A provider observes a `StrategyContext` and emits a list of
`CriterionAttestation` records. Each attestation is one provider's verdict on
**one specific criterion id** from
[`methodology/criteria.py`](methodology/criteria.py).

## Contract

Implement a subclass of `providers.base.RaterBase`:

```python
class RaterBase:
    name: str

    def attest(self, ctx: StrategyContext) -> list[CriterionAttestation]: ...
    def supported_criteria(self) -> set[str]: ...
```

A `CriterionAttestation` has:

- `layer` — `asset` | `market` | `vault`
- `component` — `security` | `operations` | `strategy_economics`
- `criterion_id` — must be a key in the criteria registry (`get_criterion(id)`).
- `verdict` — `verified`, `violated`, or `unknown`.
- `source` — the provider's name (engine fills this in if you leave it blank).
- `evidence` — short human-readable string for transparency.

`supported_criteria()` returns the subset of registry ids your provider can ever
attest. It is **not** enforced by the engine, but operators rely on it to audit
which provider covers which corner of the rubric.

## Resolution rule

For each criterion the engine applies the rule below — keep it in mind when
deciding when to file a verdict:

- ≥ 1 `verified` AND no `violated` → criterion is **satisfied**.
- Any `violated` → criterion is **unsatisfied**, regardless of how many other
  providers verify it.
- No attestation, or only `unknown` → **unsatisfied** (opacity penalised).

Use `verified` only when your data source actually supports the claim. Use
`violated` to explicitly downgrade a cell. Avoid `unknown` unless you want to
record presence-of-data for audit trails.

## Mapping numeric signals

Most upstream APIs return numeric scores. Define an explicit threshold table at
the top of your adapter file and pass it through
`providers._helpers.threshold_attestations`:

```python
from providers._helpers import threshold_attestations

S1_THRESHOLD = 0.4
S2_THRESHOLD = 0.7

threshold_attestations(
    domain_score,
    layer="market",
    component="security",
    s1_criteria=("market.security.s1.audited", "market.security.s1.lindy_1y"),
    s2_criteria=("market.security.s2.multi_audit_bounty", "market.security.s2.lindy_3y"),
    s1_threshold=S1_THRESHOLD,
    s2_threshold=S2_THRESHOLD,
    source="my_provider",
    evidence=f"my_provider.security={domain_score}",
)
```

Above `s2_threshold` every Stage 1 and Stage 2 criterion gets a `verified`
verdict; between `s1_threshold` and `s2_threshold` only Stage 1 is verified;
below `s1_threshold` Stage 1 criteria get an explicit `violated` (opt-out via
`violate_below_s1=False`).

## Caching

`ctx._cache` is a per-run dict your adapter can use to avoid duplicate HTTP
requests. Use a key that includes the upstream URL or identifying parameters.

## Environment

Missing API keys must produce an empty attestation list, never a hard failure.
See [`.env.example`](.env.example).

## Worked example

`examples/provider_integration.py` shows a minimal vault-monitor provider that
verifies three criteria from local data only.

## Tests

Add fixtures under `tests/` and stub `ctx._cache` to bypass HTTP. The existing
`tests/test_providers.py` shows the pattern.
