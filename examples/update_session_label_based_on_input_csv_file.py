"""
An example curation script to correct the session.label based on a csv files containing
columns: session.id, label.
"""
import logging

import flywheel
import pandas as pd
from pathlib import Path
from flywheel_gear_toolkit.utils.curator import HierarchyCuratorr

log = logging.getLogger("my_curator")
log.setLevel("DEBUG")


class Curator(HierarchyCurator):
    def __init__(self):
        super().__init__(**kwargs)

    def curate_project(self, project: flywheel.Project):
        if self.input_file_one:
            df = pd.read_csv(self.input_file_one)
            for i, r in df.iterrows():
                session = self.context.client.get_session(r["session.id"])
                session.update(label=r["label"])
        else:
            raise ValueError("no csv file found")

    def curate_subject(self, subject: flywheel.Subject):
        pass

    def curate_session(self, session: flywheel.Session):
        pass

    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        pass

    def curate_analysis(self, analysis):
        pass

    def curate_file(self, file_: flywheel.FileEntry):
        pass
