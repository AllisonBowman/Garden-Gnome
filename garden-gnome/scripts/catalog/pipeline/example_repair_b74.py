# Reference only: the b74 landing as run on 2026-09-10. Its S/OUT paths are that session's scratchpad.
"""Apply the b74 auditor-supplied repairs and write the landed batch file.

First landing to use repair_lib. The prose blocks below are the auditor's own
CORRECTED WORDING, used verbatim; the citation edits were each ground-truthed
against the live page with qc.py before being applied, because an auditor's
proposed substitute can itself be wrong -- this batch's auditor again claimed a
fifth NC State Plant Type value ("Woody Plant") that is really the start of the
next label, "Woody Plant Leaf Characteristics".
"""
import json
import sys

S = '/private/tmp/claude-501/-Users-allisonbowman-Developer-Garden-Gnome/d60fdf89-30e6-4ab2-9d58-640dbd475e1f/scratchpad'
OUT = 'app/data/verified/b74-native-shrubs-and-small-trees.json'
sys.path.insert(0, '/private/tmp/claude-501/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-database-build-goals-e548af/e53f91e1-ddb2-4d9f-8694-1b687525a69c/scratchpad')
from repair_lib import (CORR, cite, drop_audit, drop_cite, edit, finish,  # noqa: E402
                        replace_unknown, src_of, url_of)

res = json.load(open(f'{S}/b74_records.json'))
recs = {r['scientific_name_given']: r for r in res['records']}

# ------------------------------------------------------------- Salix discolor
r = recs['Salix discolor']
n, NC = url_of(r, 'ncsu.edu'), src_of(r, 'ncsu.edu')
rhs, RS = url_of(r, 'rhs.org.uk'), src_of(r, 'rhs.org.uk')
edit(r, "scientific_name_accepted: RHS's Name Status field value is Correct", claim=CORR)
cite(r, "scientific_name_accepted: RHS's page title names the binomial", RS, rhs,
     'Salix discolor | American glaucous willow')
edit(r, "name_note: RHS's plant profile subtitle and page title lead with American glaucous willow",
     claim="name_note: RHS's page title leads with American glaucous willow (the plant-profile subtitle beneath the H1 renders the same name)")
r['name_note'] = (
    "Sources split on the lead common name. RHS's page for this species (slug /plants/161035/salix-discolor/details, "
    "page title 'Salix discolor | American glaucous willow') leads with 'American glaucous willow' as its "
    "plant-profile subtitle and lists 'pussy willow' as the single entry under its separate Other common names field. "
    "NC State's page carries a single-entry Common Name(s) list, 'Pussy Willow,' matching its page-title parenthetical "
    "'(Pussy Willow),' and its description prose calls the species 'the American pussy willow or glaucous willow.' "
    "MoBot's page displays a single Common Name field reading 'pussy willow'; a longer common-names list exists only "
    "inside the info link's overlib attribute markup, so it is not quoted here. Two of the three dedicated pages (NC "
    "State, MoBot) lead with pussy willow, so that is used as common_name, with RHS's 'American glaucous willow' "
    "disclosed as the alternative. Distinct from Salix babylonica (Weeping Willow) and Salix nigra (Black Willow) "
    "already in this catalog, and from the European Salix caprea, which MoBot names as the goat willow.")
drop_audit(r)

# --------------------------------------------------------------- Ilex decidua
r = recs['Ilex decidua']
n, NC = url_of(r, 'ncsu.edu'), src_of(r, 'ncsu.edu')
rhs, RS = url_of(r, 'rhs.org.uk'), src_of(r, 'rhs.org.uk')
mo, MO = url_of(r, 'missouribotanicalgarden.org'), src_of(r, 'missouribotanicalgarden.org')
edit(r, "scientific_name_accepted: RHS's Name Status field value for Ilex decidua", claim=CORR)
cite(r, "scientific_name_accepted: RHS's page title names the binomial", RS, rhs, 'Ilex decidua | possum haw')
drop_cite(r, "name_note: Missouri Botanical Garden's Common Names popup")
edit(r, "common_name and name_note: NC State's body prose uses 'Possumhaw' as the name throughout, since the Common Name(s) list has five entries",
     claim="common_name and name_note: NC State's body prose uses Possumhaw as the name throughout")
