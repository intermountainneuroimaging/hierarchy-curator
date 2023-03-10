"""
An example curation script to correct the session.label based on a predefined
mapping and the classification based on the Dicom SeriesDescription data element.
"""

import logging

import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

log = logging.getLogger("my_curator")
log.setLevel("DEBUG")


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config.report = True

    def curate_project(self, project: flywheel.Project):
        self.reporter.append_log(
            container_type="project",
            label=project.label,
            msg=f"Curating files under project {project.label}",
        )

    def curate_file(self, file_: flywheel.FileEntry):
        try:
            new_classification = self.classify_file(file_)
            if new_classification is None:
                return
            else:
                file_.update_classification(new_classification)
                self.reporter.append_log(
                    container_type="file",
                    label=file_.name,
                    msg=f"file {file.name} classification updated to {new_classification}",
                )
        except Exception as exc:
            self.reporter.append_log(
                container_type="file",
                err=str(exc),
                label=file_.name,
                resolved="False",
                search_key="",
            )

    def classify_file(self, file_: flywheel.FileEntry):
        series_description = file_.info.get("SeriesDescription")
        classification = file_.classification
        if "a_special_string" in series_description.lower():
            classification["Custom"].append("HasSpecialString")
            return classification
        return None
