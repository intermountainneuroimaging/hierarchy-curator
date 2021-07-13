import logging
import sys
from contextlib import contextmanager, nullcontext
from logging import handlers
from multiprocessing import Queue
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

from fw_gear_hierarchy_curator.curate import main

ASSETS_DIR = Path(__file__).parent / "assets"


@pytest.fixture(scope="session", autouse=True)
def reset_log():
    logging.basicConfig(
        stream=sys.stdout,
        format="%(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        level=logging.DEBUG,
    )
    log = logging.getLogger()


@pytest.fixture()
def caplog_multithreaded():
    @contextmanager
    def ctx():
        logger_queue = Queue()
        logger = logging.getLogger()
        logger.setLevel(0)
        logger.addHandler(handlers.QueueHandler(logger_queue))
        yield
        while True:
            log_record: logging.LogRecord = logger_queue.get_nowait()
            if log_record.message == "END":
                break
            logger = logging.getLogger(log_record.name)
            logger._log(
                level=log_record.levelno,
                msg=log_record.message,
                args=log_record.args,
                exc_info=log_record.exc_info,
            )

    return ctx


@pytest.fixture
def oneoff_curator():
    def _gen(report=True, multi=True):
        log = logging.getLogger("test")

        class reporter(HierarchyCurator):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.config.report = report
                self.config.multi = multi
                self.config.workers = 2
                self.data = {
                    "project": "",
                    "subject": "",
                    "session": "",
                    "acquisition": "",
                }

            def validate_container(self, container):
                log.info("In validate_container")
                return super().validate_container(container)

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

    return _gen


@pytest.mark.parametrize("multi", [True, False])
def test_curate_main_depth_first(
    multi, fw_project, oneoff_curator, mocker, caplog, caplog_multithreaded, containers
):
    project = fw_project(n_subs=2)
    curator_path = ASSETS_DIR / "dummy_curator.py"

    get_curator_patch = mocker.patch("fw_gear_hierarchy_curator.curate.c.get_curator")
    reporter_mock = mocker.patch(
        "fw_gear_hierarchy_curator.curate.reporters.AggregatedReporter"
    )

    get_curator_patch.return_value = oneoff_curator(report=True, multi=multi)
    context_mock = MagicMock()
    for c_type in ["acquisition", "session", "subject", "project"]:
        getattr(
            context_mock.client, f"get_{c_type}"
        ).side_effect = containers.get_container
    context_mock.client.get_client.return_value = context_mock.client
    get_curator_patch.return_value.context = context_mock

    with (caplog_multithreaded() if multi else nullcontext()):
        log = logging.getLogger()
        main(context_mock, project, curator_path)
        log.info("END")

    records = [rec[2] for rec in caplog.record_tuples if rec[0] == "test"]
    assert all(
        val in records
        for val in [
            "Mock",
            "Mock/sub-1",
            "Mock/sub-1/ses-1-0",
            "Mock/sub-1/ses-1-0/acq-1-0-0",
            "Mock/sub-0",
            "Mock/sub-0/ses-0-0",
            "Mock/sub-0/ses-0-0/acq-0-0-0",
        ]
    )


@pytest.mark.parametrize("multi", [True, False])
def test_curate_main_breadth_first(
    multi, fw_project, oneoff_curator, mocker, caplog, caplog_multithreaded
):
    client = None
    project = fw_project(n_subjects=2)
    curator_path = ASSETS_DIR / "dummy_curator.py"

    get_curator_patch = mocker.patch("fw_gear_hierarchy_curator.curate.c.get_curator")
    reporter_mock = mocker.patch(
        "fw_gear_hierarchy_curator.curate.reporters.AggregatedReporter"
    )

    get_curator_patch.return_value = oneoff_curator(report=True, multi=multi)
    get_curator_patch.return_value.config.depth_first = False

    with (caplog_multithreaded() if multi else nullcontext()):
        log = logging.getLogger()
        main(client, project, curator_path)
        log.info("END")

    records = [rec[2] for rec in caplog.record_tuples if rec[0] == "test"]
    assert all(
        val in records
        for val in [
            "Mock",
            "Mock/sub-1",
            "Mock/sub-1/ses-1-0",
            "Mock/sub-1/ses-1-0/acq-1-0-0",
            "Mock/sub-0",
            "Mock/sub-0/ses-0-0",
            "Mock/sub-0/ses-0-0/acq-0-0-0",
        ]
    )


def test_curate_main_with_a_dummy_curator(fw_project):
    client = None
    project = fw_project(n_subjects=1)
    curator_path = ASSETS_DIR / "dummy_curator.py"
    main(client, project, curator_path)
    subject = project.subjects()[0]
    session = subject.sessions()[0]
    acquisition = session.acquisitions()[0]
    assert project.reload().label == "Curated"
    assert subject.reload().label == "Curated"
    assert session.reload().label == "Curated"
    assert acquisition.reload().label == "Curated"
