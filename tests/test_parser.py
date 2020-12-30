from unittest.mock import MagicMock

import flywheel
from flywheel_gear_toolkit import GearToolkitContext

from flywheel_hierarchy_curator.parser import parse_config


def test_parse_config():
    gear_context = MagicMock(spec=GearToolkitContext)
    gear_context.destination = {"id": "test"}
    gear_context.client.get_analysis.return_value = flywheel.AnalysisOutput(
        parent=flywheel.ContainerReference(type="subject", id="test12")
    )

    parse_config(gear_context)

    gear_context.client.get_analysis.assert_called_once_with("test")
    gear_context.client.get_subject.assert_called_once_with("test12")
    gear_context.get_input_path.called_count == 5