cite(r, "name_note: RHS's page title leads with possum haw (the plant-profile subtitle beneath the H1 renders the same name)",
     RS, rhs, 'Ilex decidua | possum haw')
r['name_note'] = (
    "Naming converges on 'Possumhaw' across all three dedicated sources. NC State's Common Name(s) field carries five "
    "stacked entries — Possumhaw, Possum-haw, Possum Haw Holly, Possumhaw Holly, Swamp Holly — in the same order as "
    "the page-title parenthetical, and its first entry, 'Possumhaw,' is also the first name in that parenthetical; NC "
    "State's body prose then uses 'Possumhaw' throughout. Missouri Botanical Garden's displayed Common Name field "
    "carries the single value 'possumhaw,' and its prose reads 'Ilex decidua is a Missouri native, deciduous holly "
    "that is commonly called possum haw.' RHS's page is titled 'Ilex decidua | possum haw' and its profile header "
    "renders 'possum haw.' RHS additionally lists 'possum haw, winterberry' under Other common names; winterberry is "
    "the common name of the sibling species Ilex verticillata, already catalogued separately here, so this catalog "
    "does not carry it as a lead name for I. decidua. 'Possumhaw' is also applied elsewhere to Viburnum nudum, which "
    "this catalog lands as Smooth Witherod. Distinct from Ilex opaca (American Holly), Ilex crenata (Japanese Holly), "
    "Ilex vomitoria (Yaupon Holly) and Ilex glabra (Inkberry), also in this catalog.")
r['is_houseplant'] = False
edit(r, "is_houseplant: NC State's structured Plant Type field lists this as an outdoor woody native shrub/tree across ten USDA hardiness zones",
     claim="is_houseplant: NC State's structured Plant Type field values",
     quote='Native Plant\nPerennial\nShrub\nTree')
cite(r, "is_houseplant false: NC State's USDA Plant Hardiness Zone field", NC, n,
     '5a, 5b, 6a, 6b, 7a, 7b, 8a, 8b, 9a, 9b')
cite(r, "is_houseplant false: MoBot's Type field", MO, mo, 'Type: Deciduous shrub')
r['unknowns'].append(
    "is_houseplant false rests on NC State's Plant Type field, which carries exactly four values (Native Plant, "
    "Perennial, Shrub, Tree), plus its USDA Plant Hardiness Zone range and MoBot's Type field. The audit asked for a "
    "fifth Plant Type value, 'Woody Plant'; the live page does not carry one — that string begins NC State's next "
    "label, 'Woody Plant Leaf Characteristics', and a naive text scrape merges the two. The repair was declined, as "
    "the same claim was declined in b73.")
r['soil_base'] = 'garden_bed'
cite(r, "soil_base: NC State's structured Plant Type and USDA Plant Hardiness Zone fields place this as an in-ground woody landscape shrub or tree, not a container or potting-mix plant",
     NC, n, 'Native Plant\nPerennial\nShrub\nTree')
cite(r, "soil_base garden_bed corroboration: MoBot's Native Range field", MO, mo,
     'Native Range: Southeastern and central United States')
replace_unknown(r, "soil_base is set to garden_bed because this is an in-ground landscape shrub",
    "soil_base garden_bed rests on NC State's Plant Type and USDA Plant Hardiness Zone fields and MoBot's Type and "
    "Native Range fields; no admissible source frames this species as a container or potting-mix plant. The research "
    "record had parked this justification in unknowns with no citation naming the field, which is the wrong container "
    "for a populated value; citations were added at landing.")
