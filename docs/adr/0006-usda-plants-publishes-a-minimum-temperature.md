# USDA PLANTS publishes a minimum temperature, not hardiness zones

Accepted 2026-09-10.

Migration 0013 gave `Species` a `hardiness_zones` column as the one field the
USDA PLANTS Database is trusted on, and scoped that authority to it. The name
was wrong. USDA PLANTS does not publish hardiness zones; those come from the
USDA ARS Plant Hardiness Zone Map, a separate product of a separate agency.
What PLANTS' Characteristics data does state is "Temperature, Minimum (°F)":
the lowest outdoor temperature a species is recorded as tolerating. No claim
in the verified tranche ever named the old field, and no row ever held a
value -- only USDA PLANTS was permitted to write it, and there were no USDA
PLANTS claims. So the column is renamed for what its only permitted writer
publishes: `outdoor_temp_min_f`, a nullable float in degrees Fahrenheit
(migration 0016). USDA PLANTS stays scoped to this field alone, as it was to
the old one, and by tier it outranks any unrestricted authority that names it.

It is not `chill_damage_f`, and the two are kept apart everywhere they are
shown. `chill_damage_f` is the temperature at which cold damage begins on a
plant in cultivation, resolved from the extension services like any other
care value and shown on the Temperature line; `outdoor_temp_min_f` is a
survival floor, stated by a single authority and shown on its own Cold line.
On the same species they can sit tens of degrees apart -- a plant scarred at
45 °F can still be rooted in the ground at 0 °F -- and folding them into one
number would tell a caretaker either to fear a frost their plant shrugs off
or to trust a winter it will not survive.

## Considered options

Keeping the name and filling the column from the ARS zone map was rejected:
the map is a different authority, and a value written under USDA PLANTS' name
from somewhere else is exactly the misattribution the claim graph exists to
prevent. Converting a zone number to a temperature was rejected for the same
reason with an extra step of arithmetic on top. Merging the new field into
`chill_damage_f` was rejected because they measure different events, as
above. Leaving the column empty under the wrong name was rejected because a
column named for a quantity its only writer never publishes is a standing
invitation to fill it by hand.

## Consequences

The upgrade checks the old column is empty before dropping it and refuses
otherwise, since a zone list has no honest translation into a temperature.
Everything that read `hardiness_zones` -- the resolver's field list, the
advisor's fact block, the API schemas, the mobile type and its Care facts
row -- now reads `outdoor_temp_min_f`, and says "survives to N °F outdoors"
rather than "zones". Most rows will stay null, which is correct for a
catalog that is mostly houseplants; a null here is "no record", never
"tender". A future USDA PLANTS claim must quote "Temperature, Minimum (°F)"
from a plant profile, and a citation from any other publisher naming this
field is weighed by tier like any other, not refused.
