"""Hierarchy curator main interface."""
import argparse
import logging
import math
import sys
from pathlib import Path
import multiprocessing

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import datatypes, walker, reporters, curator as c

sys.path.insert(0, str(Path(__file__).parents[1]))

log = logging.getLogger(__name__)

def worker(curator, children):
    if curator.config.depth_first:
        for child in children:
            w = walker.Walker(
                child,
                depth_first=curator.config.depth_first,
                reload=curator.config.reload,
                stop_level=curator.config.stop_level
            )
            for container in w.walk(callback=curator.config.callback) :
                try:
                    if curator.validate_container(container):
                        curator.curate_container(container)
                except Exception:  # pylint: disable=broad-except pragma: no cover
                    log.error("Uncaught Exception", exc_info=True)

    else:
        first_elem = children.pop(0)
        w = walker.Walker(
            first_elem,
            depth_first=curator.config.depth_first,
            reload=curator.config.reload,
            stop_level=curator.config.stop_level
        )
        if children:
            w.extend(children)
        for container in w.walk(callback=curator.config.callback) :
            try:
                if curator.validate_container(container):
                    curator.curate_container(container)
            except Exception:  # pylint: disable=broad-except pragma: no cover
                log.error("Uncaught Exception", exc_info=True)
                


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
    # Initialize curator
    curator = c.get_curator(context, curator_path, **kwargs)
    # Initialize walker from root container
    root_walker = walker.Walker(
        parent,
        depth_first=curator.config.depth_first,
        reload=curator.config.reload,
        stop_level=curator.config.stop_level
    )
    # Initialize reporter if in config
    if curator.config.report:
        curator.reporter = reporters.AggregatedReporter(
            curator.config.path,
            format=curator.config.format,
            multi=curator.config.multi
        )
    if curator.config.multi:
        run_multiproc(curator, root_walker)
    else:
        for container in root_walker.walk(callback=curator.config.callback) :
            try:
                if curator.validate_container(container):
                    curator.curate_container(container)
            except Exception:  # pylint: disable=broad-except pragma: no cover
                log.error("Uncaught Exception", exc_info=True)

def run_multiproc(curator, root_walker):
    # Main multiprocessing entrypoint
    workers = curator.config.workers
    queue = multiprocessing.Queue()
    if curator.reporter:
        # Logger process
        r = curator.reporter
        logger = multiprocessing.Process(
            target=reporters.worker,
            args=(queue, r.output_path, r.output_type, r.writer_fn)
        )
        logger.start()
    # Start by curating first container, then init workers on children
    root = root_walker.next()
    children = list(root_walker.deque)
    children_per_worker = math.ceil(len(children) / workers)
    # Worker processes
    worker_ps = []
    while len(children):
        containers = children[:children_per_worker]
        children = children[children_per_worker:]
        proc = multiprocessing.Process(target=worker, args=(curator, containers))
        proc.start()
        worker_ps.append(proc)
    for proc in worker_ps:
        proc.start()
    for proc in worker_ps:
        proc.join()
    if curator.reporter:
        curator.reporter.write('END')



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

