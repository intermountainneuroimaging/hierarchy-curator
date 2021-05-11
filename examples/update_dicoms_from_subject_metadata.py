import tempfile

from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from fw_file.dicom import DICOMCollection


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs, extra_packages=["tqdm==4.59.0"])
        # Curate depth first
        #   Important to curate depth first so that all files in curate_file
        #   Are guaranteed to be under the current self.sub_label
        self.config.depth_first = True

    def curate_subject(self, subject):
        self.sub_label = subject.label

    def curate_file(self, file_):
        if file_.type == 'dicom':
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

            """
            NOTE: Be very cautious about deleting and reuploading files to "replace".  

            The preferred workflow would be to not do these changes in place, and instead
            to upload to a new (destination) project.  However, we recognize that this doesn't
            work in all use cases.  Please only delete and re-upload if you are sure that's what
            you need.
            """

            # Delete existing file and re-upload to "replace"
            parent.delete_file(file_.name)
            parent.upload_file(f"/tmp/{file_.name}")
