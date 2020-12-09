"""
An example curation script to correct the session.label based on a predefined
mapping and the classification based on the Dicom SeriesDescription data element.
"""

import dataclasses
import json
import logging
from pathlib import Path

import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter, BaseLogRecord

log = logging.getLogger("my_curator")
log.setLevel("DEBUG")

SESSION_LABEL_CORRECTION = {
    "screening": "Screening",
    "w04": "Week_04",
    "w12": "Week_12",
    "w16": "Week_16",
    "w20": "Week_20",
    "w24": "Week_24",
    "w28": "Week_28",
    "w36": "Week_36",
    "w48": "Week_48",
    "REV1": "Relapse_Evaluation_1",
}


@dataclasses.dataclass
class MapLogRecord(BaseLogRecord):

    subject_label: str = ""
    subject_id: str = ""
    session_label: str = ""
    session_id: str = ""
    resolved: bool = False
    err: str = ""
    msg: str = ""


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.reporter = None
        if self.write_report:
            log.info("Initiating reporter")
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / "out.csv"),
                format=MapLogRecord,  # Use custom log record
            )

    def curate_project(self, project: flywheel.Project):
        pass

    def curate_subject(self, subject: flywheel.Subject):
        pass

    def curate_session(self, session: flywheel.Session):
        log.info("Curating session %s", session.id)
        try:
            new_label = SESSION_LABEL_CORRECTION.get(session.label)
            if new_label:
                session.update({"label": new_label})
                self.reporter.append_log(
                    msg=f"updated session label to {new_label}",
                    subject_label=session.subject.id,
                    subject_id=session.subject.id,
                    session_label=session.label,
                    session_id=session.id,
                    resolved=True,
                )
        except Exception as exc:
            self.reporter.append_log(
                err=str(exc),
                subject_label=session.subject.id,
                subject_id=session.subject.id,
                session_label=session.label,
                session_id=session.id,
                resolved=False,
            )

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        pass

    def curate_analysis(self, analysis):
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        pass
