"""Hierarchy curator main interface."""
import argparse
import copy
import logging
import math
import multiprocessing
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import curator as c
from flywheel_gear_toolkit.utils import datatypes, reporters, walker

from .utils import (
    container_from_pickleable_dict,
    container_to_pickleable_dict,
    handle_container,
    make_walker,
)

sys.path.insert(0, str(Path(__file__).parents[1]))
log = logging.getLogger(__name__)


def worker(curator, work, lock, worker_id):
    # breakpoint()
    try:
        local_curator = copy.deepcopy(curator)
        local_curator.context._client = local_curator.context.get_client()
        local_curator.lock = lock
        log = logging.getLogger(f"{__name__} - Worker {worker_id}")
        if local_curator.config.depth_first:
            for child in work:
                child_cont = container_from_pickleable_dict(child, local_curator)
                w = make_walker(child_cont, local_curator)
                for cont in w.walk(callback=local_curator.config.callback):
                    if local_curator.validate_container(cont):
                        local_curator.curate_container(cont)
        else:
            containers = [
                container_from_pickleable_dict(w, local_curator) for w in work
            ]
            w = make_walker(containers.pop(0), local_curator)
            if work:
                w.add(containers)
            for cont in w.walk(callback=local_curator.config.callback):
                if local_curator.validate_container(cont):
                    local_curator.curate_container(cont)
    except Exception as e:  # pylint: disable=broad-except
        log.critical("Could not finish curation, worker errored early", exc_info=True)


def main(
    context: GearToolkitContext,
    parent: datatypes.Container,
    curator_path: datatypes.PathLike,
    **kwargs,
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
    log.info("Curator config: " + str(curator.config))
    # Initialize walker from root container
    root_walker = walker.Walker(
        parent,
        depth_first=curator.config.depth_first,
        reload=curator.config.reload,
        stop_level=curator.config.stop_level,
    )
    # Initialize reporter if in config
    if curator.config.report:
        curator.reporter = reporters.AggregatedReporter(
            curator.config.path,
            format=curator.config.format,
            multi=curator.config.multi,
        )
    if curator.config.multi:
        run_multiproc(curator, root_walker)
    else:
        for container in root_walker.walk(callback=curator.config.callback):
            try:
                if curator.validate_container(container):
                    curator.curate_container(container)
            except Exception:  # pylint: disable=broad-except pragma: no cover
                log.error("Uncaught Exception", exc_info=True)


def run_multiproc(curator, root_walker):
    # Main multiprocessing entrypoint
    lock = multiprocessing.Lock()
    workers = curator.config.workers
    if curator.reporter:
        # Logger process
        reporter = curator.reporter
        reporter.start()
        log.info("Initialized reporting process")
    distributions = [[] for _ in range(workers)]
    # Curate first container
    parent_cont = root_walker.next(callback=curator.config.callback)
    parent_cont = container_to_pickleable_dict(parent_cont)
    handle_container(curator, parent_cont)
    # Populate assignments
    for i, child_cont in enumerate(root_walker.deque):
        distributions[i % workers].append(container_to_pickleable_dict(child_cont))
    worker_ps = []
    for i in range(workers):
        # Give each worker its assignments
        log.info(f"Initializing Worker {i}")
        proc = multiprocessing.Process(
            target=worker, args=(curator, distributions[i], lock, i), name=str(i)
        )
        proc.start()
        worker_ps.append(proc)
    for worker_p in worker_ps:
        worker_p.join()
        log.info(f"Worker {worker_p.name} finished with exit code: {worker_p.exitcode}")

    # breakpoint()
    if curator.reporter:
        curator.reporter.write("END")
        curator.reporter.join()


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