drop_audit(r)

# ---------------------------------------------------------- Aesculus sylvatica
r = recs['Aesculus sylvatica']
n, NC = url_of(r, 'ncsu.edu'), src_of(r, 'ncsu.edu')
rhs, RS = url_of(r, 'rhs.org.uk'), src_of(r, 'rhs.org.uk')
mo, MO = url_of(r, 'mobot.org'), src_of(r, 'mobot.org')
edit(r, "scientific_name_accepted: RHS's Name Status field for this species reads Correct", claim=CORR)
edit(r, "common_name: RHS's page title for its dedicated single-species page reads Aesculus sylvatica | painted buckeye",
     claim="common_name: RHS's plant profile shows painted buckeye as the common name beneath the botanical name heading Aesculus sylvatica",
     quote='painted buckeye')
cite(r, "scientific_name_accepted: RHS's page title names the binomial", RS, rhs,
     'Aesculus sylvatica | painted buckeye')
drop_cite(r, "name_note: MoBot's Common Names tooltip lists painted buckeye and horse chestnut")
cite(r, "name_note: MoBot's Noteworthy Characteristics prose names both painted buckeye and dwarf buckeye", MO, mo,
     "Aesculus sylvatica, commonly called painted buckeye or dwarf buckeye, is a fast-growing, thicket forming, understory deciduous shrub (6-15') or small tree (to 30')")
cite(r, "name_note: MoBot explains the lead name", MO, mo,
     'Common name of painted buckeye is in reference to the purported resemblance of the upright flower clusters to a paint brush.')
r['name_note'] = (
    "NC State's Common Name(s) list gives two entries, Dwarf Buckeye then Painted Buckeye, in alphabetical order and "
    "in the same order as the page title's parenthetical; NC State's own body description prose nonetheless calls the "
    "species 'Painted buckeye' throughout, and never uses Dwarf Buckeye outside the title and the name list. Missouri "
    "Botanical Garden's Common Name field reads 'painted buckeye', its prose introduces the species as 'commonly "
    "called painted buckeye or dwarf buckeye' — so dwarf buckeye is not unique to NC State — and it explains the lead "
    "name: 'Common name of painted buckeye is in reference to the purported resemblance of the upright flower "
    "clusters to a paint brush.' RHS's plant profile shows 'painted buckeye' as the common name beneath the heading "
    "'Aesculus sylvatica'. A UGA CAES Field Report news article (not a dedicated species page) additionally calls the "
    "species Georgia buckeye. RHS treats the georgiana names as synonyms of this species on this species' own page, "
    "listing 'Aesculus x neglecta var. georgiana, Aesculus georgiana, Aesculus sylvatica ‘Georgiana’', so they are "
    "not a separate species for this record's purposes. Distinct from Aesculus glabra (Ohio Buckeye), Aesculus pavia "
    "(Red Buckeye) and Aesculus parviflora (Bottlebrush Buckeye) already in this catalog.")
replace_unknown(r, "RHS's page for a related name",
    "RHS lists Aesculus x neglecta var. georgiana, Aesculus georgiana and Aesculus sylvatica ‘Georgiana’ as synonyms "
    "of Aesculus sylvatica on this species' own page (taxon 88590, Name Status Correct), so the georgiana names are "
    "not a separate species for this record's purposes. The research record had flagged them as a sibling-species "
    "contamination risk; corrected on audit.")
edit(r, "toxic_to_pets: NC State's Problems tags list this species as a Problem for Cats and Problem for Dogs",
     quote='Poisonous to Humans\nProblem for Cats\nProblem for Dogs\nProblem for Horses')
edit(r, "toxicity_detail: RHS separately warns this plant is harmful to pets (dogs) if eaten and recommends wearing gloves",
     claim="toxicity_detail: RHS's Potentially harmful field in full",
     quote='Humans/Pets (dogs): harmful if eaten.  Wear gloves and other protective equipment when handling.  For further information and contact numbers regarding pets, see the HTA guide to potentially harmful plants')
