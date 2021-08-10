import os
import tempfile

import backoff
from flywheel.rest import ApiException
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from fw_file.dicom import DICOMCollection


def is_not_500_502_504(exc):
    if hasattr(exc, "status"):
        if exc.status in [504, 502, 500]:
            # 500: Internal Server Error
            # 502: Bad Gateway
            # 504: Gateway Timeout
            return False
    return True


@backoff.on_exception(
    backoff.expo, ApiException, max_time=60, giveup=is_not_500_502_504
)
# will retry for 60s, waiting an exponentially increasing delay between retries
# e.g. 1s, 2s, 4s, 8s, etc, giving up if exception is in 500, 502, 504.
def robust_upload(parent, filepath):
    parent.upload_file(filepath)


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["tqdm==4.59.0", "backoff==1.11.1"])
        # Curate depth first
        #   Important to curate depth first so that all files in curate_file
        #   Are guaranteed to be under the current self.sub_label
        self.config.depth_first = True
        self.data = {}

    def curate_subject(self, subject):
        self.data["sub_label"] = subject.label

    def curate_file(self, file_):
        if file_.type == "dicom":
            # Get parent of file
            parent_type = file_.parent_ref["type"]
            if parent_type != "acquisition":
                # Only curate acquisition files.
                return
            get_parent_fn = getattr(self.context.client, f"get_{parent_type}")
            parent = get_parent_fn(file_.parent_ref["id"])
            # Download file and update each slice with PatientID from subject label
            #   Since we're traversing depth first, this is guaranteed to be
            #   The label of the subject the file is under.
            with tempfile.TemporaryDirectory() as temp:
                path = os.path.join(temp, file_.name)
                file_.download(path)
                # Open archive
                dcms = DICOMCollection.from_zip(path)
                # Set PatientID to subject file is under.
                dcms.set("PatientID", self.data["sub_label"])
                dcms.to_zip(path)
                """
                NOTE: Be very cautious about deleting and reuploading files to "replace".

                The preferred workflow would be to not do these changes in place, and instead
                to upload to a new (destination) project.  However, we recognize that this doesn't
                work in all use cases.  Please only delete and re-upload if you are sure that's what
                you need.
                """
                robust_upload(parent, path)
