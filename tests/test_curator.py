from pathlib import Path
import sys

from flywheel_hierarchy_curator.curate import main, get_curator, load_curator

ASSETS_DIR = Path(__file__).parent / "assets"


def test_get_curator(fw_project):
    client = None
    curator_path = ASSETS_DIR / "dummy_curator.py"
    curator = get_curator(client, curator_path, extra_arg="Test")
    assert curator.client == client
    assert curator.extra_arg == "Test"
    assert str(type(curator)) == "<class 'dummy_curator.Curator'>"


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
    mod = load_converter(str(ASSETS_DIR / "doesnotexist.py"))
    assert mod is None