cite(r, "toxicity_detail: NC State's Plant Type field carries the co-listed Poisonous trait", NC, n,
     'Native Plant\nPoisonous\nShrub\nTree')
cite(r, "toxicity_detail: NC State banners the severity at the top of the page", NC, n,
     'This plant has high severity poison characteristics.')
r['toxicity_detail'] = (
    "NC State rates this species Poison Severity 'High' under its human-scoped 'Poisonous to Humans' heading, with "
    "Poison Symptoms: \"Poisonous if ingested. Symptoms may include muscular weakness and paralysis, dilated pupils, "
    "vomiting, diarrhea, depression, paralysis, and stupor.\" The Poison Toxic Principle is \"Glycoside aesculin, "
    "saponin aesin, possibly alkaloids\", Causes Contact Dermatitis is \"No\", and the full Poison Part list is "
    "\"Bark / Flowers / Fruits / Leaves / Sap/Juice / Seeds / Stems\" — the whole plant, not the seeds alone. "
    "Separately from that human-scoped Poison block, NC State's Problems tags list this species as Poisonous to "
    "Humans, Problem for Cats, Problem for Dogs, and Problem for Horses, and its Plant Type traits include "
    "\"Poisonous\"; the page also banners \"This plant has high severity poison characteristics.\" RHS's own "
    "'Potentially harmful' field reads \"Humans/Pets (dogs): harmful if eaten. Wear gloves and other protective "
    "equipment when handling. For further information and contact numbers regarding pets, see the HTA guide to "
    "potentially harmful plants\". toxic_to_pets is true on NC State's cat- and dog-scoped Problems tags, with RHS's "
    "dog-scoped warning as corroboration. No admissible source states a numeric toxic dose.")
drop_audit(r)

# ------------------------------------------------------------- Lyonia lucida
r = recs['Lyonia lucida']
n, NC = url_of(r, 'ncsu.edu'), src_of(r, 'ncsu.edu')
rhs, RS = url_of(r, 'rhs.org.uk'), src_of(r, 'rhs.org.uk')
mo, MO = url_of(r, 'mobot.org'), src_of(r, 'mobot.org')
uf, UF = url_of(r, 'ifas.ufl.edu'), src_of(r, 'ifas.ufl.edu')
edit(r, "scientific_name_accepted: RHS's Name Status field value confirms the binomial as correct", claim=CORR)
edit(r, "scientific_name_accepted: RHS's H1 gives the botanical name for this species-specific page",
     claim="scientific_name_accepted: RHS's page title names the binomial", quote='Lyonia lucida | fetter bush')
edit(r, "name_note: RHS, a dedicated single-species page confirmed by URL slug and title, gives 'fetter bush' as its plant-profile subtitle and page title",
     claim="name_note: RHS's page title gives fetter bush (the plant-profile subtitle beneath the H1 renders the same name)")
edit(r, "name_note: NC State's Common Name(s) field is a stacked list of five entries matching the page-title parenthetical order",
     claim="name_note: NC State's Common Name(s) field is a five-entry alphabetized list, Fetterbush first, in the same order as the page-title parenthetical",
     quote='Fetterbush\nFetterbush Lyonia\nPink Fetterbush\nShining Fetterbush\nShinyleaf')
edit(r, "name_note: MoBot's rendered Common Name field carries a single value, 'fetter bush', with no separate Common Names tooltip/list control found on the fetched page",
     claim="name_note: MoBot's rendered Common Name field carries a single value, fetter bush")
cite(r, "name_note: MoBot's own body prose writes the name as one word", MO, mo,
     'Lyonia lucida, commonly known as fetterbush, is an evergreen shrub of the heath family.')
