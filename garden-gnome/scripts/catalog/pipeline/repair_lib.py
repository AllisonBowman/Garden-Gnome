"""Shared landing helpers for the catalog batches.

Each bNN_repair.py imports these, applies its per-species repairs, then calls
finish(). Factored out at b74 so a landing script is only the repairs, and so a
fix to a generic pass reaches every later batch instead of being re-typed.
"""
import html
import json
import re

SCHEMA_FIELDS = (
    'common_name', 'scientific_name_given', 'scientific_name_accepted', 'name_note', 'is_houseplant',
    'toxic_to_pets', 'toxicity_detail', 'chill_damage_f', 'cool_rest_note', 'day_f_min', 'day_f_max',
    'night_f_min', 'night_f_max', 'humidity_need', 'humidity_pct_min', 'humidity_pct_max', 'light_fc_min',
    'light_fc_good', 'direct_sun_hours_max', 'outdoor_sun_exposure', 'soil_base', 'soil_drainage',
    'soil_ph_min', 'soil_ph_max', 'water_regime', 'water_dry_down_target', 'water_check_depth_cm',
    'water_growing_days_est', 'water_dormant_days_est', 'water_estimate_basis', 'fertilize_interval_days',
    'fertilize_active_months', 'fertilize_strength',
)

CORR = ("scientific_name_accepted corroborated by RHS's Botanical Details Name Status row, "
        "whose value reads Correct")

BANNED_CLAIM = (
    'own convention', 'three or more entries', 'no primary', 'no single primary', "per this catalog's rule",
    'UK-calibrated', 'dedicated single-species factsheet', 'rendered bullets', 'tooltip', 'popup', 'marks no',
    'marked as primary', 'marked primary', 'ordering artifact',
)
BANNED_NOTE = (
    'own convention', 'three or more entries', 'no single primary', 'marks no primary', 'per the task',
    'UK-calibrated', 'rendered bullets', 'designates no primary', 'no primary marked', "per this catalog's rule",
    'working title', 'ordering artifact',
)
# A quote must be a field's VALUE, never its label glued to the value. The Poison
# block is the exception the pages themselves render as one contiguous run.
LABELS = (r'^(Common Name\(s\)|Plant Type|Soil Drainage|Soil pH|Problems|USDA Plant Hardiness Zone|Light|'
          r'Landscape Location|Landscape Theme|Position|Soil Texture|Edibility|Habit/Form|Sun|Water):')


def drop_audit(r):
    r['unknowns'] = [u for u in (r.get('unknowns') or []) if ' on audit' not in u]


def cite(r, claim, source, url, quote):
    r['citations'].append({'claim': claim, 'source': source, 'url': url, 'quote': quote})


def edit(r, startswith, **kw):
    hits = [c for c in r['citations'] if c['claim'].startswith(startswith)]
    assert len(hits) == 1, (r['common_name'], startswith, len(hits))
    hits[0].update(kw)


def drop_cite(r, startswith):
    before = len(r['citations'])
    r['citations'] = [c for c in r['citations'] if not c['claim'].startswith(startswith)]
    assert len(r['citations']) == before - 1, (r['common_name'], startswith)


def url_of(r, part):
    for c in r['citations']:
        if part in c['url']:
            return c['url']
    raise KeyError((r['common_name'], part))


def src_of(r, part):
    for c in r['citations']:
        if part in c['url']:
            return c['source']
    raise KeyError((r['common_name'], part))


def replace_unknown(r, startswith, new):
    hits = [i for i, u in enumerate(r['unknowns']) if u.startswith(startswith)]
    assert len(hits) == 1, (r['common_name'], startswith, len(hits))
    if new is None:
        del r['unknowns'][hits[0]]
    else:
        r['unknowns'][hits[0]] = new


def title_ok(name):
    """Title-case check that survives apostrophes: Lizard's Tail, not Lizard'S Tail."""
    return name == ' '.join(w[0].upper() + w[1:] for w in name.split() if w)


