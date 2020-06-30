"""A module to store reporter classes"""
import os
import csv
import logging
from pathlib import Path
from typing import Union, List
from collections import namedtuple

from custom_curator import utils

log = logging.getLogger(__name__)


class CuratorReporter:
    """Logs and appends in an output csv.

    Example:
    # Create a CuratorReporter object and assign it as an attribute of Curator
    >>> from custom_curator import curator
    >>> from flywheel_gear_toolkit import GearToolkitContext
    >>> class Curator(curator.Curator):
    ...     def __init__(self):
    ...         super(Curator, self).__init__(depth_first=True)
    ...         self.reporter = None
    ...
    ...     def curate_project(self, project):
    ...         gear_context = GearToolkitContext()
    ...         self.reporter = CuratorReporter(
    ...             output_dir=gear_context.output_dir,
    ...             project_label=project.label)
    ...         self.reporter.append({
    ...             'ID': project.id,
    ...             'label': project.label,
    ...             'comment': 'BLM'
    ...         })
    """

    def __init__(
        self, output_dir: utils.PathLike, project_label: str, fieldnames: list = None,
    ):
        """
        Args
            output_folder (PathLike): A output directory
            project_name (str): A project label
        """
        self.output_dir = output_dir
        self.project_name = project_label
        self._fieldnames = fieldnames
        self.error_log_name = self.project_name + "_curation_report.csv"
        self.output_path_full = Path(self.output_dir) / self.error_log_name

        # Create the output csv file
        if self._fieldnames:
            self._create_output_file()

    def _create_output_file(self):
        log.info("Creating %s in output path %s", self.error_log_name, self.output_dir)
        with open(self.output_path_full, "w") as output_file:
            csv_dict_writer = csv.DictWriter(output_file, fieldnames=self._fieldnames)
            csv_dict_writer.writeheader()

    def _validate_data_header(self, data: dict):
        if not self._fieldnames:
            self._fieldnames = list(data.keys())
            self._create_output_file()
            return True
        else:
            return all([f in data.keys() for f in self._fieldnames])

    def append(self, data: List[dict]):
        """Append data to csv report

        Args:
            data (list): List of dictionary of key/value to be reported.
        """
        if not data or not isinstance(data, list):
            raise ValueError(
                f"data must contain a list of at least "
                f"one dictionary to write out, got '{data}'"
            )

        for d in data:
            if not self._validate_data_header(d):
                raise ValueError(
                    f"Dictionary keys must match report fieldnames, "
                    f"'got '{d.keys()}' instead"
                )

        with open(self.output_path_full, "a") as output_file:
            new_rows = [{f: d[f] for f in self._fieldnames} for d in data]
            csv_dict_writer = csv.DictWriter(output_file, fieldnames=self._fieldnames)
            csv_dict_writer.writerows(new_rows)


