"""Hierarchy curator main interface."""
import argparse
import logging

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes, walker
from flywheel_gear_toolkit.utils.curator import get_curator

log = logging.getLogger(__name__)


def main(
    context: GearToolkitContext,
    parent: datatypes.Container,
    curator_path: datatypes.PathLike,
    **kwargs
):
    """Curates a flywheel project using a curator.

    Args:
        client (flywheel.Client): The flywheel sdk client.
        project (flywheel.Project): The project to curate.
        curator_path (Path-like): A path to a curator module.
        kwargs (dict): Dictionary of attributes/value to set on curator.
    """
    curator = get_curator(context, curator_path, **kwargs)

    project_walker = walker.Walker(parent, depth_first=curator.depth_first)
    try:  # pragma: no cover
        for container in project_walker.walk():
            curator.curate_container(container)  # Tested in gear toolkit
    except Exception:  # pylint: disable=broad-except pragma: no cover
        log.error("Uncaught Exception", exc_info=True)
        curator.__del__()


if __name__ == "__main__":  # pragma: no cover
    parser = argparse.ArgumentParser(description="Argument parser for curation")
    parser.add_argument(
        "--api-key",
        default=None,
        help="Pass in api key if not logged in with cli",
    )
    parser.add_argument(
        "--curator", "-c", required=True, help="path to curator implementation"
    )
    parser.add_argument("--additional-input-one", help="Input file one")
    parser.add_argument("--additional-input-two", help="Input file two")
    parser.add_argument("--additional-input-three", help="Input file three")
    parser.add_argument("path", help="The resolver path to the project")

    args = parser.parse_args()
    client = flywheel.Client(args.api_key)
    project = client.lookup(args.path)
    main(
        client,
        project,
        args.curator,
        additional_input_one=args.input_file_one,
        additional_input_two=args.input_file_two,
        additional_input_three=args.input_file_three,
    )
