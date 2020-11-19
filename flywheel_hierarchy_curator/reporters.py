"""A module to store reporter classes"""
from collections import namedtuple
import csv
import logging
import os
from pathlib import Path
from typing import Union, List

from custom_curator import utils

log = logging.getLogger(__name__)


class CuratorReporter:
    """Class to logs and appends to an output csv.

    Example:
    >>> # Create a CuratorReporter object and assign it as an attribute of Curator
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
        self, output_dir: utils.PathLike, container_label: str, fieldnames: list = None,
    ):
        """
        Args
            output_folder (PathLike): A output directory
            container_label (str): A project label
        """
        self.output_dir = output_dir
        self.container_label = container_label
        self._fieldnames = fieldnames
        self.error_log_name = self.container_label + "_curation_report.csv"
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
    >>> # Create a CuratorErrorReporter object and assign it as an attribute of Curator
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
    ...             self.error_reporter.write_session_error(
    ...                 err_str=str(exc),
    ...                 subject_label=session.subject.label,
    ...                 subject_id=session.subject.id,
    ...                 session_label=session.label,
    ...                 session_id=session.id,
    ...            )
    """

    # namedtuple that defines the csv row
    ErrorRecord = namedtuple(
        "ErrorRecord",
        [
            "subject_label",
            "subject_id",
            "session_label",
            "session_id",
            "acquisition_label",
            "acquisition_id",
            "analysis_label",
            "analysis_id",
            "file_name",
            "error",
            "resolved",
            "search_key",
        ],
    )

    def __init__(self, output_dir: Union[str, os.PathLike, Path], container_label: str):
        """
        Args
            output_folder (str): Should be set using attribute
                flywheel.GearContext.ouput_dir
            container_label (str): Should be set using attribute flywheel.<container>.label
        """
        self.output_dir = output_dir
        self.container_label = container_label
        self.error_log_name = self.container_label + "_curation_error_log.csv"
        self.output_path_full = os.path.join(self.output_dir, self.error_log_name)

        # Create the output csv file
        log.info(
            f"Creating '{self.error_log_name}' in output path " f"'{self.output_dir}'"
        )
        with open(self.output_path_full, "w") as output_file:
            csv_dict_writer = csv.DictWriter(
                output_file, fieldnames=self.ErrorRecord._fields
            )
            csv_dict_writer.writeheader()

    def write_subject_error(
        self,
        subject_label: str,
        subject_id: str,
        resolved: str = "False",
        search_key="",
        err_str: str = "",
        err_list: list = None,
    ):

        self.append_error(
            err_str=err_str,
            err_list=err_list,
            subject_label=subject_label,
            subject_id=subject_id,
            file_name="",
            resolved=resolved,
            search_key=search_key,
        )

    def write_session_error(
        self,
        session_label: str,
        session_id: str,
        subject_label: str = "",
        subject_id: str = "",
        resolved: str = "False",
        search_key="",
        err_str: str = "",
        err_list: list = None,
    ):

        self.append_error(
            err_str=err_str,
            err_list=err_list,
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

    def write_acquisition_error(
        self,
        acquisition_label: str,
        acquisition_id: str,
        subject_label: str = "",
        subject_id: str = "",
        session_label: str = "",
        session_id: str = "",
        resolved: str = "False",
        search_key="",
        err_str: str = "",
        err_list: list = None,
    ):

        self.append_error(
            err_str=err_str,
            err_list=err_list,
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

    def write_analysis_error(
        self,
        analysis_label: str,
        analysis_id: str,
        subject_label: str = "",
        subject_id: str = "",
        session_label: str = "",
        session_id: str = "",
        acquisition_label: str = "",
        acquisition_id: str = "",
        resolved: str = "False",
        search_key="",
        err_str: str = "",
        err_list: list = None,
    ):

        self.append_error(
            err_str=err_str,
            err_list=err_list,
            subject_label=subject_label,
            subject_id=subject_id,
            session_label=session_label,
            session_id=session_id,
            acquisition_label=acquisition_label,
            acquisition_id=acquisition_id,
            analysis_label=analysis_label,
            analysis_id=analysis_id,
            file_name="",
            resolved=resolved,
            search_key=search_key,
        )

    def write_file_error(
        self,
        file_name: str,
        subject_label: str = "",
        subject_id: str = "",
        session_label: str = "",
        session_id: str = "",
        acquisition_label: str = "",
        acquisition_id: str = "",
        analysis_label: str = "",
        analysis_id: str = "",
        resolved: str = "False",
        search_key="",
        err_str: str = "",
        err_list: list = None,
    ):

        self.append_error(
            err_str=err_str,
            err_list=err_list,
            subject_label=subject_label,
            subject_id=subject_id,
            session_label=session_label,
            session_id=session_id,
            acquisition_label=acquisition_label,
            acquisition_id=acquisition_id,
            analysis_label=analysis_label,
            analysis_id=analysis_id,
            file_name=file_name,
            resolved=resolved,
            search_key=search_key,
        )

    @staticmethod
    def _validate_error(err_str: str, err_list: list):
        """Returns a list of validation errors for `err_str` and `err_list`"""
        validation_error = []
        if not err_str and not err_list:
            validation_error.append(
                f"Either err_str or err_list must be defined."
                f"Currently: \nerr_str: {err_str}\nerr_list: {err_list}"
            )

        if err_list and not isinstance(err_list, list):
            validation_error.append(f"err_list must be a list. {err_list} found.")

        if err_str and err_list:
            validation_error.append(
                f"err_str and err_list cannot be both defined. "
                f"Currently: \nerr_str: {err_str}\nerr_list: {err_list}"
            )

        return validation_error

    def append_error(
        self,
        subject_label: str = "",
        subject_id: str = "",
        session_label: str = "",
        session_id: str = "",
        acquisition_label: str = "",
        acquisition_id: str = "",
        analysis_label: str = "",
        analysis_id: str = "",
        file_name: str = "",
        resolved: str = "False",
        search_key="",
        err_str: str = "",
        err_list: list = None,
    ):
        """Append errors to the error output csv."""
        validation_error = self._validate_error(err_str, err_list)
        if validation_error:
            val_err_str = "\n".join(validation_error)
            raise ValueError(f"Validation error(s) found: {val_err_str}")

        errors = [err_str] if err_str else err_list
        error_record_list = []
        for error in errors:
            error_record_list.append(
                self.ErrorRecord(
                    subject_label=subject_label,
                    subject_id=subject_id,
                    session_label=session_label,
                    session_id=session_id,
                    acquisition_label=acquisition_label,
                    acquisition_id=acquisition_id,
                    analysis_label=analysis_label,
                    analysis_id=analysis_id,
                    file_name=file_name,
                    error=error,
                    resolved=resolved,
                    search_key=search_key,
                )
            )
        self.write_error(error_record_list)

    def write_error(self, errors_list: list):
        if not errors_list:
            raise ValueError(
                f"errors_list must contain a list of at least "
                f"one dictionary to write out, got '{errors_list}'"
            )

        with open(self.output_path_full, "a") as output_file:
            csv_dict_writer = csv.DictWriter(
                output_file, fieldnames=self.ErrorRecord._fields
            )
            csv_dict_writer.writerows(map(lambda x: x._asdict(), errors_list))
