import logging

import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

log = logging.getLogger("test")
log.setLevel(logging.INFO)


class Curator(HierarchyCurator):
    """Very simple curator that appends a log for each level of the
    hierarchy.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config.report = True

    def curate_project(self, project: flywheel.Project):
        self.reporter.append_log(
            container_type=project.container_type,
            container_label=project.label,
        )

    def curate_subject(self, subject: flywheel.Subject):
        log.info("logging subject")
        self.reporter.append_log(
            container_type=subject.container_type,
            container_label=subject.label,
        )

    def curate_session(self, session: flywheel.Session):
        self.reporter.append_log(
            container_type=session.container_type,
            container_label=session.label,
        )

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        self.reporter.append_log(
            container_type=acquisition.container_type,
            container_label=acquisition.label,
        )

    def curate_analysis(self, analysis):
        self.reporter.append_log(
            container_type=analysis.container_type,
            container_label=analysis.label,
        )

    def curate_file(self, file_: flywheel.FileEntry):
        self.reporter.append_log(
            container_type=file_.container_type, container_label=file_.name
        )
