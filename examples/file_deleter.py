"""
A script to delete files attached at the acquisition level and tagged with 'delete'.
"""

import logging
import flywheel
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

log = logging.getLogger(__name__)

def remove_dtagged_files(self, acq):
    files_rm = []
    if \
            hasattr(acq, 'files') and \
                    (acq.container_type != 'analysis') and \
                    acq.parents.session:
        for f in acq.files:
            if 'delete' in f.tags:
                log.info(f" Deleting file {f.name} file ID {f._id} from acquisition ID {acq.id} ")
                files_rm.append(f.name)
                acq.delete_file(f.name)
    return files_rm

class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        remove_dtagged_files(self, acquisition)

    def curate_project(self, acquisition: flywheel.Acquisition):
        pass

    def curate_subject(self, acquisition: flywheel.Acquisition):
        pass

    def curate_session(self, acquisition: flywheel.Acquisition):
        pass

    def curate_file(self, acquisition: flywheel.Acquisition):
        pass

    def curate_analysis(self, acquisition: flywheel.Acquisition):
        pass

