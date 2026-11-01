# Eaten parts: how the field was minted and checked

Written 2026-11-01 for branch `candidate-categorization-proposal`, on the records in `garden-gnome/app/data/verified/` at the ship tip `65ecf93`. It is the audit trail for the `eaten_parts` field that ADR 0011 adds: which species got which parts, from which words, who checked them, and what stayed null and why.

## What was done

The catalog holds 293 verified records that say the plant is eaten (`is_edible` true). Each one already cites the passage that says so. `scripts/catalog/mint_eaten_parts.py` read every such passage and proposed the parts it names as eaten, from a fixed vocabulary of leaves, fruit, seeds, roots, flowers and stems. It reads clause by clause: a clause that speaks of eating and not of harm contributes the parts it names; a clause that speaks of harm contributes only a part it excepts; a comparison ("tastes like cucumber"), another plant's part, a part removed before eating and a timing phrase are blanked first. A crop named by its own word names its part: bananas are the fruit, lettuce the leaves. It fetched no page and added nothing a passage does not say. The script and its output, `scripts/catalog/pipeline/eaten-parts-mint.json`, are in the repository, so the proposals can be regenerated.

It proposed parts for 271 records and found no part in 22. Every proposal then went to two independent readers (Claude, Opus, no tools, the passage and the vocabulary only), one reading literally and one as a skeptic, each asked to say which proposed parts the passage supports, with the words, which it does not, and which it left out. A proposal was written only when both readers agreed: as proposed, or corrected to the same list. Their notes are in `scripts/catalog/pipeline/eaten-parts-verdicts.json`.

## The numbers

- Accepted as proposed: 244.
- Corrected by both readers to the same shorter list: 14.
- Refused by both readers: 9; the field stays null.
- Readers disagreed: 4; the field stays null.
- No part named in the passage: 22; the field stays null.
- Written: 258 records, each with a citation that names `eaten_parts` and carries the same url and quote as the citation behind `is_edible`.
- Parts written: fruit 105, leaves 99, flowers 68, seeds 42, roots 29, stems 25.

A record left null reads in the app as "no source names a part of this plant that is eaten", never as "nothing is eaten". It is off a list that asked for something to eat and counted there.

## Corrected

The parser had read a word that does not say the part is eaten. Both readers removed it, with the words that decided it.

- Raphanus raphanistrum subsp. sativus (Radish): proposed flowers, leaves, roots, fruit, seeds; written roots, leaves, flowers, fruit. The passage supports roots, leaves, flowers and fruit (the edible seed pods), but it never says the seeds alone are eaten, so seeds comes off the list.
- Lagenaria siceraria (Bottle Gourd): proposed flowers, fruit, leaves, seeds, stems; written seeds, leaves, flowers, stems. The passage supports seeds, leaves, flowers and stems as edible, but it names the fruit only as a timing condition ("when the fruit is young"), so fruit is not supported.
- Cucurbita argyrosperma (Cushaw Squash): proposed fruit, seeds; written seeds. Only the seeds are called edible, and the fruits are named only for decoration, so fruit comes off the list.
- Dysphania ambrosioides (Epazote): proposed leaves, seeds; written leaves. The passage supports leaves only, because 'beans' names another food that the leaves help with, not epazote seeds.
- Celosia argentea (Cockscomb): proposed leaves, stems, seeds; written leaves, stems. Leaves and shoots are said to be cooked and eaten, but the seeds are named only as the source of an edible oil, so seeds are dropped.
- Tulbaghia violacea (Society Garlic): proposed flowers, leaves, roots; written flowers, leaves. The passage supports flowers and leaves as edible but says nothing about roots, so roots must be dropped.
- Camellia sinensis (Tea Plant): proposed leaves, flowers; written leaves. The passage supports leaves because they are used to make tea, but it only calls the flowers a source of edible oil, and plain "buds" is not stated to mean flower buds.
- Artemisia dracunculus (Tarragon): proposed flowers, leaves; written leaves. Only "#edible leaves" names an eaten part; "#summer flowers" describes when the plant blooms, not that its flowers are eaten.
- Mentha spicata (Mint): proposed flowers, leaves, seeds; written leaves, flowers. The passage supports leaves and flowers as used in food and drink, but "peas" is a dish the leaves are added to, so seeds is not supported.
- Dalea purpurea (Purple Prairie Clover): proposed leaves, roots; written leaves. Tea is a drink, so the leaves are supported, but "palatable when chewed" never says the roots are eaten or used as food, so the roots are dropped.
- Gleditsia triacanthos (Honey Locust): proposed fruit, seeds; written fruit. The passage supports only the pod pulp (fruit) as edible, and "seed" names the pod rather than saying the seeds are eaten.
- Physalis philadelphica (Tomatillo): proposed fruit, seeds; written fruit. The passage supports fruit only; "seed" is a verb for a preparation step that is not needed, not a statement that the seeds are edible.
- Origanum majorana (Sweet Marjoram): proposed flowers, leaves; written leaves. Only the leaves are called edible, and the flowers appear only as a bloom-time marker, so flowers is removed.
- Rubus occidentalis (Black Raspberry): proposed flowers, fruit; written fruit. The passage calls only the fruits edible and mentions the flowers only as what comes before the fruit, so flowers must be dropped.

