from unittest.mock import MagicMock

import flywheel
import pytest
from flywheel_gear_toolkit.utils.reporters import LogRecord

from fw_gear_hierarchy_curator.curate import main, start_multiproc, worker


def test_worker(mocker):
    curator = MagicMock()
    copy_mock = mocker.patch("fw_gear_hierarchy_curator.curate.copy")
    copy_mock.deepcopy.return_value = curator
    pickle_mock = mocker.patch(
        "fw_gear_hierarchy_curator.utils.container_from_pickleable_dict"
    )
    walker_mock = mocker.patch("fw_gear_hierarchy_curator.curate.make_walker")
    walker_mock.return_value.walk.return_value = [flywheel.Acquisition(label="test")]
    work = [
        {"container_type": "test", "id": "test"},
        {"container_type": "test1", "id": "test1"},
    ]
    # Depth First
    curator.config.depth_first = True
    lock_mock = MagicMock()
    worker(curator, work, lock_mock, 0)
    assert [call[0] for call in pickle_mock.call_args_list] == [
        (work[0], curator),
        (work[1], curator),
    ]
    assert walker_mock.call_count == 2
    assert curator.context.get_client.call_count == 1
    assert curator.validate_container.call_count == 2
    assert curator.curate_container.call_count == 2
    pickle_mock.reset_mock()
    walker_mock.reset_mock()
    curator.reset_mock()
    # Breadth First
    curator.config.depth_first = False
    worker(curator, work, lock_mock, 0)

    assert curator.context.get_client.call_count == 1
    assert [call[0] for call in pickle_mock.call_args_list] == [
        (work[0], curator),
        (work[1], curator),
    ]
    assert walker_mock.call_count == 1
    assert curator.validate_container.call_count == 1
    assert curator.curate_container.call_count == 1


def test_start_multiproc(mocker, tmp_path):
    mocker.patch("fw_gear_hierarchy_curator.curate.multiprocessing")
    mocker.patch("fw_gear_hierarchy_curator.curate.handle_work")
    pickle_mock = mocker.patch(
        "fw_gear_hierarchy_curator.curate.container_to_pickleable_dict"
    )
    walker = MagicMock()
    walker.deque = [
        {"container_type": "test", "id": "test"},
        {"container_type": "test1", "id": "test1"},
    ]
    curator = MagicMock()
    curator.config.format = LogRecord
    curator.config.workers = 2
    curator.config.path = tmp_path / "out.csv"

    start_multiproc(curator, walker)

    assert pickle_mock.call_count == 2


def test_main(mocker):
    get_curator = mocker.patch("fw_gear_hierarchy_curator.curate.c.get_curator")
    curator_mock = MagicMock()
    curator_mock.config.depth_first = True
    curator_mock.config.reload = True
    curator_mock.config.stop_level = "session"
    curator_mock.config.multi = False
    get_curator.return_value = curator_mock
    walker = mocker.patch("fw_gear_hierarchy_curator.curate.walker.Walker")
    walker.return_value.walk.return_value = ["test"]
    reporter = mocker.patch(
        "fw_gear_hierarchy_curator.curate.reporters.AggregatedReporter"
    )
    ctx = MagicMock()
    parent = MagicMock()
    curator_path = ""
    main(ctx, parent, curator_path)

    get_curator.assert_called_once()
    walker.assert_called_once_with(
        parent, depth_first=True, reload=True, stop_level="session"
    )
    reporter.assert_called_once()
    curator_mock.validate_container.assert_called_once()
    curator_mock.curate_container.assert_called_once()
