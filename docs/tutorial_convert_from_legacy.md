# Tutorial: Convert a legacy script (1.0) to work with 2.0

## Objective and task definition

The objective of this script is to
take in a project CSV that and update the hierarchy according to that CSV.

The CSV has the columns:

* STUDY_ID: corresponds to project id
* STUDY_NAME: corresponds to project name
* patientId: corresponds to subject name
* siteId: ID of the site the subject was screened at
* screeningId: Anonymized screening ID
* bp_d: blood pressure (diastolic) at time of session
* bp_s: blood pressure (systolic) at time of session
* hr: heart rate at time of session
* timestamp: session timestamp

So our generalized list of tasks are:

1. Update project metadata
    a. set project StudyID metadata
    b. set project StudyName metadata
2. For each subject
    a. Set the subject's patientId
    b. Set the subject's screeningId
    c. Update the metadata to set "curated" to True
    d. Ensure subject type is "human"
3. For each session
    a. Update timestamp to reflect that in the CSV
    b. Update the blood pressure and heart rate values
4. For each acquisition
    a. Update the timestamp to the timestamp value in the CSV

## Translate from legacy to new version

Let's look at how the [legacy-script](./examples/legacy-script.py)
accomplishes these tasks:

### Project level

The existing script uses this function to curate the project:

```python
def curate_project(self, project):
    # Create patient and session info dictionaries
    # For use in curating subjects/sessions
    self.patient_info_dict = {}
    self.session_info_dict = {}
    self.index_file = None

    # CSV with first three columns patientId, screeningId, and siteId
    df = pd.read_csv(self.input_file_one)
    self.index_file = df

    # Set project custom information.
    log.info(
        "Setting StudyID (%s) and StudyName (%s)",
        df.iloc[0].studyId,
        df.iloc[0].studyName,
    )
    # Tasks 1a and 1b
    project.update_info(
        {"StudyID": df.iloc[0].STUDY_ID, "StudyName": df.iloc[0].STUDY_NAME}
    )
`
    # Extract patient (subject) data.
    group_by_patient = df.groupby("patientId")

    for patient_id, group in group_by_patient:
        first_el = group.iloc[0]
        p_id = str(patient_id)
        s_id = str(first_el.screeningId)

        # Choose site ID from the first visit.
        site_id = df.loc[pd.to_datetime(group.date).idxmin(), "siteId"]

        self.patient_info_dict[p_id] = {
            "patientId": p_id,
            "screeningId": s_id,
            "siteId": site_id,
        }
        # Extract visit (session) information
        by_visit = group.groupby(["visit", "date"])
        for visit_id, v_group in by_visit:
            session_key = p_id + "-" + visit_id
            self.session_info_dict[visit_id] = {
                "bp_d": v_group.bp_d,
                "bp_s": v_group.bp_s,
                "hr": v_group.hr,
                "timestamp": v_group.timestamp,
            }
```

In addition to doing the two tasks for project level, we are also
doing a ton of work to populate subject and session dictionaries

To get this into the new format we need to do a few things:

* `self.patient_info_dict` needs to be stored under `self.data`, so
we'll name it `self.data['subject_info']`
* similarly, `self.session_info_dict` needs to be stored under `self.data`, so
we'll name it `self.data['session_info']`
* We need to change `self.input_file_one` -> `self.additional_input_one`
* We need to use the `self.open_input` context manager to open the file
to make it thread-safe

```python
def curate_project(self, project):
    # Create patient and session info dictionaries
    # For use in curating subjects/sessions
    # Store under self.data
    self.data = {
        'subject_info': {},
        'session_info': {},
        'index_file': {}
    }
    df = None
    # Switch to use self.open_file to be thread-safe
    # Switch from input_file_one to additional_input_one
    with self.open_file(self.additional_input_one) as fp:
        df = pd.read_csv(fp)
        self.data['index_file'] = df

    # Set project custom information.
    log.info(
        "Setting StudyID (%s) and StudyName (%s)",
        df.iloc[0].studyId,
        df.iloc[0].studyName,
    )
    # Tasks 1a and 1b
    project.update_info(
        {"StudyID": df.iloc[0].STUDY_ID, "StudyName": df.iloc[0].STUDY_NAME}
    )
`
    # Extract patient (subject) data.
    group_by_patient = df.groupby("patientId")

    for patient_id, group in group_by_patient:
        first_el = group.iloc[0]
        p_id = str(patient_id)
        s_id = str(first_el.screeningId)

        # Choose site ID from the first visit.
        site_id = df.loc[pd.to_datetime(group.date).idxmin(), "siteId"]

        self.data['subject_info'][p_id] = {
            "patientId": p_id,
            "screeningId": s_id,
            "siteId": site_id,
        }
        # Extract visit (session) information
        by_visit = group.groupby(["visit", "date"])
        for visit_id, v_group in by_visit:
            session_key = p_id + "-" + visit_id
            self.data['session_info'][visit_id] = {
                "bp_d": v_group.bp_d,
                "bp_s": v_group.bp_s,
                "hr": v_group.hr,
                "timestamp": v_group.timestamp,
            }
```

