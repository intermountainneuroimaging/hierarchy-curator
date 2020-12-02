#!/usr/bin/env python
import logging

from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import install_requirements

from flywheel_hierarchy_curator import curate, parser

log = logging.getLogger(__name__)


if __name__ == "__main__":
    with GearToolkitContext() as gear_context:
        gear_context.init_logging(
            default_config_name=(
                "debug" if gear_context.config.get("verbose") else "info"
            )
        )
        parent, curator_path, input_files, optional_requirements = parser.parse_config(
            gear_context
        )

        if optional_requirements:
            log.info(f"Installing requirements from {optional_requirements}")
            install_requirements(optional_requirements)

        log.info(f"Curating {parent.container_type} {parent.label or parent.code}")
        curate.main(
            gear_context,
            parent,
            curator_path,
            write_report=gear_context.config.get("write_report"),
            **input_files,
        )