edit(r, "is_houseplant: NC State's USDA Plant Hardiness Zone field frames this as an outdoor landscape shrub",
     claim="is_houseplant: NC State's USDA Plant Hardiness Zone field", quote='7a, 7b, 8a, 8b, 9a, 9b')
edit(r, "toxic_to_pets: NC State's Problems tags list Problem for Cats and Problem for Dogs alongside Poisonous to Humans",
     claim="toxic_to_pets: NC State's Problems field values name both cats and dogs",
     quote='Poisonous to Humans\nProblem for Cats\nProblem for Children\nProblem for Dogs\nProblem for Horses')
edit(r, "toxicity_detail: NC State's Plant Type field carries the Poisonous tag",
     claim="toxicity_detail: NC State's Plant Type field carries the co-listed Poisonous trait",
     quote='Native Plant\nPerennial\nPoisonous\nShrub')
cite(r, "toxicity_detail: UF/IFAS carries a genus-level ingestion siting warning against planting near livestock", UF, uf,
     'Because many members of the genus Lyonia are poisonous, they should not be planted in or near areas used by livestock.')
r['name_note'] = (
    "Sources split on the lead spelling/form. NC State's page-title parenthetical and its Common Name(s) field carry "
    "the same five alphabetized entries (Fetterbush, Fetterbush Lyonia, Pink Fetterbush, Shining Fetterbush, "
    "Shinyleaf); the first entry, Fetterbush, matches the first name in the page title, and NC State's body prose "
    "opens with 'Fetterbush' as one word. UF/IFAS's dedicated Lyonia lucida publication (FOR 261/FR323) leads with "
    "'Fetterbush' in its title and gives 'Fetterbush, Shiny Lyonia' as its Common Names, tying 'shiny lyonia' to the "
    "leaf's shine. RHS's dedicated page gives its page title and plant-profile subtitle as 'fetter bush' (two words) "
    "and lists 'fetter bush, shiny lyonia' under Other common names. MoBot's Common Name field reads a single value, "
    "'fetter bush' (two words); a separate Common Names popup on the same page holds a two-entry list, but its text "
    "exists only in the link's overlib attribute markup, so it is not quoted here. MoBot's own body prose, however, "
    "writes it as one word: 'Lyonia lucida, commonly known as fetterbush, is an evergreen shrub of the heath family.' "
    "Given the one-word usage in NC State's, UF/IFAS's and MoBot's body prose, 'Fetterbush' was chosen as "
    "common_name, with 'fetter bush' (RHS and MoBot structured fields) and 'Shiny Lyonia' (RHS, UF/IFAS) noted as "
    "alternate forms. RHS applies 'fetter bush' to Eubotrys racemosa as well; that species lands in this same batch "
    "under a different name, and its own name_note records the overlap.")
r['toxicity_detail'] = (
    "NC State rates this species Poison Severity 'High' with Poison Symptoms: \"Signs of Toxicity occur usually "
    "within six hours of consuming the plant. Symptoms include lack of coordination, excessive salivation, abdominal "
    "pain, bloating, nausea, vomiting, diarrhea, headache, weakness, muscular spasms, watering of eyes and nose, slow "
    "pulse, colic, ataxia, depression, sweating, tingling of skin, convulsions, paralysis, coma, and sometimes even "
    "death. Toxicity in sheep, goats, cattle, and horses is most likely to occur in late winter or early spring when "
    "other forage is not available. Livestock are found down, unable to stand with their head weaving from side to "
    "side.\" The Poison Toxic Principle is \"Andromedotoxin, Grayanotoxins\", Causes Contact Dermatitis is \"No\", and "
    "the full Poison Part list is \"Flowers / Leaves / Sap/Juice\". NC State's Plant Type traits carry a co-listed "
    "\"Poisonous\" tag, and its Problems field names Poisonous to Humans, Problem for Cats, Problem for Children, "
    "Problem for Dogs and Problem for Horses — the basis for toxic_to_pets=true, since both cats and dogs are named. "
    "Disagreement to disclose: UF/IFAS's dedicated Lyonia lucida publication states the opposite for this species "
    "specifically — 'While many plants in the Lyonia genus are poisonous if ingested, Lyonia lucida is not known to "
    "be poisonous. However, many Lyonia spp. can cause irritation or a rash if sap comes into contact with the skin. "
    "Therefore, most Lyonia spp. are considered moderately to highly allergenic.' UF/IFAS nonetheless carries its own "
    "ingestion-scoped siting warning at genus level: 'Because many members of the genus Lyonia are poisonous, they "
    "should not be planted in or near areas used by livestock.' So UF/IFAS's species-level 'not known to be "
    "poisonous' sits alongside a genus-level ingestion caution and a genus-level skin/sap allergenicity caution; "
    "neither UF/IFAS caution is a cats/dogs claim. Its species-level statement conflicts directly with NC State's "
    "Poisonous designation and full Poison block for this species. Both are admissible, species-specific sources and "
    "they disagree on this species' basic toxicity status.")
