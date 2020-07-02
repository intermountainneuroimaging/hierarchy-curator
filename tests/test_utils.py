from pathlib import Path
import sys

from custom_curator.utils import load_converter

ASSETS_DIR = Path(__file__).parent / "assets"


def test_load_converter_returns_module():
    sys.modules.pop("dummy_curator", None)
    assert "dummy_curator" not in sys.modules.keys()
    mod = load_converter(ASSETS_DIR / "dummy_curator.py")
    assert mod.filename == str(ASSETS_DIR / "dummy_curator.py")
    assert "dummy_curator" in sys.modules.keys()

    # Path as string
    sys.modules.pop("dummy_curator")
    assert "dummy_curator" not in sys.modules.keys()
    mod = load_converter(str(ASSETS_DIR / "dummy_curator.py"))
    assert mod.filename == str(ASSETS_DIR / "dummy_curator.py")
    assert "dummy_curator" in sys.modules.keys()

    # Returns None if path is corrupted
    mod = load_converter(str(ASSETS_DIR / "doesnotexist.py"))
    assert mod is None
