from pathlib import Path

import flywheel

from custom_curator.curate import main, get_curator

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
    assert project.label == "Curated"
    subject = project.subjects()[0]
    session = subject.sessions()[0]
    acquisition = session.acquisitions()[0]
    assert subject.label == "Curated"
    assert session.label == "Curated"
    assert acquisition.label == "Curated"