class CuratorErrorReporter:
    """
    Logs curation subject, session, acquisition, and file errors and saves
    them in an output csv.

    Call a method that corresponds to the type of object (e.g.,
    write_subject_error() for reporting a subject error). A
    CuratorErrorReporter object should be instantiated in Curator's
    curate_project() method and saved as one of Curator's attributes.

    Example:
    # Create a CuratorErrorReporter object and assign it as an attribute of Curator
    >>> from custom_curator import curator
    >>> from flywheel_gear_toolkit import GearToolkitContext
    >>> class Curator(curator.Curator):
    ...     def __init__(self):
    ...         super(Curator, self).__init__(depth_first=True)
    ...         self.error_reporter = None
    ...
    ...     def curate_project(self, project):
    ...         gear_context = GearToolkitContext()
    ...         self.error_reporter = CuratorErrorReporter(
    ...             output_dir=gear_context.output_dir,
    ...             project_label=project.label)
    ...
    ...     def curate_session(self, session):
    ...         try:
    ...             # something that may raise
    ...         except Exception as exc:
    ...             self.error_reporter.write_project_error(
    ...                 errors_list=[],
    ...                 err_str=str(exc),
    ...                 subject_label=session.subject.id,
    ...                 subject_id=session.subject.id,
    ...                 session_label=session.label,
    ...                 session_id=session.id,
    ...                 acquisition_label="",
    ...                 acquisition_id="",
    ...                 file_name="",
    ...                 resolved="False",
    ...                 search_key="",
    ...            )
    """

    ErrorLogger = namedtuple(
        "ErrorLogger",
        [
            "subject_label",
            "subject_id",
            "session_label",
            "session_id",
            "acquisition_label",
            "acquisition_id",
            "file_name",
            "error",
            "resolved",
            "sear_key",
        ],
    )
    """
    ErrorLogger is a namedtuple used instead of an OrderedDict to easily
    access values using dot notation.
    """

    def __init__(self, output_dir: Union[str, os.PathLike, Path], project_label: str):
        """
        Args
            output_folder (str): Should be set using attribute
                flywheel.GearContext.ouput_dir
            project_name (str): Should be set using attribute flywheel.Project.label
        """
        self.output_dir = output_dir
        self.project_name = project_label
        self.error_log_name = self.project_name + "_curation_error_log.csv"
        self.output_path_full = os.path.join(self.output_dir, self.error_log_name)

        # Create the output csv file
        log.info(
            f"Creating '{self.error_log_name}' in output path " f"'{self.output_dir}'"
        )
        with open(self.output_path_full, "w") as output_file:
            csv_dict_writer = csv.DictWriter(
                output_file, fieldnames=self.ErrorLogger._fields
            )
            csv_dict_writer.writeheader()

    def write_subject_error(
        self,
        errors_list: list,
        err_str: str,
        subject_label: str,
        subject_id: str,
        resolved: str = "False",
        search_key="",
    ):

        self.append_write_error(
            errors_list=errors_list,
            err_str=err_str,
            subject_label=subject_label,
            subject_id=subject_id,
            session_label="",
            session_id="",
            acquisition_label="",
            acquisition_id="",
            file_name="",
            resolved=resolved,
            search_key=search_key,
        )

    def write_session_error(
        self,
        errors_list: list,
        err_str: str,
        subject_label: str,
        subject_id: str,
        session_label: str,
        session_id: str,
        resolved: str = "False",
        search_key="",
    ):

        self.append_write_error(
            errors_list=errors_list,
            err_str=err_str,
            subject_label=subject_label,
            subject_id=subject_id,
            session_label=session_label,
            session_id=session_id,
            acquisition_label="",
            acquisition_id="",
            file_name="",
            resolved=resolved,
            search_key=search_key,
        )

    def write_acq_error(
        self,
        errors_list: list,
        err_str: str,
        subject_label: str,
        subject_id: str,
        session_label: str,
        session_id: str,
        acquisition_label: str,
        acquisition_id: str,
        resolved: str = "False",
        search_key="",
    ):

        self.append_write_error(
            errors_list=errors_list,
            err_str=err_str,
            subject_label=subject_label,
            subject_id=subject_id,
            session_label=session_label,
            session_id=session_id,
            acquisition_label=acquisition_label,
            acquisition_id=acquisition_id,
            file_name="",
            resolved=resolved,
            search_key=search_key,
        )

    def write_file_error(
        self,
        errors_list: list,
        err_str: str,
        subject_label: str,
        subject_id: str,
        session_label: str,
        session_id: str,
        acquisition_label: str,
        acquisition_id: str,
        file_name: str,
        resolved: str = "False",
        search_key="",
    ):

        self.append_write_error(
            errors_list=errors_list,
            err_str=err_str,
            subject_label=subject_label,
            subject_id=subject_id,
            session_label=session_label,
            session_id=session_id,
            acquisition_label=acquisition_label,
            acquisition_id=acquisition_id,
            file_name=file_name,
            resolved=resolved,
            search_key=search_key,
        )

    def append_write_error(
        self,
        errors_list: list,
        err_str: str,
        subject_label,
        subject_id: str,
        session_label: str,
        session_id: str,
        acquisition_label: str,
        acquisition_id: str,
        file_name: str,
        resolved: str,
        search_key="",
    ):
        """Append an error to the error list and write it out to the output csv."""

        log.error(err_str)
        errors_list.append(
            self.ErrorLogger(
                subject_label=subject_label,
                subject_id=subject_id,
                session_label=session_label,
                session_id=session_id,
                acquisition_label=acquisition_label,
                acquisition_id=acquisition_id,
                file_name=file_name,
                error=err_str,
                resolved=resolved,
                sear_key=search_key,
            )
        )
        self.write_error_log(errors_list)

    def write_error_log(self, errors_list: list):
        # errors_list is a dictionary. Use its keys as the headers for the
        # csv file
        if not errors_list:
            raise ValueError(
                f"errors_list must contain a list of at least "
                f"one dictionary to write out, got '{errors_list}'"
            )

        with open(self.output_path_full, "a") as output_file:
            csv_dict_writer = csv.DictWriter(
                output_file, fieldnames=self.ErrorLogger._fields
            )

            # Convert named tuple object to an OrderedDict
            errors_list = [tup._asdict() for tup in errors_list]
            csv_dict_writer.writerows(errors_list)
