from osdagbridge.core.bridge_types.plate_girder.initial_sizing import steel_i_section_properties


def test_steel_i_section_properties_are_consistent():
    props = steel_i_section_properties(
        D=1000,
        bf_top=300,
        tf_top=20,
        bf_bot=300,
        tf_bot=20,
        tw=12,
    )

    assert props["member_properties.girder_details.section_input.web_depth"] == 960
    assert props["member_properties.girder_details.section_properties.area"] > 0
    assert props["member_properties.girder_details.section_properties.iz"] > 0
