import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from flywheel_hierarchy_curator.curate import get_curator, load_curator, main

ASSETS_DIR = Path(__file__).parent / "assets"


def test_get_curator():
    client = None
    curator_path = ASSETS_DIR / "dummy_curator.py"
    curator = get_curator(client, curator_path, extra_arg="Test")
    assert curator.client == client
    assert curator.extra_arg == "Test"
    assert str(type(curator)) == "<class 'dummy_curator.Curator'>"


@pytest.mark.skip(reason="Import fw_project fixture from flywheel_Gear_toolkit")
@pytest.mark.usefixtures("fw_project")
def test_curate_main_with_a_dummy_curator(fw_project):
    client = None
    project = fw_project(n_subjects=1)
    curator_path = ASSETS_DIR / "dummy_curator.py"
    main(client, project, curator_path)
    subject = project.subjects()[0]
    session = subject.sessions()[0]
    acquisition = session.acquisitions()[0]
    assert project.reload().label == "Curated"
    assert subject.reload().label == "Curated"
    assert session.reload().label == "Curated"
    assert acquisition.reload().label == "Curated"


def test_load_curator_returns_module():
    # Path as pathlib.Path
    sys.modules.pop("dummy_curator", None)
    assert "dummy_curator" not in sys.modules.keys()
    mod = load_curator(ASSETS_DIR / "dummy_curator.py")
    assert mod.filename == str(ASSETS_DIR / "dummy_curator.py")
    assert "dummy_curator" in sys.modules.keys()

    # Path as string
    sys.modules.pop("dummy_curator")
    assert "dummy_curator" not in sys.modules.keys()
    mod = load_curator(str(ASSETS_DIR / "dummy_curator.py"))
    assert mod.filename == str(ASSETS_DIR / "dummy_curator.py")
    assert "dummy_curator" in sys.modules.keys()

    # Returns None if path is corrupted
    mod = load_curator(str(ASSETS_DIR / "doesnotexist.py"))
    assert mod is None


def test_get_curator_sets_arbitrary_kwargs():
    sys.modules.pop("dummy_curator", None)

    curator = get_curator(
        MagicMock(),
        str(ASSETS_DIR / "dummy_curator.py"),
        write_report=True,
        test="test",
        test2="test3",
    )

    assert curator.write_report == True
    assert curator.test == "test"
    assert curator.test2 == "test3"