drop_audit(r)

# --------------------------------------------------------- Leucothoe racemosa
r = recs['Leucothoe racemosa']
n, NC = url_of(r, 'ncsu.edu'), src_of(r, 'ncsu.edu')
edit(r, "toxic_to_pets is true and toxicity_detail is supported by NC State's Problems tag naming cats",
     claim="toxic_to_pets and toxicity_detail: NC State's Problems field values name both cats and dogs",
     quote='Problem for Cats\nProblem for Dogs\nProblem for Horses')
drop_cite(r, "toxic_to_pets is true and toxicity_detail is supported by NC State's Problems tag naming dogs")
edit(r, "toxicity_detail also carries NC State's co-listed Problems tag naming horses",
     claim="toxicity_detail: NC State's page tag list separately carries the same three animals as hashtags",
     quote='#problem for cats')
r['toxicity_detail'] = (
    "NC State Extension Gardener Plant Toolbox lists this species under its Problems field as three separate values: "
    "\"Problem for Cats\", \"Problem for Dogs\" and \"Problem for Horses\" (the page's tag list separately carries the "
    "same three as \"#problem for cats\", \"#problem for dogs\" and \"#problem for horses\"). NC State carries no "
    "Poisonous to Humans block for this species — no Poison Severity, Poison Symptoms, Poison Toxic Principle, Causes "
    "Contact Dermatitis or Poison Part field appears — so the Problems values are the only toxicity information the "
    "source gives, with no severity rating, symptom description, poison part or named toxic principle. toxic_to_pets "
    "is true on the cat- and dog-scoped values.")

# Landing decision (2026-09-10, second session): RHS's lead 'fetter bush' is the name Lyonia lucida lands under in this
# same batch, so this record takes NC State's lead instead -- a two-entry Common Name(s) list in page-title order whose
# first entry the body prose opens with (the b55 Senna rule).
r['common_name'] = 'Swamp Doghobble'
edit(r, "common_name is Fetter Bush, per RHS's plant-profile subtitle and page title for this species",
     claim="common_name: Swamp Doghobble is NC State's lead -- its two-entry Common Name(s) list is in page-title order and its body prose opens with the name",
     source=NC, url=n, quote='Swamp Doghobble is a 3 to 6-foot-tall deciduous shrub with alternate leaves.')
edit(r, "name_note: RHS's page title and subtitle lead with the common name fetter bush for this species",
     claim="name_note: RHS's page title leads with fetter bush (the plant-profile subtitle beneath the H1 renders the same name)")
edit(r, "soil_drainage is moderate per NC State's Soil Drainage field",
     claim="soil_drainage moderate: NC State's structured Soil Drainage field carries Good Drainage with Moist and Occasionally Wet (the structured-field rule from b64)",
     quote='Good Drainage')
