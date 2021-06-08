"""Hierarchy curator main interface."""
import argparse
import logging
import sys
from pathlib import Path
import multiprocessing

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes, walker
from flywheel_gear_toolkit.utils.curator import get_curator, HierarchyCurator

sys.path.insert(0, str(Path(__file__).parents[1]))

log = logging.getLogger(__name__)


def main(
    context: GearToolkitContext,
    parent: datatypes.Container,
    curator_path: datatypes.PathLike,
    **kwargs
):
    """Curates a flywheel project using a curator.

    Args:
        context (GearToolkitContext): The flywheel gear toolkit context.
        project (flywheel.Project): The project to curate.
        curator_path (Path-like): A path to a curator module.
        kwargs (dict): Dictionary of attributes/value to set on curator.
    """
    curator = get_curator(context, curator_path, **kwargs)
    if curator.multi:
        def run_curate(queue: multiprocessing.Queue) -> None:
            container = queue.get()
            if curator.validate_container(container):
                curator.curate_container(container)

        queue = multiprocessing.Queue()
        num_cpus = multiprocessing.cpu_count()
        processes = []
        for _ in range(num_cpus):
            proc  = multiprocessing.Process(target=run_curate, args=(queue,))
            proc.start()
            processes.append(proc)

    # Curator specific configuration unpack
    config = curator.config

    project_walker = walker.Walker(
        parent,
        depth_first=config.depth_first,
        reload=config.reload,
        stop_level=config.stop_level
    )
    try:  # pragma: no cover
        if curator.multi:
            for container in project_walker.walk(callback=config.callback):
                queue.put((curator, container))
        else:
            for container in project_walker.walk(callback=config.callback):
                if curator.validate_container(container):
                    curator.curate_container(container)

    except Exception:  # pylint: disable=broad-except pragma: no cover
        log.error("Uncaught Exception", exc_info=True)
    
    if curator.multi:
        for proc in processes:
            proc.join()


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
    context = GearToolkitContext()
    context.client = client
    project = client.lookup(args.path)
    main(
        context,
        project,
        args.curator,
        additional_input_one=args.additional_input_one,
        additional_input_two=args.additional_input_two,
        additional_input_three=args.additional_input_three,
    )
