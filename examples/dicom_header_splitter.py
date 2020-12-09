import json
import logging
import random
import zipfile

import flywheel
import pydicom
from flywheel_gear_toolkit.utils.reporters import AggregatedReporter
from flywheel_gear_toolkit.utils import curator
from flywheel_gear_toolkit import GearToolkitContext

log = logging.getLogger("dicom_tag_splitter")
log.setLevel("DEBUG")


class Curator(curator.HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.reporter = None
        if self.write_report:
            log.info('Initiating reporter')
            self.reporter = AggregatedReporter(
                output_path=(Path(self.context.output_dir) / 'out.csv')
            )

    def curate_project(self, project: flywheel.Project):
        pass

    def curate_subject(self, subject: flywheel.Subject):
        pass

    def curate_session(self, session: flywheel.Session):
        pass

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        self.reporter.append_log(
            container_type='acquisition',
            label=acquisition.label, msg=f'Curating {len(acquisition.files)} files'
        )

    def curate_analysis(self, analysis):
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        log.info(f"Curating file {file_.name}")
        if zipfile.is_zipfile(file_):
            zip = zipfile.ZipFile(zip_file_path)
            for n in range(len(zip.namelist())):
                dcm_path = zip.extract(zip.namelist()[n], "/tmp")
                if os.path.isfile(dcm_path):
                    try:
                        dcm = pydicom.dcmread(dcm_path)
                        # Randomly adjust patient weight for deidentify
                        setattr(dcm,'PatientWeight', dcm.get('PatientWeight')+ random.randint(-10,10))
                    except:
                        pass
        log.warning("Not a zip")