replace_unknown(r, "water_regime: MoBot's own structured 'Water: Medium to wet' field is mid-scale",
    "water_regime: MoBot's structured field reads \"Water: Medium to wet\", the second-wettest band on MoBot's scale, which is "
    "consistent with keep_moist; the value rests on MoBot's Culture-section cultivation guidance (\"Grow in average, medium to "
    "wet, well-drained soils in part shade.\" and \"Prefers a moist, cool, acidic soil.\") together with \"Does not tolerate "
    "drought or windy conditions.\", which NC State's Description repeats in its own words.")
r['name_note'] = (
    "Sources split on the lead common name and on the genus. NC State's Common Name(s) field lists two entries, "
    "'Swamp Doghobble' and 'Sweetbells Leucothoe', in the same order as its page-title parenthetical, and its body prose "
    "opens with 'Swamp Doghobble', so that is NC State's lead. RHS's page title leads with 'fetter bush' (its plant-profile "
    "subtitle renders the same name) and MoBot's prose says 'commonly called fetter bush or sweetbells leucothoe'. "
    "'Swamp Doghobble' is the landed name because 'fetter bush' is also RHS's and MoBot's name for Lyonia lucida, which "
    "lands in this same batch as Fetterbush. On the genus: RHS's H1 is 'Eubotrys racemosa' with Name Status Correct, NC "
    "State's Previously Known As field gives 'Leucothoe racemosa', and MoBot states 'Synonymous with Leucothoe racemosa.', "
    "so the accepted name follows Eubotrys and the researched name is kept as scientific_name_given.")
r['unknowns'].append(
    "common_name researched as 'Fetter Bush' (RHS's lead); landed as 'Swamp Doghobble' (NC State's lead) because fetter "
    "bush is the name Lyonia lucida carries in the same batch.")
drop_audit(r)

# ------------------------------------------------------- Zenobia pulverulenta
r = recs['Zenobia pulverulenta']
n, NC = url_of(r, 'ncsu.edu'), src_of(r, 'ncsu.edu')
rhs, RS = url_of(r, 'rhs.org.uk'), src_of(r, 'rhs.org.uk')
mo, MO = url_of(r, 'missouribotanicalgarden.org'), src_of(r, 'missouribotanicalgarden.org')
edit(r, "scientific_name_accepted is confirmed by RHS's Name Status field value for this binomial", claim=CORR)
edit(r, "scientific_name_accepted 'Zenobia pulverulenta' matches RHS's H1 botanical name on its dedicated species page",
     claim="scientific_name_accepted: RHS's page title names the binomial", quote='Zenobia pulverulenta | dusty zenobia')
edit(r, "common_name 'Dusty Zenobia' is corroborated by RHS's dedicated single-species page, whose page title and subtitle name this common name",
     claim="common_name is corroborated by RHS's page title (the plant-profile subtitle beneath the H1 renders the same name)")
edit(r, "name_note: NC State's Common Name(s) field stacks three separate entries, so per that page it marks no primary by order alone",
     claim="name_note: NC State's Common Name(s) field lists three alphabetized entries, Dusty Zenobia first")
edit(r, "name_note: RHS's dedicated single-species page (its H1 botanical name and plant-profile subtitle) leads with 'dusty zenobia', supporting that name over the NC State list's raw order",
     claim="name_note: RHS's page title leads with dusty zenobia (the plant-profile subtitle beneath the H1 renders the same name)")
edit(r, "common_name is 'Dusty Zenobia' per NC State's own body prose, which leads with this name rather than the ordering of its stacked Common Name(s) list",
     claim="common_name: NC State's body prose leads with Dusty zenobia")
cite(r, "name_note: NC State's propagation prose also leads with the name", NC, n,
     'Dusty zenobia may not grow true from seed so propagatate it via softwood cuttings in early summer and layering or division in early spring')