### Subject level

The existing script uses this function to curate the subject:

```python
def curate_subject(self, subject):

    if subject.label in self.patient_info_dict:
        pat_info = self.patient_info_dict.get(subject.label)
        log.info("Updating subject %s", pat_info["patientId"])
        subject.update(type="human")
        subject.update_info(
            {
                "patientId": pat_info["patientId"],
                "screeningId": pat_info["screeningId"],
                "curated": True,
            }
        )
```

For this all we need to do is update `self.patient_info_dict` ->
`self.data['subject_info']`

```python
def curate_subject(self, subject):
    if subject.label in self.data['subject_info']:
        pat_info = self.data['subject_info'].get(subject.label)
        log.info("Updating subject %s", pat_info["patientId"])
        subject.update(type="human")
        subject.update_info(
            {
                "patientId": pat_info["patientId"],
                "screeningId": pat_info["screeningId"],
                "curated": True,
            }
        )
```

### Session level

The existing script uses this function to curate the subject:

```python
def curate_session(self, session):
    session_key = session.subject.label + "-" + session.label
    if session_key in self.session_info_dict:
        session_info = self.session_info_dict.get(session_key)
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
```

There is only one thing we need to do to change this into the new format:

* `self.session_info_dict` -> `self.data['session_info']`

However, we can also improve the functionality of this by either moving
the acquisition update into the `curate_acquisition` method, or by only
curating down to the session level, here is how we could do either

### Move functionality to `curate_acquisition`

In order to move the functionality to `curate_acquisition`, we need to store
the session timestamp on the class in `curate_session` and then ensure we
are curating depth-first so that the current value is guarenteed to be the
session parent of that acquisition:

```python
def __init__(self, **kwargs):
   super().__init__(**kwargs)
   self.config.depth_first = True

# ...

def curate_session(self, session):
    session_key = session.subject.label + "-" + session.label
    if session_key in self.session_info_dict:
        # ... rest of curate_session above
        session.update_info(session_dict)
        self.data['timestamp'] = tstamp
    else:
        self.data['timestamp'] = None

def curate_acquisition(self, acquisition):
    if self.data['timestamp']:
        acquisition.update(timestamp=self.data['timestamp'])
```

Since we are curating depth-first, we can set a variable timestamp
on `self.data` and then have access to that value in the acquisitions
under the session for which we've set `self.data['timestamp']`

### Keep functionality in `curate_session` but stop after session level

```python
def __init__(self, **kwargs):
   super().__init__(**kwargs) 
    # Don't queue session children
   self.config.stop_level = 'session'

def curate_session(self, session):
    session_key = session.subject.label + "-" + session.label
    if session_key in self.data['session_info']:
        session_info = self.data['session_info'].get(session_key)
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
```

This method keeps the `curate_session` almost exactly the same, but
improves execution speed since no acquisitions are curated, the children
of sessions aren't queued.

## Other changes and best practices

### Backoff

You may notice there are decorators over most functions, these are
essentially mechanisms to retry on any transient errors:

```python
def is_not_server_error(exception):
    """A giveup function to be passed as giveup parameter to backoff.on_exception
        Give up for status codes below 500, backoff for >= 500 (server error).
    Args:
        exception (flywheel.rest.ApiException): a flywheel API exception.
    Returns:
        bool: whether to raise rather than backing off.
    """
    return False if (exception.status >= 500) else True

# ...
@backoff.on_exception(
    backoff.expo,
    flywheel.rest.ApiException,
    max_time=300,
    giveup=is_not_server_error,
)
```

This decorator retries a given function if a Flywheel API error is thrown,
but only if it is a transient error.  If it is a user error, it will
immediately give up.  This mechanism makes the script robust running when
there are many gears running, or the system is under high load.

### Delete unused curate methods

In the [legacy-script](./examples/legacy-script.py) you may notice that there
are a few curate methods that only have one statement that is `pass`.  In the
new version, you don't need to specifically include those, so you can remove
any method that just has `pass` in it.

### Extend HierarchyCurator

Instead of

```python
import curator

class Curator(curator.Curator):
    ...
```

You will have to extend the
`flywheel_gear_toolkit.utils.curator.HierarchyCurator`:

```python
from flywheel_gear_toolkit.utils.curator import HierarchyCurator

class Curator(HierarchyCurator):
    ...
```

## End

That's it!  Make sure you check out the [final script](./examples/legacy-translated.py)
