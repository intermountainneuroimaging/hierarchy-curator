import logging
import sys
from contextlib import contextmanager, nullcontext
from logging import handlers
from multiprocessing import Queue
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from fw_gear_testing.hierarchy import _cont, make_project

from fw_gear_hierarchy_curator.curate import main


def oneoff_curator(report=True, multi=True):
    log = logging.getLogger("test")

    class reporter(HierarchyCurator):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.config.report = report
            self.config.multi = multi
            self.config.workers = 2
            self.data = {
                "project": "test",
                "subject": "",
                "session": "",
                "acquisition": "",
            }

        def curate_project(self, proj):
            self.data["project"] = proj.label
            path = self.data["project"]
            log.info(path)

        def curate_subject(self, sub):
            self.data["subject"] = sub.label
            path = f"{self.data['project']}/{self.data['subject']}"
            log.info(path)

        def curate_session(self, ses):
            self.data["session"] = ses.label
            path = (
                self.data["project"]
                + "/"
                + self.data["subject"]
                + "/"
                + self.data["session"]
            )
            log.info(path)

        def curate_acquisition(self, acq):
            self.data["acquisition"] = acq.label
            path = (
                self.data["project"]
                + "/"
                + self.data["subject"]
                + "/"
                + self.data["session"]
                + "/"
                + self.data["acquisition"]
            )
            log.info(path)

    return reporter()


@patch("fw_gear_hierarchy_curator.curate.c.get_curator")
@patch("fw_gear_hierarchy_curator.curate.reporters.AggregatedReporter")
def test_curate_main_depth_first(get_curator_patch, reporter_mock):
    project = make_project(n_subs=2)

    get_curator_patch.return_value = oneoff_curator(report=True, multi=True)
    context_mock = MagicMock()
    for c_type in ["acquisition", "session", "subject", "project"]:
        getattr(context_mock.client, f"get_{c_type}").side_effect = _cont.get_container
    context_mock.client.get_client.return_value = context_mock.client
    get_curator_patch.return_value.context = context_mock
    get_curator_patch.return_value.reporter = reporter_mock

    main(context_mock, project, None)


test_curate_main_depth_first()
