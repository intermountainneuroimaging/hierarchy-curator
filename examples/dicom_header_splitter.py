import json
import logging
import zipfile
import pydicom

import flywheel
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import curator

from custom_curator.reporters import CuratorErrorReporter


log = logging.getLogger("dicom_tag_splitter")
log.setLevel("DEBUG")


class Curator(curator.Curator):
    def __init__(self):
        super(Curator, self).__init__(depth_first=True)
        self.error_reporter = None

    def curate_project(self, project: flywheel.Project):
        pass

    def curate_subject(self, subject: flywheel.Subject):
        pass

    def curate_session(self, session: flywheel.Session):
        pass

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        self.context = GearToolkitContext()
        if self.write_report:
            self.error_reporter = CuratorErrorReporter(
                output_dir=gear_context.output_dir, container_label=acquisition.label
            )

    def curate_analysis(self, analysis):
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        # Only operate on input file
        if self.input_file_one.hash == file_.hash:
            log.info(f"Curating file {file_.name}")
            if zipfile.is_zipfile(file_):
                zip = zipfile.ZipFile(zip_file_path)
                for n in range(len(zip.namelist())):
                    dcm_path = zip.extract(zip.namelist()[n], "/tmp")
                    if os.path.isfile(dcm_path):
                        try:
                            dcm = pydicom.dcmread(dcm_path)
                            log.info(f"Weight: {dcm.PatientWeight}")
                        except:
                            pass
                log.info("Done")
            log.warning("Not a zip")
