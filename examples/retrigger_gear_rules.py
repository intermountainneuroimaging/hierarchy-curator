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

log = logging.getLogger("retrigger_gear_rules")
log.setLevel("DEBUG")


def needs_to_be_retriggered(file_: flywheel.FileEntry):
    # Custom logic to determine if file needs to have gear rule retriggered.
    # Simply re-evaluate gear rules on all niftis
    if file_.type == "nifti":
        return True
    return False


def retrigger(acq: flywheel.Acquisition, file_: flywheel.FileEntry):
    type_ = file_.type
    modality = file_.modality
    # Set to none type
    acq.update_file(file_.name, {"type": None})
    # Set back to nifti
    acq.update_file(file_.name, {"type": type_, "modality": modality})


class Curator(HierarchyCurator):

    # Curate acquisition files
    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        log.info(f"Curating acquisition {acquisition.label}")
        acq = acquisition.reload()
        for file_ in acq.files:
            if needs_to_be_retriggered(file_):
                log.info(f"Retriggering {file_.name}")
                retrigger(acq, file_)
