import json
import logging
import zipfile
import pydicom
from pathlib import Path

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter


log = logging.getLogger("test")
log.setLevel(logging.INFO)


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        log.info("Initiating reporter")
        log.info(vars(self))
        if self.write_report:
            self.reporter = AggregatedReporter(
                output_path=Path(self.context.output_dir / "test.csv")
            )

    def curate_project(self, project: flywheel.Project):
        if self.reporter:
            self.reporter.append_log(
                container_type=project.container_type, container_label=project.label
            )
        pass

    def curate_subject(self, subject: flywheel.Subject):
        if self.reporter:
            log.info("logging subject")
            self.reporter.append_log(
                container_type=subject.container_type, container_label=subject.label
            )
        pass

    def curate_session(self, session: flywheel.Session):
        if self.reporter:
            self.reporter.append_log(
                container_type=session.container_type, container_label=session.label
            )
        pass

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        if self.reporter:
            self.reporter.append_log(
                container_type=acquisition.container_type,
                container_label=acquisition.label,
            )
        pass

    def curate_analysis(self, analysis):
        if self.reporter:
            self.reporter.append_log(
                container_type=analysis.container_type, container_label=analysis.label
            )
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        if self.reporter:
            self.reporter.append_log(
                container_type=file_.container_type, container_label=file_.name
            )
