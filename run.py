#!/usr/bin/python3
"""Hierarchy Curator gear entrypoint."""
from flywheel_gear_toolkit import GearToolkitContext

from fw_gear_hierarchy_curator import curate, parser


if __name__ == "__main__":  # pragma: no cover
    with GearToolkitContext() as gear_context:
        gear_context.init_logging()
        parent, curator_path, input_files = parser.parse_config(gear_context)

        curate.main(
            gear_context,
            parent,
            curator_path,
            **input_files,
        )
