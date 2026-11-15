"""Public data sources for the site profile (build spec section 3).

Each module exposes `read(block, pin, footprint, *, client) -> list[Reading]`
(see `app.services.site.types`). It fetches by grid-snapped block through
the guarded client, samples at the pin or over the footprint on this server,
raises SourceUnavailable when the service fails, and returns a reading with
level "unknown" when the service answers but has no data there.
"""
