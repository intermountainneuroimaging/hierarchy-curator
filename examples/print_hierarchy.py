"""
An example curation script to correct the session.label based on a predefined
mapping and the classification based on the Dicom SeriesDescription data element.
"""

import dataclasses
import logging

import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from flywheel_gear_toolkit.utils.reporters import BaseLogRecord


@dataclasses.dataclass
class Log(BaseLogRecord):
    container_type: str = ""
    container_id: str = ""
    label: str = ""
    msg: str = ""
    resolved: bool = False


log = logging.getLogger("print_hierarchy")
log.setLevel("DEBUG")


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config.report = True
        self.config.format = Log

    def curate_project(self, project: flywheel.Project):
        log.info("Curating project %s", project.label)
        files = " ".join([file.name for file in project.files])
        self.reporter.append_log(
            container_type="project",
            container_id=project.id,
            resolved=True,
            label=project.label,
            msg=f"Project {project.label}: found files {files}",
        )

    def curate_subject(self, subject: flywheel.Subject):
        log.info("Curating subject %s", subject.label)
        files = " ".join([file.name for file in subject.files])
        self.reporter.append_log(
            container_type="subject",
            container_id=subject.id,
            resolved=True,
            label=subject.label,
            msg=f"Project {subject.label}: found files {files}",
        )

    def curate_session(self, session: flywheel.Session):
        log.info("Curating session %s", session.label)
        files = " ".join([file.name for file in session.files])
        self.reporter.append_log(
            container_type="session",
            container_id=session.id,
            resolved=True,
            label=session.label,
            msg=f"Project {session.label}: found files {files}",
        )

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        log.info("Curating acquisition %s", acquisition.label)
        files = " ".join([file.name for file in acquisition.files])
        self.reporter.append_log(
            container_type="acquisition",
            container_id=acquisition.id,
            resolved=True,
            label=acquisition.label,
            msg=f"Acquisition {acquisition.label}: found files {files}",
        )
