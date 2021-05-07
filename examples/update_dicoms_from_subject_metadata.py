import tempfile

from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from fw_file.dicom import DICOMCollection


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["tqdm==x.y.z"])
        self.depth_first = False  # Curate depth first

    def curate_subject(self, subject):
        self.sub_label = subject.label

    def curate_file(self, file_):
        # Get parent of file
        parent_type = file_.parent_ref["type"]
        get_parent_fn = getattr(self.context.client, f"get_{parent_type}")
        parent = get_parent_fn(file_.parent_ref["id"])
        # Download file and update each slice with PatientID from subject label
        #   Since we're traversing depth first, this is guaranteed to be
        #   The label of the subject the file is under.
        with tempfile.NamedTemporaryFile() as temp:
            file_.download(temp)
            dcms = DICOMCollection.from_zip(temp)
            dcms.set("PatientID", self.sub_label)

            dcms.to_zip(f"/tmp/{file_.name}")
        # Delete existing file and re-upload to "replace"
        parent.delete_file(file_.name)
        parent.upload_file(f"/tmp/{file_.name}")
