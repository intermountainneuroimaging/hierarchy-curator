#!/usr/bin/env python
import logging

from flywheel_gear_toolkit import GearToolkitContext

from custom_curator import curate
from custom_curator.parser import parse_config

log = logging.getLogger(__name__)


if __name__ == "__main__":
    with GearToolkitContext() as gear_context:
        gear_context.init_logging()
        project, curator_path, input_files = parse_config(gear_context)
        log.info("Curating project %s", project.label)
        curate.main(gear_context.client, project, curator_path, **input_files)
