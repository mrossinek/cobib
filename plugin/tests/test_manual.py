"""Test the integration of the plugin's man-pages."""

from cobib.man import manual


def test_man_pages() -> None:
    """Test the man-pages registration."""
    assert manual.index["cobib-dummy.1"] == "cobib_dummy.man"
    assert manual.index["cobib-dummy-importer.7"] == "cobib_dummy.man"
    assert manual.index["cobib-dummy-parser.7"] == "cobib_dummy.man"
    assert manual.index["cobib-plugin-dummy.7"] == "cobib_dummy.man"
    assert "P" in manual.sections[1]
    assert "cobib-dummy.1" in manual.sections[1]["P"]["plugin"]
    assert "cobib-dummy-importer.7" in manual.sections[7]["I"]["importers"]
    assert "cobib-dummy-parser.7" in manual.sections[7]["P"]["parsers"]
    assert "cobib-plugin-dummy.7" in manual.sections[7]["A"]["overview"]
