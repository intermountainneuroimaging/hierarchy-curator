import copy
import logging
import sys
from contextlib import contextmanager, nullcontext
from logging import handlers
from multiprocessing import Queue
from pathlib import Path
from unittest.mock import MagicMock

import _pytest
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
    """Logs from multiple processes don't get propagated back  to the
    pytest caplog fixture correctly.

    In this context manager, we remove the pytest caplog handlers,
    and add a QueueHandler (which uses a multiprocessing.Queue so can
    handle sharing between processes).  Whenever a log message is
    written in the context manager, it goes to the Queue instead.

    Then when we finish the context manager, we pull everything off
    the queue and re-emit the log to the proper logger in the
    MainProcess.
    """

    @contextmanager
    def ctx():
        logger_queue = Queue()
        logger = logging.getLogger()
        # Save copy of original handlers to restore
        orig_handlers = copy.copy(logger.handlers)
        # Set level to 0 to capture every log.
        logger.setLevel(0)
        # Add QueueHandler
        logger.addHandler(handlers.QueueHandler(logger_queue))
        # Remove pytest LogCaptureHandlers
        logger.handlers = [
            handler
            for handler in logger.handlers
            if not isinstance(handler, _pytest.logging.LogCaptureHandler)
        ]
        yield
        # Restore original handlers
        logger = logging.getLogger()
        logger.handlers = orig_handlers
        # Re-emit logs.
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
            "test",
            "test/sub-1",
            "test/sub-1/ses-0-sub-1",
            "test/sub-1/ses-0-sub-1/acq-0-ses-0-sub-1",
            "test/sub-0",
            "test/sub-0/ses-0-sub-0",
            "test/sub-0/ses-0-sub-0/acq-0-ses-0-sub-0",
        ]
    )


@pytest.mark.parametrize("multi", [True, False])
def test_curate_main_breadth_first(
    multi, fw_project, oneoff_curator, mocker, caplog, caplog_multithreaded, containers
):
    project = fw_project(n_subs=2)
    curator_path = ASSETS_DIR / "dummy_curator.py"

    get_curator_patch = mocker.patch("fw_gear_hierarchy_curator.curate.c.get_curator")
    reporter_mock = mocker.patch(
        "fw_gear_hierarchy_curator.curate.reporters.AggregatedReporter"
    )

    get_curator_patch.return_value = oneoff_curator(report=True, multi=multi)
    get_curator_patch.return_value.config.depth_first = False

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
            "test",
            "test/sub-1",
            "test/sub-1/ses-1-0",
            "test/sub-1/ses-1-0/acq-1-0-0",
            "test/sub-0",
            "test/sub-0/ses-0-0",
            "test/sub-0/ses-0-0/acq-0-0-0",
        ]
    )
