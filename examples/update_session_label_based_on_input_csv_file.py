"""
An example curation script to correct the session.label based on a csv files containing
columns: session.id, label.
"""
import logging
from pathlib import Path

import flywheel
import pandas as pd
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

log = logging.getLogger("my_curator")
log.setLevel("DEBUG")


class Curator(HierarchyCurator):
    def __init__(self):
        super().__init__(**kwargs)
        # Stop at project level since we only care about curating project
        self.config.stop_level = 'project'

    def curate_project(self, project: flywheel.Project):
        if self.additional_input_one:
            df = pd.read_csv(self.additional_input_one)
            for i, r in df.iterrows():
                session = self.context.client.get_session(r["session.id"])
                session.update(label=r["label"])
        else:
            raise ValueError("no csv file found")
