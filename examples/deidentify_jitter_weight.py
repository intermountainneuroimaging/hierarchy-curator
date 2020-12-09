import json
import logging
from pathlib import Path
import os
import random
import tempfile
import zipfile

import flywheel
import pydicom
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter
from flywheel_gear_toolkit.utils import curator
from flywheel_gear_toolkit import GearToolkitContext

log = logging.getLogger("deidentify_patient_weight")
log.setLevel("DEBUG")


class Curator(curator.HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None
        if self.write_report:
            log.info("Initiating reporter")
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / "out.csv")
            )
        self.temp_dir = Path(tempfile.mkdtemp())

    def curate_project(self, project: flywheel.Project):
        pass

    def curate_subject(self, subject: flywheel.Subject):
        pass

    def curate_session(self, session: flywheel.Session):
        pass

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        self.reporter.append_log(
            container_type="acquisition",
            label=acquisition.label,
            msg=f"Curating {len(acquisition.files)} files",
            resolved=True,
            err="",
            search_key=""
        )

    def curate_analysis(self, analysis):
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        log.info(f"Curating file {file_.name}")
        if file_.name.endswith(".zip"):
            f_read_path = self.temp_dir / f"old_{file_.name}"
            f_write_path = self.temp_dir / file_.name

            f_read_extract_path = self.temp_dir / f"old_{file_.name.split('.zip')[0]}"
            f_write_extract_path = self.temp_dir / file_.name.split(".zip")[0]

            file_.download(str(f_read_path))
            # try:
            zip_read = zipfile.ZipFile(str(f_read_path))
            zip_write = zipfile.ZipFile(str(f_write_path), 'w')

            for n in range(len(zip_read.namelist())):
                dcm_path = zip_read.extract(
                    zip_read.namelist()[n], path=str(f_read_extract_path)
                )
                if os.path.isfile(dcm_path):
                    try:
                        dcm = pydicom.dcmread(dcm_path)
                        # Randomly adjust patient weight for deidentify (Adding "jitter")
                        setattr(
                            dcm,
                            "StudyDescription",
                            f"My deescr {random.randint(-10,10)}",
                        )
                        new_path = f_write_extract_path / os.path.basename(dcm_path)
                        dcm.save_as(new_path)
                        zip_write.write(new_path)
                    except Exception as e:
                        if self.reporter:
                            self.reporter.append_log(
                                err=str(e),
                                container_type="file",
                                label=file_.name,
                                search_key="",
                                resolved=False,
                                container_id=file_.id,
                                msg="",
                            )
                        else:
                            log.error(e)
            zip_read.close()
            zip_write.close()
            file_.parent.upload_file(f_write_path)
            # except:
            #    self.reporter.append_log(
            #        err="Cannot open zipfile",
            #        container_type='file',
            #        label=file_.name
            #    )
