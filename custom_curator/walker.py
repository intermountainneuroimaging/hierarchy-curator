import abc
import logging
from custom_curator.utils import Container

log = logging.getLogger(__name__)
log.setLevel("INFO")


class Walker(abc.ABC):
    """A class to walk the container hierarchically"""

    def __init__(self, root: Container):
        """
        Args:
            root (Container): The root container
        """
        self.list = [root]

    @abc.abstractmethod
    def add(self, element: Container):
        """Adds an element to the data structure.

        Args:
            element (object): Element to add to the walker
        """
        raise NotImplementedError

    @abc.abstractmethod
    def next(self):
        """Returns the next element from the walker.

        Returns:
            Container|FileEntry
        """
        raise NotImplementedError

    def get_children(self, element: Container):
        """Returns children of the element.

        Args:
            element (Container)

        Returns:
            list: the children of the element
        """
        children = []
        container_type = element.container_type

        if container_type == "file":
            return children

        children += element.files or []

        # Make sure that the analyses attribute is a list before iterating
        if container_type != "analysis" and isinstance(element.analyses, list):
            children += [analysis.reload() for analysis in element.analyses]
            if container_type == "project":
                children += [subject.reload() for subject in element.subjects()]
            elif container_type == "subject":
                children += [session.reload() for session in element.sessions()]
            elif container_type == "session":
                children += [
                    acquisition.reload() for acquisition in element.acquisitions()
                ]

        log.debug("Children of element %s are:\n%s", element.id, children)
        return children

    def is_empty(self):
        """Returns True if the walker is empty.

        Returns:
            bool
        """
        return len(self.list) == 0

    def walk(self):
        """Walks the hierarchy from a root container.

        Yields:
            Container|FileEntry
        """

        while not self.is_empty():
            yield self.next()


class DepthFirstWalker(Walker):
    def add(self, element: Container):
        """Adds an element to the data structure.

        Args:
            element (object): Element to add to the walker
        """
        self.list.append(element)

    def next(self):
        """Returns the next element from the walker and adds its children.

        Returns:
            Container|FileEntry
        """
        next_element = self.list.pop()
        log.debug("Element returned is %s", type(next_element))
        for child in self.get_children(next_element):
            self.add(child)
        return next_element


class BreadthFirstWalker(Walker):
    def add(self, element: Container):
        """Adds an element to the data structure.

        Args:
            element (object): Element to add to the walker
        """
        self.list.append(element)

    def next(self):
        """Returns the next element from the walker and adds its children.

        Returns:
            Container|FileEntry
        """
        next_element = self.list.pop(0)
        for child in self.get_children(next_element):
            self.add(child)
        return next_element
