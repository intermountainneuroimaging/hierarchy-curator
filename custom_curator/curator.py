import abc
import flywheel
from custom_curator.utils import Container


class Curator(abc.ABC):
    def __init__(self, depth_first=True):
        """An abstract class to be implemented in the input python file."""
        self.depth_first = depth_first
        self.input_file_one = None
        self.input_file_two = None
        self.input_file_three = None
        self.context = None
        self.client = None

    def curate_container(self, container: Container):
        """Curates a generic container.

        Args:
            container (Container): A Flywheel container.
        """
        if hasattr(container, "container_type"):
            container_type = container.container_type
            if container_type == "project":
                self.curate_project(container)
            elif container_type == "subject":
                self.curate_subject(container)
            elif container_type == "session":
                self.curate_session(container)
            elif container_type == "acquisition":
                self.curate_acquisition(container)
            elif container_type == "file":
                self.curate_file(container)
            else:
                self.curate_analysis(container)
        else:
            # element is a file and has no children
            self.curate_file(container)

    @abc.abstractmethod
    def curate_project(self, project: flywheel.Project):
        """Updates a project.

        Args:
            project (flywheel.Project): The project object to curate
        """
        raise NotImplementedError

    @abc.abstractmethod
    def curate_subject(self, subject: flywheel.Subject):
        """Updates a subject.

        Args:
            subject (flywheel.Subject): The subject object to curate
        """
        raise NotImplementedError

    @abc.abstractmethod
    def curate_session(self, session: flywheel.Session):
        """Updates a session.

        Args:
            session (flywheel.Session): The session object to curate
        """
        raise NotImplementedError

    @abc.abstractmethod
    def curate_acquisition(self, acquisition: flywheel.Acquisition):
        """Updates an acquisition.

        Args:
            acquisition (flywheel.Acquisition): The acquisition object to
                curate
        """
        raise NotImplementedError

    @abc.abstractmethod
    def curate_analysis(self, analysis: flywheel.AnalysisOutput):
        """Updates an analysis.

        Args:
            analysis (flywheel.Analysis): The analysis object to curate
        """
        raise NotImplementedError

    @abc.abstractmethod
    def curate_file(self, file_: flywheel.FileEntry):
        """Updates a file.

        Args:
            file_ (flywheel.FileEntry): The file entry object to curate
        """
        raise NotImplementedError

    def validate_project(self, project: flywheel.Project):
        """Validates if a project has been correctly curated.

        Args:
            project (flywheel.Project): The project object to validate

        Returns:
            bool: Whether or not the project is curated correctly
        """
        return False

    def validate_subject(self, subject: flywheel.Subject):
        """Validates if a subject has been correctly curated.

        Args:
            subject (flywheel.Subject): The subject object to validate

        Returns:
            bool: Whether or not the subject is curated correctly
        """
        return False

    def validate_session(self, session: flywheel.Session):
        """Validates if a session has been correctly curated.

        Args:
            session (flywheel.Session): The session object to validate

        Returns:
            bool: Whether or not the session is curated correctly
        """
        return False

    def validate_acquisition(self, acquisition: flywheel.Acquisition):
        """Validates if a acquisition has been correctly curated.

        Args:
            acquisition (flywheel.Acquisition): The acquisition object to
                validate

        Returns:
            bool: Whether or not the acquisition is curated correctly
        """
        return False

    def validate_analysis(self, analysis: flywheel.AnalysisOutput):
        """Validates if a analysis has been correctly curated.

        Args:
            analysis (flywheel.Analysis): The analysis object to validate

        Returns:
            bool: Whether or not the analysis is curated correctly
        """
        return False

    def validate_file(self, file_: flywheel.FileEntry):
        """Validates if a file_ has been correctly curated.

        Args:
            file_ (flywheel.FileEntry): The file entry object to validate

        Returns:
            bool: Whether or not the file_ is curated correctly
        """
        return False
