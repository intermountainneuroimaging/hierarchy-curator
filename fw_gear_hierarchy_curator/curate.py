"""Hierarchy curator main interface."""
import argparse
import copy
import functools
import logging
import multiprocessing
import sys
import typing as t
from pathlib import Path

import flywheel

# import multiprocessing_logging
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import curator as c
from flywheel_gear_toolkit.utils import datatypes, reporters, walker

from .utils import container_to_pickleable_dict, handle_work, make_walker

sys.path.insert(0, str(Path(__file__).parents[1]))
# multiprocessing_logging.install_mp_handler()
log = logging.getLogger(__name__)


def handle_depth_first(
    log: logging.Logger,
    local_curator: c.HierarchyCurator,
    containers: t.List[datatypes.Container],
) -> None:
    """For each container create a walker and walk if it has children.
    Otherwise, just curate.
    """
    for container in containers:
        if container.container_type in ["analysis", "file"]:
            if local_curator.validate_container(container):
                local_curator.curate_container(container)
        else:
            w = make_walker(container, local_curator)
            for cont in w.walk(callback=local_curator.config.callback):
                log.debug(f"Found {cont.container_type}, ID: {cont.id}")
                if local_curator.validate_container(cont):
                    local_curator.curate_container(cont)


def handle_breadth_first(
    log: logging.Logger,
    local_curator: c.HierarchyCurator,
    containers: t.List[datatypes.Container],
) -> None:
    """Add all containers to one walker and walk in breadth-first."""
    w = make_walker(containers.pop(0), local_curator)
    if containers:
        w.add(containers)
    for cont in w.walk(callback=local_curator.config.callback):
        log.debug(f"Found {cont.container_type}, ID: {cont.id}")
        if local_curator.validate_container(cont):
            local_curator.curate_container(cont)


def worker(
    curator: c.HierarchyCurator,
    work: t.List[t.Dict[str, str]],
    lock: multiprocessing.Lock,
    worker_id: int,
) -> None:
    """Target function for Process.

    Args:
        curator: Curator object
        work: List of dictionaries representing containers to process.
        lock: multiprocessing lock to pass into container.
        worker_id: id of worker.
    """
    log = logging.getLogger(f"{__name__} - Worker {worker_id}")
    try:
        # Use custom __deepcopy__ hook to copy relevant data, remove
        # unpickleable attributes, and re-populate.
        local_curator = copy.deepcopy(curator)
        local_curator.context._client = local_curator.context.get_client()
        local_curator.lock = lock
        if local_curator.config.depth_first:
            # Pass work, curator, and handle_depth_first into handle_work
            handle_work(work, local_curator, functools.partial(handle_depth_first, log))
        else:
            # Pass work, curator, and handle_breadth_first into handle_work
            handle_work(
                work, local_curator, functools.partial(handle_breadth_first, log)
            )
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
    log.info(f"Getting curator from {curator_path}")
    curator = c.get_curator(context, curator_path, **kwargs)
    log.info("Curator config: " + str(curator.config))
    # Initialize walker from root container
    log.info(
        "Initializing walker over hierarchy starting at "
        f"{parent.container_type} {parent.label or parent.code}"
    )
    root_walker = walker.Walker(
        parent,
        depth_first=curator.config.depth_first,
        reload=curator.config.reload,
        stop_level=curator.config.stop_level,
    )
    start_multiproc(curator, root_walker)


# See docs/multiprocessing.md for details on why this implementation was chosen
def start_multiproc(curator, root_walker):
    """Run hierarchy curator in parallel.

    1. Set up
    2. Curate root container
    3. Divide children of root container evenly among workers
    4. Run each worker process
    5. Clean up
    """
    # Main multiprocessing entrypoint
    log.info(f"Running in multi-process mode with {curator.config.workers} workers")
    lock = multiprocessing.Lock()
    workers = curator.config.workers
    reporter_proc = None
    # Initialize reporter if in config
    if curator.config.report:
        manager = multiprocessing.Manager()
        curator.reporter = reporters.AggregatedReporter(
            curator.config.path, format=curator.config.format, queue=manager.Queue()
        )
        # Logger process
        reporter_proc = multiprocessing.Process(
            target=curator.reporter.worker,
        )
        reporter_proc.start()
        log.info("Initialized reporting process")
    distributions = [[] for _ in range(workers)]
    # Curate first container
    log.debug("Curating root container")
    parent_cont = root_walker.next(callback=curator.config.callback)
    if curator.validate_container(parent_cont):
        curator.curate_container(parent_cont)
    log.info(f"Assigning work to each worker process.")
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
    # Block until each process has completed
    for worker_p in worker_ps:
        worker_p.join()
        log.info(f"Worker {worker_p.name} finished with exit code: {worker_p.exitcode}")
    # If a reporter was instantiated, send it the termination signal.
    if reporter_proc:
        curator.reporter.write("END")
        reporter_proc.join()


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
