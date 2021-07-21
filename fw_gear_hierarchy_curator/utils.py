"""Utilities for running the curator."""

import logging
import typing as t

import flywheel
from flywheel_gear_toolkit.utils import curator as c
from flywheel_gear_toolkit.utils import datatypes, reporters, walker

log = logging.getLogger(__name__)


def container_to_pickleable_dict(container: datatypes.Container) -> t.Dict[str, str]:
    """Take a flywheel container and transform into
    a simple dictionary that can be pickled for
    multiprocessing.
    """
    log.debug(f"Found {container.container_type}, ID: {container.id}")
    val = {
        "id": container.id,
        "container_type": container.container_type,
    }
    if container.container_type == "file":
        if hasattr(container, "file_id"):
            val["id"] = container.file_id
        val["parent_type"] = container.parent.container_type
        val["parent_id"] = container.parent.id
    return val


def container_from_pickleable_dict(
    val: t.Dict, local_curator: c.HierarchyCurator
) -> datatypes.Container:
    """Take the simple pickleable dict entry and
    return the flywheel container.
    """
    get_container_fn = getattr(
        local_curator.context.client, f"get_{val['container_type']}"
    )
    container = get_container_fn(val["id"])
    log.debug(f"Found {container.container_type}, ID: {container.id}")
    return container


def handle_container(local_curator: c.HierarchyCurator, val: t.Dict[str, str]):
    """Take the pickleable dictionary and convert back
    into container, then handle curation.
    """
    try:
        container = container_from_pickleable_dict(val, local_curator)
    except flywheel.rest.ApiException as e:
        log.error(e)
    else:
        if local_curator.validate_container(container):
            local_curator.curate_container(container)


def make_walker(container: datatypes.Container, curator: c.HierarchyCurator):
    """Generate a walker from a container and curator."""
    w = walker.Walker(
        container,
        depth_first=curator.config.depth_first,
        reload=curator.config.reload,
        stop_level=curator.config.stop_level,
    )
    return w