## Refused

Both readers found no part the passage says is eaten. Two of these, the firs, are refusals the vocabulary caused: the passage says the needles are made into tea or are edible, and the readers' vocabulary did not list needles under leaves, though the parser's did. They stay null until a pass with that word in the vocabulary; nothing is written on a reading the readers did not make.

- Allium porrum (Leek): proposed stems. The passage calls the whole leek plant a herbaceous perennial grown as an annual vegetable, but it never says a stem, shaft or any other part is eaten, so no part is supported.
- Lactuca sativa (Lettuce): proposed leaves. The passage calls the whole Lettuce plant edible but names no part as eaten, so it does not support leaves.
- Picea abies (Norway Spruce): proposed leaves. The passage names \"leafy twigs\" as the tea material, but twigs are not a vocabulary part and \"leafy\" does not plainly say leaves are used, so no part is supported.
- Hedychium coronarium (Butterfly Ginger): proposed roots. The passage only says the tubers taste spicy and never says they are eaten or used as seasoning, so it supports no eaten part.
- Humulus lupulus (Common Hops): proposed fruit. The passage names only an extract of the fruit bracts as a beer flavoring, which is not a vocabulary part, so no eaten part is supported.
- Laurus nobilis (Bay Laurel): proposed leaves. The passage says bay leaves flavour food during cooking but "should not be eaten", so no part is supported as eaten and the leaves claim fails.
- Fraxinus pennsylvanica (Green Ash): proposed seeds. The passage names only bark as used in food, and bark is not in the vocabulary; "grain" there is another ingredient in the bread, so no vocabulary part is supported.
- Abies balsamea (Balsam Fir): proposed leaves. The passage calls the needles edible, but "needles" is not a vocabulary word for leaves, so no part is supported; if needles should count as leaves, the vocabulary needs to add that word.
- Pinus mugo (Mugo Pine): proposed leaves. The only part the passage says is consumed is \"needles\" made into tea, which is not on the allowed word list for leaves, and the general phrase \"used as ... food\" names no part, so no part is supported.

## Readers disagreed

One reader supported a part the other did not. Nothing is written on a split reading.

