from app.data.expansion.disambiguate import (
    cultivar_of, disambiguated_name, plan_renames,
)


def test_cultivar_is_read_from_the_quoted_epithet():
    assert cultivar_of("Lycopersicon esculentum 'Sungold'") == "Sungold"
    assert cultivar_of("Salvia rosmarinus 'Tuscan Blue'") == "Tuscan Blue"


def test_an_apostrophe_inside_the_epithet_survives():
    # Greedy match anchored at the end — truncating this to "Chef" would be
    # worse than not renaming at all.
    assert cultivar_of("Lycopersicon esculentum 'Chef's Choice Orange'") == "Chef's Choice Orange"


def test_a_plain_species_has_no_cultivar():
    assert cultivar_of("Solanum lycopersicum") is None
    assert cultivar_of("Cyphomandra betacea") is None
    assert cultivar_of("") is None


def test_the_epithet_is_promoted_into_the_display_name():
    assert disambiguated_name("Tomato", "Lycopersicon esculentum 'Sungold'") == "Tomato 'Sungold'"


def test_a_row_that_already_names_its_cultivar_is_left_alone():
    assert disambiguated_name("Tomato 'Sungold'", "Lycopersicon esculentum 'Sungold'") is None


def test_a_species_without_a_cultivar_is_left_alone():
    assert disambiguated_name("Tomatoes", "Solanum lycopersicum") is None


# The real tomato rows, verbatim from the live catalog.
TOMATO_ROWS = [
    (76, "Tomatoes", "Solanum lycopersicum"),
    (642, "Tomato", "Lycopersicon esculentum 'Sungold'"),
    (840, "Tree Tomato", "Cyphomandra betacea"),
    (951, "Tomato", "Lycopersicon esculentum 'Big Beef'"),
    (952, "Tomato", "Lycopersicon esculentum 'Chef's Choice Orange'"),
    (953, "Tomato", "Lycopersicon esculentum 'Pink Girl'"),
    (954, "Tomato", "Lycopersicon esculentum 'Rapunzel'"),
]


def test_the_five_tomato_cultivars_become_tellable_apart():
    renames = plan_renames(TOMATO_ROWS)
    assert [(sid, new) for sid, _old, new in renames] == [
        (642, "Tomato 'Sungold'"),
        (951, "Tomato 'Big Beef'"),
        (952, "Tomato 'Chef's Choice Orange'"),
        (953, "Tomato 'Pink Girl'"),
        (954, "Tomato 'Rapunzel'"),
    ]


def test_the_curated_species_and_the_unrelated_plant_are_untouched():
    renamed_ids = {sid for sid, _o, _n in plan_renames(TOMATO_ROWS)}
    assert 76 not in renamed_ids   # Tomatoes, the curated row people mean
    assert 840 not in renamed_ids  # Tree Tomato is a different plant entirely


def test_a_cultivar_with_a_name_nobody_shares_is_left_alone():
    # Renaming here would add noise without resolving any ambiguity.
    rows = [(1, "Sungold Tomato", "Lycopersicon esculentum 'Sungold'")]
    assert plan_renames(rows) == []


def test_renaming_leaves_no_shared_names_among_the_tomatoes():
    renames = {sid: new for sid, _o, new in plan_renames(TOMATO_ROWS)}
    final = [renames.get(sid, common) for sid, common, _sci in TOMATO_ROWS]
    assert len(final) == len(set(final))