r['name_note'] = (
    "All three sources lead with the same name. NC State's Common Name(s) list is alphabetized and its first entry, "
    "'Dusty Zenobia,' is also the first name in the page title's parenthetical; NC State's body prose uses 'Dusty "
    "zenobia' as its working name, in its description and again in its propagation advice. MoBot's single Common Name "
    "field gives 'dusty zenobia' and its Noteworthy Characteristics prose adds 'honey-cup' as an alternate. RHS's page "
    "heading is 'Zenobia pulverulenta' with 'dusty zenobia' as the plant-profile common name beneath it. 'Zenobia' "
    "alone is excluded as a lead because it mirrors the genus name and the genus is monotypic — MoBot states "
    "'Pulverulenta is the only species in the genus Zenobia.' No admissible source renders the exact string "
    "'Honeycup' (one word), the name this batch was researched under; NC State has 'Honey-cups' (hyphenated plural, "
    "second in its list) and MoBot has 'honey-cup' in prose only.")
r['unknowns'].append(
    "common_name researched as 'Honeycup'; landed as 'Dusty Zenobia', which all three dedicated pages lead with. No "
    "admissible source renders 'Honeycup' as one word.")
drop_audit(r)

# Generic: an NC State <dt> label glued to its <dd> value ("Light:\nDappled Sunlight ...") -- quote the value only,
# the shape every b74 audit prescribed. Poison-block labels are not in LABELS and stay as the page renders them.
import re as _re
from repair_lib import LABELS as _LABELS
for _r in res['records']:
    for _c in _r['citations']:
        if 'ncsu.edu' in _c['url'] and _re.match(_LABELS, _c['quote']):
            _label, _rest = _c['quote'].split(':', 1)
            _c['quote'] = _rest.lstrip('\n ')
            print(f"  stripped label {_label!r} from a {_r['common_name']} quote -> {_c['quote'][:50]!r}")

# Possumhaw's poison citation stacked five values from five fields; the page renders the block as label/value pairs in
# one contiguous run, the shape this catalog accepts for the Poison block alone (verify_quotes MISS otherwise).
_r = recs['Ilex decidua']
edit(_r, "toxicity_detail and toxic_to_pets: NC State's Poison block, rendered under the human-scoped 'Poisonous to Humans' heading",
     quote='Poison Severity:\nLow\nPoison Symptoms:\nMinor toxicity. Ingestion may cause vomiting, diarrhea, or other illness in humans.\nPoison Toxic Principle:\nSaponins\nCauses Contact Dermatitis:\nNo\nPoison Part:\nFruits')

NORMALIZATION = (
    "2026-09-10: b74 landed by a second session (branch claude/database-build-goals-e548af) from the loop session's own "
    "post-audit records and its half-written repair script, after that session stalled on a session limit at 09:56. Six "
    "native shrubs and small trees: Dusty Zenobia, Pussy Willow, Fetterbush, Swamp Doghobble, Possumhaw, Painted Buckeye. "
    "Auditor-supplied corrected wording used verbatim; the loop session had ground-truthed each citation substitute with "
    "qc.py (its auditor again offered 'Woody Plant' as a fifth Plant Type value; declined). Landing decisions here: "
    "Leucothoe racemosa lands as Swamp Doghobble, NC State's lead (a two-entry Common Name(s) list in page-title order "
    "that its prose opens with), because the 'fetter bush' RHS and MoBot lead with is the name Lyonia lucida carries in "
    "this same batch; three NC State label-glued quotes on Fetterbush (Light, Soil pH, Soil Drainage) trimmed to their "
    "values; Possumhaw's five-field poison quote re-quoted as the page's contiguous Poison block with its labels. "
    "verify_quotes: every reachable quote verified after repair; MoBot pages skipped from this machine (ConnectError).")
finish(res, OUT, NORMALIZATION, '/private/tmp/claude-501/-Users-allisonbowman-Developer-Garden-Gnome--claude-worktrees-database-build-goals-e548af/e53f91e1-ddb2-4d9f-8694-1b687525a69c/scratchpad/b74_landed_records.json')
