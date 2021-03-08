#!/usr/bin/python3
"""Hierarchy Curator gear entrypoint."""
import logging

from flywheel_gear_toolkit import GearToolkitContext

from flywheel_hierarchy_curator import curate, parser

log = logging.getLogger(__name__)


if __name__ == "__main__":  # pragma: no cover
    with GearToolkitContext() as gear_context:
        gear_context.init_logging()
        parent, curator_path, input_files = parser.parse_config(gear_context)

        log.info(
            "Curating %s %s",
            parent.container_type,
            (parent.label or parent.code),
        )
        curate.main(
            gear_context,
            parent,
            curator_path,
            **input_files,
        )
