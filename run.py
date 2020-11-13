#!/usr/bin/env python
import logging

from flywheel_gear_toolkit import GearToolkitContext

from custom_curator import curate
from custom_curator.parser import parse_config

log = logging.getLogger(__name__)


if __name__ == "__main__":
    with GearToolkitContext() as gear_context:
        gear_context.init_logging(
            default_config_name=(
                "debug" if gear_context.config.get("verbose") else "info"
            )
        )
        parent, curator_path, input_files = parse_config(gear_context)
        log.info(f"Curating {parent.container_type} {parent.label or parent.code}")
        curate.main(
            gear_context.client,
            parent,
            curator_path,
            gear_context.config.get("write_report"),
            **input_files,
        )
