import copy
import logging
import pickle
import sys
from contextlib import contextmanager, nullcontext
from logging import handlers
from multiprocessing import Queue
from pathlib import Path
from unittest.mock import MagicMock, Mock

import _pytest
import dill
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


log = logging.getLogger("test")


class reporter(HierarchyCurator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config.report = kwargs.get("report", True)
        self.config.multi = kwargs.get("multi", True)
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


@pytest.fixture
def oneoff_curator(containers):
    def _gen(report=True, multi=True):

        my_reporter = reporter(report=report, multi=multi)
        client_kwargs = {}
        for c_type in ["acquisition", "session", "subject", "project"]:
            client_kwargs[f"get_{c_type}"] = PickleableMock(
                side_effect=containers.get_container
            )
        client_mock = PickleableMock(**client_kwargs)
        context_mock = PickleableMock(client=client_mock)
        my_reporter.context = context_mock
        return my_reporter

    return _gen


blank_dict_keys = MagicMock().__dict__.keys()
# See https://github.com/testing-cabal/mock/issues/139#issuecomment-122128815
# Needed to allow for pickling
class PickleableMock(MagicMock):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._to_save = kwargs

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __reduce__(self):
        if "side_effect" in self._to_save:
            self._to_save["_mock_side_effect"] = self._to_save.pop("side_effect")
        return (PickleableMock, (), self._to_save)


def test_pickle_curator(oneoff_curator):
    curator = oneoff_curator()
    curator.context = PickleableMock()
    curator.context.client = PickleableMock()
    out = dill.dumps(curator)
    assert out
    out = pickle.dumps(curator)
    assert out


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
    reporter_mock.return_value = PickleableMock()

    get_curator_patch.return_value = oneoff_curator(report=True, multi=multi)
    context_mock = MagicMock()

    with (caplog_multithreaded() if multi else nullcontext()):
        log = logging.getLogger()
        main(context_mock, project, curator_path)
        log.info("END")

    records = [rec[2] for rec in caplog.record_tuples if rec[0] == "test"]
    exp = [
        "test",
        "test/sub-1",
        "test/sub-1/ses-0-sub-1",
        "test/sub-1/ses-0-sub-1/acq-0-ses-0-sub-1",
        "test/sub-0",
        "test/sub-0/ses-0-sub-0",
        "test/sub-0/ses-0-sub-0/acq-0-ses-0-sub-0",
    ]
    assert all([val in records for val in exp])


"""
    Note: multiprocessing cannot be fully breadth_first.

    For example, if a project with two subjects are run in breadth first,
    the project will first be curated, and then each subject will be delegated
    to one of the workers, which will then curate breadth-first below them.

    In traditional (single process) curation, both subjects would first  be
    curated, but in multiprocessing, it cannot be guarenteed that both subjects
    will be fully curated before one worker starts on a session.


    Becasue of this, running breadth-first in single process will differ
    slightly from breadth-first in multiprocess, which can be seen in the
    path order prints below.


    In single threaded, both subjects would be curated first, each subject
    sets the curator's `data['subject']` attribute, so when sessions are
    curated, the sessions will only see the label of the _last subject
    to be curated_.  Whereas in multiprocessing, both subjects are curated
    in different processes, so each session will see the label of _its parent_.
"""


@pytest.mark.parametrize(
    "multi, exp",
    [
        (
            True,
            [
                "test",
                "test/sub-0",
                "test/sub-0/ses-0-sub-0",
                "test/sub-0/ses-0-sub-0/acq-0-ses-0-sub-0",
                "test/sub-1",
                "test/sub-1/ses-0-sub-1",
                "test/sub-1/ses-0-sub-1/acq-0-ses-0-sub-1",
            ],
        ),
        (
            False,
            [
                "test",
                "test/sub-0",
                "test/sub-1/ses-0-sub-0",
                "test/sub-1/ses-0-sub-1/acq-0-ses-0-sub-0",
                "test/sub-1",
                "test/sub-1/ses-0-sub-1",
                "test/sub-1/ses-0-sub-1/acq-0-ses-0-sub-1",
            ],
        ),
    ],
)
def test_curate_main_breadth_first(
    multi,
    exp,
    fw_project,
    oneoff_curator,
    mocker,
    caplog,
    caplog_multithreaded,
    containers,
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

    with (caplog_multithreaded() if multi else nullcontext()):
        log = logging.getLogger()
        main(context_mock, project, curator_path)
        log.info("END")

    records = [rec[2] for rec in caplog.record_tuples if rec[0] == "test"]
    _ = [records.remove(val) for val in exp]
    assert not len(records)
