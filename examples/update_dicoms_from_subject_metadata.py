import tempfile

from flywheel.rest import ApiException
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from fw_file.dicom import DICOMCollection


def robust_replace(parent, filename, filepath):
    """Robust deletion and upload of file."""
    import backoff

    def is_not_500_502_504(exc):
        if hasattr(exc, "status"):
            if exc.status in [504, 502, 500]:
                return False
        return True

    @backoff.on_exception(
        backoff.expo, ApiException, max_time=60, giveup=is_not_500_502_504
    )
    def robust_delete(parent, filename):
        parent.delete_file(filename)

    @backoff.on_exception(
        backoff.expo, ApiException, max_time=60, giveup=is_not_500_502_504
    )
    def robust_upload(parent, filepath):
        parent.upload_file(filepath)

    robust_delete(parent, filename)
    robust_upload(parent, filepath)


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["tqdm==4.59.0", "backoff==1.11.1"])
        # Curate depth first
        #   Important to curate depth first so that all files in curate_file
        #   Are guaranteed to be under the current self.sub_label
        self.depth_first = True

    def curate_subject(self, subject):
        self.sub_label = subject.label

    def curate_file(self, file_):
        if file_.type == "dicom" and \
                file_.mimetype != 'application/zip':

            # Get parent of file
            parent_type = file_.parent_ref["type"]
            get_parent_fn = getattr(self.context.client, f"get_{parent_type}")
            parent = get_parent_fn(file_.parent_ref["id"])
            # Download file and update each slice with PatientID from subject label
            # Since we're traversing depth first, this is guaranteed to be
            # the label of the subject the file is under.
            with tempfile.NamedTemporaryFile(suffix='.dicom.zip') as temp:
                file_.download(temp.name)
                dcms = DICOMCollection.from_zip(temp.name)
                dcms.set("PatientID", self.sub_label)

                dcms.to_zip(f"/tmp/{file_.name}")
            # Delete existing file and re-upload to "replace"
            robust_replace(parent, file_.name, f"/tmp/{file_.name}")
