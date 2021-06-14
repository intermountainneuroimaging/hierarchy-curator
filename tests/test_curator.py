import logging
import pytest
import sys
from contextlib import contextmanager
from logging import handlers
from multiprocessing import Queue
from pathlib import Path

from flywheel_gear_toolkit.utils.curator import HierarchyCurator
from fw_gear_hierarchy_curator.curate import main

ASSETS_DIR = Path(__file__).parent / "assets"

@pytest.fixture(scope='session', autouse=True)
def reset_log():
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    log = logging.getLogger()


@pytest.fixture()
def caplog_workaround():
    @contextmanager
    def ctx():
        logger_queue = Queue()
        logger = logging.getLogger()
        logger.addHandler(handlers.QueueHandler(logger_queue))
        yield
        while not logger_queue.empty():
            print("Forwaring message")
            log_record: logging.LogRecord = logger_queue.get()
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

    log = logging.getLogger('test')

    def _gen(report=True, multi=True):

        class reporter(HierarchyCurator):

            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.config.report = report
                self.config.multi = multi

            def curate_project(self, proj):
                log.info(proj.label)

            def curate_subject(self, sub):
                log.info(sub.label)

            def curate_session(self, ses):
                log.info(ses.label)

            def curate_acquisition(self, acq):
                log.info(acq.label)

        return reporter()

    return _gen

@pytest.mark.parametrize('multi',[True, False])
def test_curate_main_initializes_reporter(
    multi,
    fw_project,
    oneoff_curator,
    mocker,
    caplog,
    caplog_workaround
):
    client = None
    project = fw_project(n_subjects=2)
    curator_path = ASSETS_DIR / "dummy_curator.py"

    get_curator_patch = mocker.patch(
        'fw_gear_hierarchy_curator.curate.c.get_curator'
    )
    reporter_mock = mocker.patch(
        'fw_gear_hierarchy_curator.curate.reporters.AggregatedReporter'
    )

    get_curator_patch.return_value = oneoff_curator(report=True, multi=multi)

    with caplog_workaround():
        main(client, project, curator_path)

    records = [rec[2] for rec in caplog.record_tuples if rec[0] == 'test']
    assert records == [
        'Mock',
        'sub-1','ses-1-0', 'acq-1-0-0',
        'sub-0','ses-0-0', 'acq-0-0-0'
    ]


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

