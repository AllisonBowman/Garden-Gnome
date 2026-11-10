# A poison rating is about people, and only a named crop is exempt from it

Status: accepted 2026-10-20.

## Context

NC State's Poison Severity sits under its "Poisonous to Humans" heading. The
Problem for Cats and Problem for Dogs tags beside it carry no severity at all,
and the tranche's own details say so ("human-scoped, separate from the pet
tags"). The toxicity sentence put the rating's word in front of the whole
clause, so 113 species read "mildly toxic" to pets from a rating no source
gave for pets: 104 with a bare pet flag ("Mildly toxic to pets and people")
and 9 aroids. Garlic, the azaleas, the daffodils and hardy cyclamen were
among them.

The candidate rule keeps a species a source rates a high-severity or fatal
poison for people off every growing area's list. Commit 798f905 exempted
anything recorded as eaten, to keep potato, eggplant, peanut, tomatillo and
butter beans. Mayapple came back with them: its ripe fruit is eaten, and
every other part of it is highly poisonous.

## Decision

A rating, a table naming people, or a source calling the plant fatal to
people sets the people's severity, and its word ("seriously", "mildly") goes
on the people's half of a sentence only. The animals are "toxic to pets", or
to cats or dogs, unless a table or a source's own grave words about pets say
more ("Ingestion of this plant by pets can be fatal"). A grave word beside a
pet tag, or about horses and livestock, is not about pets. The list row's
hazard line follows the same split, without "mildly".

A food crop is named by its eaten part. The toxicity table (KNOWN_NUANCE)
lists the crops, each with the eaten part and the harmful parts its cited
passages name, and the sentence leads with the crop: "The tubers are the
crop; the leaves and stems ... are seriously toxic to people, and toxic to
cats and dogs." Only those table crops are exempt from the high-severity
rule. Being recorded as eaten is not enough. The exemption does not read
the bed's goals.

A source's "Invasive Species" tag keeps a species off candidate lists, the
same as a noxious weed, with or without the crop exemption.

## Consequences

On the shipped catalog (997 species) no sentence calls a pet "mildly" toxic.
14 species have a source calling them fatal or seriously toxic to pets, and
their sentences say so for pets; for 8 of them that is new. The crop
exemption admits exactly potato, eggplant, peanut, tomatillo and butter
beans, and a test seeded from the real tranche pins that set, so a new crop
is a deliberate table entry. Mayapple, Japanese and
Chinese wisteria, beefsteak plant, leatherleaf mahonia and English ivy are
never put forward. They can still be looked up and added by hand, with their
warnings.

Taro is not affected. NC State rates it Medium, the same as tomato, so the
high-severity rule never reaches it. It is offered with its hazard line and
its "only after preparation" edibility note. Keeping it off a list would
need a rule no source states.

The exemption is keyed on the table, not on the edibility passage being
unconditional. Potato's and eggplant's passages limit what is eaten ("All
green parts ... are inedible"; "The fruits should not be consumed raw"), so
an edibility test would have dropped two of the five crops.
