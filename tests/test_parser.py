from unittest.mock import MagicMock

import flywheel
import pytest
from flywheel_gear_toolkit import GearToolkitContext

from flywheel_hierarchy_curator.parser import parse_config


def test_parser():
    gc = MagicMock(spec=GearToolkitContext)
    gc.destination = {'id': 'test'}

    parent, curator_path, input_files = parse_config(gc)

    assert gc.get_input_path.call_count == 4
    gc.client.get_analysis.called_once_with('test')
