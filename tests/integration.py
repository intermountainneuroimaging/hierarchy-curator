from pathlib import Path
from unittest.mock import MagicMock

import flywheel
from flywheel_gear_toolkit import GearToolkitContext

from flywheel_hierarchy_curator import curate, parser

GROUP = "scien"
PROJECT = "Nate-BIDS-test"
CURATOR = (Path(".") / "examples/test_file_basic.py").resolve()

# Note: only for local testing, set the above variables to be a
# project you have access to
def test_integration(mocker):
    fw = flywheel.Client()
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.client = fw

    parent, curator_path, input_files = parser.parse_config(gear_context)

    parent = fw.lookup(f"{GROUP}/{PROJECT}")

    curate.main(gear_context, parent, str(CURATOR))
