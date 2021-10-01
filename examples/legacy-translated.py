import logging

import flywheel
import pandas as pd
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("root")

import backoff


def is_not_server_error(exception):
    """A giveup function to be passed as giveup parameter to backoff.on_exception
        Give up for status codes below 500, backoff for >= 500 (server error).
    Args:
        exception (flywheel.rest.ApiException): a flywheel API exception.
    Returns:
        bool: whether to raise rather than backing off.
    """
    return False if (exception.status >= 500) else True


class Curator(HierarchyCurator):
    def __init__(self, **kwargs):
        # Install backoff
        super().__init__(**kwargs, extra_packages=["backoff"])
        # curate depth first
        self.config.depth_first = True
        # Don't queue up session children
        self.config.stop_level = "session"

    def curate_project(self, project):
        # Create patient and session info dictionaries
        # For use in curating subjects/sessions
        # Store under self.data
        self.data = {"subject_info": {}, "session_info": {}, "index_file": {}}
        df = None
        # Switch to use self.open_input to be thread-safe
        # Switch from input_file_one to additional_input_one
        with self.open_input(self.additional_input_one) as fp:
            df = pd.read_csv(fp)
            self.data["index_file"] = df

        # Set project custom information.
        log.info(
            "Setting StudyID (%s) and StudyName (%s)",
            df.iloc[0].studyId,
            df.iloc[0].studyName,
        )
        # Tasks 1a and 1b
        project.update_info(
            {"StudyID": df.iloc[0].studyId, "StudyName": df.iloc[0].studyName}
        )
        # Extract patient (subject) data.
        group_by_patient = df.groupby("patientId")

        for patient_id, group in group_by_patient:
            first_el = group.iloc[0]
            p_id = str(patient_id)
            s_id = str(first_el.screeningId)

            # Choose site ID from the first visit.
            site_id = df.loc[pd.to_datetime(group.date).idxmin(), "siteId"]

            self.data["subject_info"][p_id] = {
                "patientId": p_id,
                "screeningId": s_id,
                "siteId": site_id,
            }
            # Extract visit (session) information
            by_visit = group.groupby(["visit", "date"])
            for (visit_id, date), v_group in by_visit:
                session_key = p_id + "-" + visit_id
                self.data["session_info"][visit_id] = {
                    "bp_d": v_group.bp_d,
                    "bp_s": v_group.bp_s,
                    "hr": v_group.hr,
                    "timestamp": v_group.timestamp,
                }

    @backoff.on_exception(
        backoff.expo,
        flywheel.rest.ApiException,
        max_time=300,
        giveup=is_not_server_error,
    )
    def curate_subject(self, subject):
        if subject.label in self.data["subject_info"]:
            pat_info = self.data["subject_info"].get(subject.label)
            log.info("Updating subject %s", pat_info["patientId"])
            subject.update(type="human")
            subject.update_info(
                {
                    "patientId": pat_info["patientId"],
                    "screeningId": pat_info["screeningId"],
                    "curated": True,
                }
            )

    @backoff.on_exception(
        backoff.expo,
        flywheel.rest.ApiException,
        max_time=300,
        giveup=is_not_server_error,
    )
    def curate_session(self, session):
        session_key = session.subject.label + "-" + session.label
        if session_key in self.data["session_info"]:
            session_info = self.data["session_info"].get(session_key)
            log.info("Updating session %s", session_key)
            tstamp = session_info["timestamp"]
            session.update(timestamp=tstamp)
            session_dict = {
                "bp_d": session_info["bp_d"],
                "bp_s": session_info["bp_s"],
                "hr": session_info["hr"],
            }
            session.update_info(session_dict)
            for acq in session.acquisitions():
                acq.update(timestamp=tstamp)
