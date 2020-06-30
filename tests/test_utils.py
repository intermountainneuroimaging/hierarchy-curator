import sys
from pathlib import Path
from custom_curator.utils import load_converter

ROOT_DIR = Path(__file__).parents[1]


def test_load_converter_returns_module():
    assert "my_curator" not in sys.modules.keys()
    mod = load_converter(ROOT_DIR / "examples" / "my_curator.py")
    assert mod.filename == str(ROOT_DIR / "examples" / "my_curator.py")
    assert "my_curator" in sys.modules.keys()

    # Path as string
    sys.modules.pop("my_curator")
    assert "my_curator" not in sys.modules.keys()
    mod = load_converter(str(ROOT_DIR / "examples" / "my_curator.py"))
    assert mod.filename == str(ROOT_DIR / "examples" / "my_curator.py")
    assert "my_curator" in sys.modules.keys()

    # Returns None if path is corrupted
    mod = load_converter(str(ROOT_DIR / "doesnotexist.py"))
    assert mod is None
