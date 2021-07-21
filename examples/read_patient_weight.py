import json
import logging
import os
import tempfile
import zipfile

import flywheel
import pydicom
from flywheel_gear_toolkit import GearToolkitContext
from flywheel_gear_toolkit.utils import curator

log = logging.getLogger("dicom_tag_splitter")
log.setLevel("DEBUG")


class Curator(curator.HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.error_reporter = None

    def curate_file(self, file_: flywheel.FileEntry):
        # Only operate on input file
        if self.additional_input_one.hash == file_.hash:
            log.info(f"Curating file {file_.name}")
            with tempfile.TemporaryDirectory() as tmp_dir:
                zip_file_path = Path(tmp_dir) / file_.name
                file_.download(zip_file_path)
                if zipfile.is_zipfile(zip_file_path):
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