- Zingiber officinale (Ginger): proposed roots; one reader roots, stems, the other roots. The passage supports roots (rhizomes, ginger root) and also names young sprouts as edible, which map to stems as shoots, so the proposal omitted stems.
- Polygonatum biflorum (Solomon's Seal): proposed stems; one reader roots, the other stems, roots. The passage says only that the rootstock \"can be eaten\" and says just that the shoots can be boiled, so the supported list is roots, not stems.
- Prunus cerasus (Sour Cherry): proposed fruit; one reader fruit, the other none. The passage says the fruit is used fresh and dried, and in this context that use is as food, so fruit is supported and no other part is named.
- Zea mays var. saccharata (Sweet Corn): proposed seeds; one reader seeds, the other none. The passage says sweet corn, the crop named by "corn" (a seeds word), is picked immature and eaten as a vegetable, though "grain" itself appears only as a contrast and names no part on its own.

## No part named

The passage says the plant is eaten and names no part the vocabulary holds. A record here needs a research pass that cites the source's own line on the part, if the source has one.

- Brassica oleracea (Gongylodes Group) (Kohlrabi): "Edible vegetable."
- Ocimum tenuiflorum (Holy Basil): "A culinary herb especially in Asia used in the same ways as sweet basil though it is commonly cooked or used i..."
- Allium × proliferum (Egyptian Walking Onion): "All parts of the plant are edible raw or cooked."
- Crocus sativus (Saffron Crocus): "To harvest the saffron, remove the bright orange stigmas and use fresh or dry and store in air-tight container..."
- Centaurea cyanus (Bachelor's Button): "Edible"
- Echinacea purpurea (Purple Coneflower): "Herbaceous parts may be steeped as a tea"
- Dahlia pinnata (Dahlia): "Were grown as a food crop by Aztecs, but the practice has died out."
- Alcea rosea (Hollyhock): "Can be used as a showy edible garnish or a container for dip."
- Hibiscus rosa-sinensis (Chinese Hibiscus): "Edible"
- Diospyros virginiana (American Persimmon): "sweet when soft and ripe and may be eaten raw"
- Salvia rosmarinus (Rosemary): "Teas; flavoring for vinegar, jam, bread, butter, stuffing, vegetables, stew, and meat dishes and, when mixed w..."
- Lavandula angustifolia (Lavender): "Edible"
- Foeniculum vulgare (Fennel): "Edible"
- Cornus sericea (Red-osier Dogwood): "Edible"
- Trillium grandiflorum (Great White Trillium): "EDIBLE PARTS: Young, unfolding leaves HARVEST TIME: Only collect leaves from areas you know have NOT been trea..."
- Geranium maculatum (Wild Geranium): "Teas can be made from the plant"
- Asimina triloba (Pawpaw): "In late summer to early fall, pawpaw produces an edible, sweet, custard-like fruit 2.5 to 6 inches long."
- Morus rubra (Red Mulberry): "sweet, juicy, and can be eaten raw or made into pies, jellies, or jams."
- Vitis rotundifolia (Muscadine Grape): "Muscadine grapes are large and have thick skin but are good for eating and wine-making due to their sweet, pun..."
- Chamaecyparis thyoides (Atlantic White Cedar): "Edibility:                                                                    Edible"
- Capsicum chinense (Habanero Pepper): "Use these plants in the edible garden."
- Brassica oleracea var. gemmifera (Brussels Sprouts): "Round sprouts are edible."

## What this does not claim

The part is what the passage names, not a statement that the whole part is safe to eat; the condition the passage puts on eating it (cooked, ripe, in small amounts) and the hazards recorded beside it travel with the part on every row, read from the same passage by `toxicity.eating_line`. A food crop the toxicity table knows is named by the table's eaten part where its record has none (ADR 0009). No page was read for this pass, so a passage that was wrong about its plant stays wrong here; the quote and the url on every citation say where to look.


## To run it again

From `garden-gnome/`: `python scripts/catalog/mint_eaten_parts.py` rewrites the proposals and reports; `--write VERDICTS.json` writes the entries a verdicts file passes. The readers' run was a Workflow of two agents per proposal; its prompt is reproduced in the verdicts file's notes by what they answered. A new batch of records gets the same pass before its parts are minted.
