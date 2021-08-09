import json
import logging
import os
import random
import tempfile

import flywheel
from flywheel_gear_toolkit.utils import curator
from fw_file import DICOMCollection

log = logging.getLogger("deidentify_patient_weight")
log.setLevel("DEBUG")


class Curator(curator.HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config.report = True

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        self.reporter.append_log(
            container_type="acquisition",
            label=acquisition.label,
            msg=f"Curating {len(acquisition.files)} files",
            resolved=True,
            err="",
            search_key="",
        )

    def curate_file(self, file_: flywheel.FileEntry):
        log.info(f"Curating file {file_.name}")
        if file_.name.endswith(".zip"):
            with tempfile.TemporaryDirectory() as temp_dir:
                path = os.path.join(temp_dir, file_.name)
                file_.download(path)
                dcms = DICOMCollection.from_zip(path)
                jitter = random.randint(-10, 10)
                weight = dcms.get("PatientWeight")
                if weight:
                    dcms.set("PatientWeight", weight + jitter)
                dcms.to_zip(path)
                file_.parent.upload_file(path)
