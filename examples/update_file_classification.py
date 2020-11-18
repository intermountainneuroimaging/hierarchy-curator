"""
An example curation script to correct the session.label based on a predefined
mapping and the classification based on the Dicom SeriesDescription data element.
"""

import json
import logging

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import curator

from custom_curator.reporters import CuratorErrorReporter


log = logging.getLogger("my_curator")
log.setLevel("DEBUG")


class Curator(curator.Curator):
    def __init__(self):
        super(Curator, self).__init__(depth_first=True)
        self.error_reporter = None

    def curate_project(self, project: flywheel.Project):
        gear_context = GearToolkitContext()
        self.error_reporter = CuratorErrorReporter(
            output_dir=gear_context.output_dir, project_label=project.label
        )

    def curate_subject(self, subject: flywheel.Subject):
        pass

    def curate_session(self, session: flywheel.Session):
        pass

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        pass

    def curate_analysis(self, analysis):
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        log.info("Curating file %s", file_.name)
        try:
            new_classification = self.classify_file(file_)
            if new_classification is None:
                return
            else:
                log.debug(
                    "file %s classification updated to %s",
                    file_.name,
                    new_classification,
                )
                file_.update_classification(new_classification)
        except Exception as exc:
            ref = file_._parent.ref()
            kwargs = {f"{ref.type}_id": ref["id"]}
            self.error_reporter.write_file_error(
                err_list=[],
                err_str=str(exc),
                file_name=file_.name,
                resolved="False",
                search_key="",
                **kwargs,
            )

    def classify_file(self, file_: flywheel.FileEntry):
        series_description = file_.info.get("SeriesDescription")
        classification = file_.classification
        if "a_special_string" in series_description.lower():
            classification["Custom"].append("HasSpecialString")
            return classification
        return None
