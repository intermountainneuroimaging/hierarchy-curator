"""A HierarchyCurator script that smart copies multiple projects and then aggregate
all subjects to a dedicated destination project

This is script is intended to alleviate the current limitation with smart copy
only copying to a new project.

Usage:

    1. Modify the below global variables
        * `SOURCE_PROJECT_PATHS` (required)
        * `DESTINATION_PROJECT_PATH` (required)
        * `TMP_GROUP` (optional)
        * `WAIT_TIMEOUT` (optional)
    2. Run the script as a HierarchyCurator gear job
"""

import json
import logging
import re
import sys
import time
from typing import Any, Dict, List, Optional

import flywheel
from flywheel_gear_toolkit.utils.curator import GearToolkitContext, HierarchyCurator

log = logging.getLogger()

################################################################################
#      The below global variables need to be modified to run the script        #
################################################################################

# Path to source project to copy
SOURCE_PROJECT_PATHS = [
    "<group>/<project.label>",
    "<group>/<project.label>",
]
# Final destination project
DESTINATION_PROJECT_PATH = "<group>/<project.label>"
# Group where temporary copies will be created
TMP_GROUP = "flywheel"
# Maximum time to wait for a copy to complete
WAIT_TIMEOUT = 2 * 3600  # Timeout


def get_api_key_from_client(fw_client: flywheel.Client) -> str:
    """Returns the api key from an instance of flywheel.Client

    Args:
        fw_client (flywheel.Client): an instance of the flywheel client

    Returns:
        (str): the api key
    """
    site_url = fw_client.get_config().site.get("api_url")  # Get the URL
    site_base = site_url.rsplit("/", maxsplit=1)[0]  # Remove the "/api"
    site_base = site_base.split("/")[-1]  # remove the "http://"
    key_string = fw_client.get_current_user().api_key.key
    api_key = ":".join([site_base, key_string])
    return api_key


def get_or_create_group(client, group_id=None) -> flywheel.Group:
    """Returns or create the group with the given id."""
    try:
        group = client.lookup(group_id)
    except flywheel.ApiException as exc:
        if exc.status == 404:
            client.add_group(group_id)
            group = client.lookup(group_id)
        else:
            log.error("Error creating or getting temporary group: {}".format(exc))
            sys.exit(-1)
    return group


def validate_project_path(project_path):
    """Validates the project path.

    Args:
        path (str): the path to validate
    """
    reg = re.compile(r"^[0-9a-z][0-9a-z.@_-]{0,62}[0-9a-z]\/(?!unsorted|unknown).*$")
    if reg.match(project_path):
        return True
    return False


def get_or_create_project(client, project_path):
    """Returns or create the project with the given path."""
    try:
        project = client.lookup(project_path)
    except flywheel.ApiException as exc:
        if exc.status == 404:
            log.info(f"Creating project {project_path}")
            group, project_label = project_path.split("/")
            try:
                group = client.lookup(group)
            except flywheel.ApiException as exc:
                if exc.status == 404:
                    log.error(
                        f"Group {group} not found. Must exist before creating project."
                    )
                    sys.exit(-1)
                else:
                    raise exc
            group.add_project(label=project_label)
            project = client.lookup(project_path)
        else:
            log.error("Error creating or getting project: {}".format(exc))
            sys.exit(-1)
    return project


def smart_copy(
    api_key, src_project, group: flywheel.Group = None, dst_project_label: str = None
) -> dict:
    """Smart copy a project to a group and returns API response.

    Args:
        src_project (flywheel.Project): the source project
        dst_group (flywheel.Group): the destination group
        dst_project_label (str): the destination project label
    """
    from fw_core_client import CoreClient

    log.info(f"Smart copying {src_project}")
    core_client = CoreClient(
        api_key=api_key, client_name="curator", client_version="1.0"
    )
    data = {
        "group_id": group.id,
        "project_label": dst_project_label,
        "filter": {
            "exclude_analysis": False,
            "exclude_notes": False,
            "exclude_tags": False,
            "include_rules": [],
            "exclude_rules": [],
        },
    }
    return core_client.post(f"/projects/{src_project.id}/copy", data=json.dumps(data))


def is_copy_done(api_key, project_id, snapshot_id):
    """Returns True if the copy is done, False otherwise."""
    from fw_core_client import CoreClient

    core_client = CoreClient(
        api_key=api_key, client_name="curator", client_version="1.0"
    )
    response = core_client.get(f"/projects/{project_id}/copy/{snapshot_id}/status")
    return True if response["copy_status"] == "completed" else False


class Curator(HierarchyCurator):
    """
    Curator for aggregating smart copies of a projects into a single project.
    """

    def __init__(
        self, context: GearToolkitContext = None, **kwargs: Optional[Dict[str, Any]]
    ) -> None:
        super().__init__(context, extra_packages=["fw-core-client==1.1.2"], **kwargs)
        is_valid = validate_project_path(DESTINATION_PROJECT_PATH)
        if not is_valid:
            log.error(
                f"This is an invalid project path (check script instructions): {DESTINATION_PROJECT_PATH}"
            )
        self.dst_project = get_or_create_project(self.client, DESTINATION_PROJECT_PATH)
        self.source_proj = []
        self.config.stop_level = "project"
        self.api_key = get_api_key_from_client(self.client)
        self.tmp_group = get_or_create_group(self.client, TMP_GROUP)  # store tmp copies

    def curate_project(self, project):
        copy_rsp = []
        for project_path in SOURCE_PROJECT_PATHS:
            log.info(f"Triggering smart copy of {project_path}")
            is_valid = validate_project_path(project_path)
            if not is_valid:
                log.error(f"This is an invalid project path: {project_path} - SKIPPING")
                continue
            project = self.client.lookup(project_path)
            dst_project_label = f"{project.label}_tmp_copy"
            copy_rsp.append(
                smart_copy(
                    self.api_key,
                    project,
                    group=self.tmp_group,
                    dst_project_label=dst_project_label,
                )
            )
        copy_projects = [self.client.get(rsp["project_id"]) for rsp in copy_rsp]

        # wait for all copies to complete
        log.info("Waiting for all copies to complete")
        start_time = time.time()
        n_complete = 0
        while True:
            time.sleep(10)
            for i, rsp in enumerate(copy_rsp):
                if is_copy_done(self.api_key, rsp["project_id"], rsp["snapshot_id"]):
                    log.info(f"Copy project {rsp['project_id']} complete")
                    n_complete += 1
            if len(copy_rsp) == n_complete:
                break
            if time.time() - start_time > WAIT_TIMEOUT:
                log.error("Wait timeout for copies to complete")
                sys.exit(-1)

        # Move subjects to destination project
        for project in copy_projects:
            log.info(
                f"Moving subjects from {project.label} to {self.dst_project.label}"
            )
            # TODO: replace with bulk move when working for smart copied subjects
            for subject in project.subjects.iter():
                try:
                    subject.update(project=self.dst_project.id)
                except flywheel.ApiException as exc:
                    if exc.status == 422:
                        log.error(
                            f"Subject {subject.label} already exists in {self.dst_project.label} - Skipping"
                        )
                    else:
                        log.exception(
                            f"Error moving subject {subject.label} from {project.label} to {self.dst_project.label}"
                        )

        # delete tmp projects
        for project in copy_projects:
            if len(project.subjects()) == 0:
                log.info(f"deleting {project.label}")
                self.client.delete_project(project.id)
            else:
                log.info(
                    f"{project.label} has {len(project.subjects())} subjects - skipping delete"
                )

        log.info("DONE")
        sys.exit(0)
