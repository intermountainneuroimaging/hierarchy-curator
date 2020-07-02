import csv
import tempfile

import pytest

from custom_curator.reporters import CuratorErrorReporter, CuratorReporter


def test_CuratorReporter_can_write_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        reporter = CuratorReporter(output_dir=tmpdir, project_label="test_project")
        reporter.append([{"ID": "1234", "label": "test", "comment": "Bla"}])
        with open(reporter.output_path_full) as f:
            csv_dict_reader = csv.DictReader(f)
            assert list(next(csv_dict_reader).values()) == ["1234", "test", "Bla"]


def test_CuratorReporter_validates_data():
    with tempfile.TemporaryDirectory() as tmpdir:
        reporter = CuratorReporter(
            output_dir=tmpdir,
            project_label="test_project",
            fieldnames=["ID", "label", "comment"],
        )

        # raises if data is not a list
        with pytest.raises(ValueError):
            reporter.append({"ID": "1234", "label": "test", "comment": "Bla"})

        # raises if data does not contain correct fieldnames
        with pytest.raises(ValueError):
            reporter.append([{"ID": "1234", "label": "test"}])

        # do not raises if data does not contain correct fieldnames
        reporter.append(
            [{"ID": "1234", "label": "test", "comment": "Bla", "extra": True}]
        )


def test_CuratorErrorReporter_can_write_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        err_reporter = CuratorErrorReporter(
            output_dir=tmpdir, project_label="test_project"
        )

        # Check if an error was correctly written out.
        err_reporter.append_error(
            err_list=[],
            err_str="test error",
            acquisition_label="acq_0",
            acquisition_id="my_acq_id",
            resolved="True",
            search_key=["my", "search", "key", "list"],
        )

        with open(err_reporter.output_path_full) as f:
            csv_dict_reader = csv.DictReader(f)
            assert list(next(csv_dict_reader).values()) == [
                "",
                "",
                "",
                "",
                "acq_0",
                "my_acq_id",
                "",
                "",
                "",
                "test error",
                "True",
                "['my', 'search', 'key', 'list']",
            ]