def generic_passes(records):
    """The defect classes every batch has repeated. Assertions, not silent fixes."""
    for r in records:
        for c in r['citations']:
            c['quote'] = html.unescape(c['quote']).replace('\xa0', ' ')
            cl = c['claim']
            if (' | ' in c['quote'] and 'subtitle' in cl and 'beneath the H1' not in cl
                    and 'page title' not in cl and 'page header' not in cl):
                cl = cl.replace('subtitle', 'page title (the plant-profile subtitle beneath the H1 renders the same name)')
            cl = (cl.replace('Light Requirements field', 'Light field')
                    .replace('Light Requirements list', 'Light field values')
                    .replace('Landscape Uses field', 'Landscape Location field'))
            c['claim'] = cl
            q, who = c['quote'], r['common_name']
            assert not re.search(r'<[A-Za-z/]', q), (who, 'markup in quote', q[:80])
            assert '&bull;' not in q and '•' not in q, (who, 'tooltip bullets', q[:80])
            assert '|#' not in q, (who, 'tag-run quote', q[:80])
            assert not q.endswith(' | North Carolina Extension Gardener Plant Toolbox'), (who, 'title suffix', q[:80])
            assert not q.endswith('..'), (who, 'stray separator', q[-60:])
            # MoBot renders "Sun: Part shade" / "Water: Medium" as one text node (auditor-verified in b74), and the
            # corpus quotes that form in 60+ files; the label check is for NC State's <dt>/<dd> pairs. Penn State's
            # Site Conditions list and UMD Extension's fact paragraph do the same -- one <li>/<p> holding
            # "<strong>Sun:</strong>&nbsp;Full sun to light shade." (both re-read from the raw HTML at b76).
            inline_label = any(h in c['url'] for h in (
                'mobot.org', 'missouribotanicalgarden.org', 'extension.psu.edu', 'extension.umd.edu'))
            assert inline_label or not re.match(LABELS, q), (who, 'label+value concat', q[:60])
            for bad in BANNED_CLAIM:
                assert bad not in cl, (who, 'banned claim phrase', bad, cl[:90])
            assert not ('rhs.org.uk' in c['url'] and '/wd/' in c['url']), (who, 'RHS wd slug', c['url'])
        for k, v in list(r.items()):
            if v == 'null' or v == '':
                r[k] = None
        for k in ('name_note', 'toxicity_detail'):
            if r.get(k):
                for bad in BANNED_NOTE:
                    assert bad not in r[k], (r['common_name'], k, 'banned note phrase', bad)
        for u in r['unknowns']:
            assert ' on audit:' not in u, (r['common_name'], 'audit line survived', u[:60])
        assert title_ok(r['common_name']), (r['common_name'], 'not title case')
        assert len(r['scientific_name_given'].split()) == 2, r['scientific_name_given']
        acc = r.get('scientific_name_accepted')
        assert acc is None or (len(acc.split()) == 2 and acc.split()[1].islower()), (r['common_name'], acc)
        # b74 (all landscape shrubs) asserted False outright; b75 carries a carnivorous plant NC State says "can also
        # be grown indoors", as b45's Cape Sundew and Purple Pitcher Plant already do. True is allowed only when a
        # citation labelled is_houseplant quotes an indoor/houseplant framing; null is never allowed.
        house = r['is_houseplant']
        assert house is False or (house is True and any(
            'is_houseplant' in c['claim'] and re.search(r'indoor|houseplant', c['quote'], re.I)
            for c in r['citations'])), (r['common_name'], 'is_houseplant', house)
        for f in SCHEMA_FIELDS:
            if f == 'scientific_name_given' or r.get(f) is None:
                continue
            assert any(f in c['claim'] for c in r['citations']), (r['common_name'], 'uncited field', f)
    names = [r['common_name'].lower().replace(' ', '') for r in records]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, ('common_name collision inside batch', dupes)


def finish(res, out_path, normalization, scratch_path=None):
    generic_passes(res['records'])
    landed = {'batch': res['batch'], 'records': res['records'],
              'audit_summary': res['audit_summary'], 'normalizations': [normalization]}
    json.dump(landed, open(out_path, 'w'), indent=2, ensure_ascii=False)
    if scratch_path:
        json.dump(res, open(scratch_path, 'w'), indent=1, ensure_ascii=False)
    print('wrote', out_path)
    for r in res['records']:
        print(f"{r['common_name']:26s} acc={r['scientific_name_accepted']} house={r['is_houseplant']} "
              f"toxic={r['toxic_to_pets']} sun={r['outdoor_sun_exposure']} drain={r['soil_drainage']} "
              f"water={r['water_regime']} ph={r['soil_ph_min']}/{r['soil_ph_max']} base={r['soil_base']} "
              f"cites={len(r['citations'])} unk={len(r['unknowns'])}")
