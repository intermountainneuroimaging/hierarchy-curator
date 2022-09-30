"""
An example curation script to retrigger gear rules based on fiddling file.type
"""

import logging

import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from flywheel_gear_toolkit.utils.reporters import BaseLogRecord

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
    # Set to none type
    acq.update_file(file_.name, {"type": None})
    # Set back to nifti
    res = acq.update_file(file_.name, {"type": type_})
    log.info(f"{file_.name}: {res}")


class Curator(HierarchyCurator):

    # Curate acquisition files
    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        log.info(f"Curating acquisition {acquisition.label}")
        acq = acquisition.reload()
        for file_ in acq.files:
            if needs_to_be_retriggered(file_):
                log.info(f"Retriggering {file_.name}")
                retrigger(acq, file_)
