"""
An example curation script to print container paths.
"""

import dataclasses
import json
import logging
from pathlib import Path

import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

log = logging.getLogger("print_container_path")
log.setLevel("DEBUG")


def print_path(levels):
    log.info("/".join(levels))


SPECIAL_LABEL = "my_special_label"


class Curator(HierarchyCurator):
    """
    Walk entire hierarchy, but skip everything under the subject
    with the name "my_special_label"
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # By setting the callback to `self.validate_container`
        #   we tell the walker to call this whenever it's going
        #   to queue up a containers children.  `self.validate_container`
        #   returns `True` by default, unless one of the
        #   `self.validate_<container> methods has been implemented.  In this
        #   case we have implemented `self.validate_subject`, so when this
        #   function returns `True`, the walker will queue that subjects
        #   children, when it returns `False` it will not, effectively removing
        #   a branch of the Flyhweel Hierarchy Tree.
        self.config.callback = self.validate_container

    def curate_project(self, project: flywheel.Project):
        self.project_label = project.label
        print_path([self.project_label])

    def validate_subject(self, session: flywheel.Subject):
        if session.label == SPECIAL_LABEL:
            return False
        return True

    def curate_subject(self, subject: flywheel.Subject):
        self.subject_label = subject.label
        print_path([self.project_label, self.subject_label])

    def curate_session(self, session: flywheel.Session):
        self.session_label = session.label
        print_path([self.project_label, self.subject_label, self.session_label])

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        print_path(
            [
                self.project_label,
                self.subject_label,
                self.session_label,
                acquisition.label,
            ]
        )
