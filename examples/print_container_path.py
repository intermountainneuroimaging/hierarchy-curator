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
    log.info('/'.join(levels))

SPECIAL_LABEL='my_special_label'

class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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
        print_path([self.project_label, self.subject_label, self.session_label, acquisition.label])
