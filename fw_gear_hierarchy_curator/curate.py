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

sys.path.insert(0, str(Path(__file__).parents[1]))
log = logging.getLogger(__name__)


def worker(curator, queue, lock):
    local_curator = copy.deepcopy(curator)
    local_curator.context._client = local_curator.context.get_client()
    locak_curator.lock = lock
    while True:
        val = queue.get()
        if val is None:
            log.debug("Recieved termination signal")
            break
        try:
            get_container_fn = getattr(
                local_curator.context.client, f"get_{val['container_type']}"
            )
            container = get_container_fn(val["id"])
        except flywheel.rest.ApiException as e:
            log.error(e)
        if local_curator.validate_container(container):
            local_curator.curate_container(container)


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
        reload=(curator.config.reload if not curator.config.multi else False),
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
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    lock = multiprocessing.Lock()
    workers = curator.config.workers
    if curator.reporter:
        # Logger process
        reporter = curator.reporter
        reporter.start()
        log.info("Initialized logging process")
    worker_ps = []
    for i in range(workers):
        proc = multiprocessing.Process(
            target=worker, args=(curator, queue, lock), name=f"worker-{i}"
        )
        proc.start()
        worker_ps.append(proc)
    for container in root_walker.walk(callback=curator.config.callback):
        # log.debug(f'Found {container.container_type}, ID: {container.id}')

        val = {
            "id": container.id,
            "container_type": container.container_type,
        }
        if container.container_type == "file":
            if hasattr(container, "file_id"):
                val["id"] = container.file_id
            val["parent_type"] = container.parent.id
            val["parent_id"] = container.parent.container_type
        queue.put(val)
    for i in range(workers):
        queue.put(None)
    for worker_p in worker_ps:
        worker_p.join()
        log.info(f"Worker {worker_p.name} finished with exit code: {worker_p.exitcode}")

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
