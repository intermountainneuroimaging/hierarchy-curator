from unittest.mock import MagicMock, patch

import flywheel
import pytest

from fw_gear_hierarchy_curator.utils import (
    container_from_pickleable_dict,
    container_to_pickleable_dict,
    handle_work,
    make_walker,
)


def test_container_to_pickleable_dict():
    proj = flywheel.Project(id="test")
    out = container_to_pickleable_dict(proj)
    assert out["container_type"] == "project"
    assert out["id"] == "test"
    file = flywheel.FileEntry(file_id="test")
    file._parent = flywheel.Acquisition(id="test")
    file.parent_ref = {"type": "acquisition", "id": "test"}
    out = container_to_pickleable_dict(file)
    assert out["container_type"] == "file"
    assert out["id"] == "test"
    assert out["parent_type"] == "acquisition"
    assert out["parent_id"] == "test"


def test_container_from_pickleable_dict(mocker):
    val = {"container_type": "subject", "id": "test"}
    curator_mock = MagicMock()
    curator_mock.context.client.return_value = flywheel.Subject(label="test")
    _ = container_from_pickleable_dict(val, curator_mock)
    curator_mock.context.client.get_subject.assert_called_once_with("test")


def test_handle_work(mocker):
    pickleable_mock = mocker.patch(
        "fw_gear_hierarchy_curator.utils.container_from_pickleable_dict"
    )
    func = MagicMock()
    curator = MagicMock()
    children = [MagicMock()]
    handle_work(children, curator, func)
    pickleable_mock.assert_called_once_with(children[0], curator)
    func.assert_called_once_with(curator, [pickleable_mock.return_value])


def test_handle_container_api_exception_doesnt_validate(mocker, caplog):
    pickleable_mock = mocker.patch(
        "fw_gear_hierarchy_curator.utils.container_from_pickleable_dict"
    )
    pickleable_mock.side_effect = flywheel.rest.ApiException
    func = MagicMock()
    curator = MagicMock()
    children = [MagicMock()]
    handle_work(children, curator, func)
    func.assert_called_once_with(curator, [])
    assert caplog.record_tuples[0][2].startswith("Could not get container")


def test_make_walker(mocker):
    w_patch = mocker.patch("fw_gear_hierarchy_curator.utils.walker.Walker")
    curator = MagicMock()
    curator.config.depth_first = True
    curator.config.reload = True
    curator.config.stop_level = "project"
    container = MagicMock()
    _ = make_walker(container, curator)
    w_patch.assert_called_once_with(
        container, depth_first=True, reload=True, stop_level="project"
    )
