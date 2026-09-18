# Supporting quotes stay server-side

Each Claim stores the passage from the citation that supports it, but that
passage is never sent to a client. What ships is the value, the Authority's
name, and a link. Facts are not copyrightable and the attribution is the honest
thing to show; the verbatim passage is the part that belongs to the publisher,
and we hold it as audit evidence rather than as content.

## Consequences

Storing something we never display looks redundant until someone has to answer
"where did this number come from" two years from now, or purge an Authority
whose terms turn out to be incompatible. Both need the passage. Anyone adding a
"show the evidence" feature should surface the link, not the text.
