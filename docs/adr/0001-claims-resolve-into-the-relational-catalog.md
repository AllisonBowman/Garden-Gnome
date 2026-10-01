# Claims resolve into the relational catalog, not a graph database

Every catalog value needs to trace to a citation, which is a graph-shaped
problem, and the obvious reading of "use a graph" is a graph database. We are
not doing that. Claims and Authorities become ordinary tables beside `Species`,
and `Species` keeps a materialized Resolved value per field, recomputed by an
idempotent command in the manner of `recompute_xrefs.py`.

## Considered options

A dedicated graph store (Neo4j, or RDF) was rejected: it splits the source of
truth in two and adds an operational dependency on Fly for a graph of roughly
two thousand nodes that SQLite handles without noticing. Resolving claims at
read time was rejected because advice and reminders are hot paths, and cold
starts already cost us. Keeping claims only in the review JSON — the status quo
— was rejected because provenance then dies at load time and cannot be queried,
which defeats the point of collecting it.

## Consequences

A Resolved value can go stale when resolution rules change, so rows carry the
resolver version that produced them and staleness is a query rather than a
guess. Because Authorities are rows and not strings, a licence that turns out
to be unusable is a delete, not an archaeology project — this is the property
that ASPCA's terms taught us to want.
