# The extraction model never decides

Catalog growth is split across two model tiers. A light model does retrieval
and extraction only — find the page, quote the passage, propose a value — and a
strong model adversarially verifies, covering every harm-capable field and a
sample of the rest. The light tier resolves nothing, fills no gaps, and settles
no disagreements; anything it cannot attach a quote to becomes null rather than
a guess. Its output is admitted at `inferred` and can only reach `sourced` by
passing verification.

## Consequences

The split exists because of a measurement that is not visible in the code: an
adversarial audit of a research run performed by a *full-strength* model killed
14% of proposed fields, including one where the researcher promoted a
class-level light floor into a species-level value. Extraction is a task a
light model can be held to; horticultural judgment is not. Nothing from either
tier reaches the database except through `apply_review`, so the safety
properties are enforced by tested code rather than by prompt wording.
