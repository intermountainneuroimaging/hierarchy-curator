import abc
import logging
from collections import deque
from typing import List

from custom_curator.utils import Container

log = logging.getLogger(__name__)
log.setLevel("INFO")


class Walker:
    """A class to walk the container hierarchically"""

    def __init__(self, root: Container, depth_first: bool = True):
        """
        Args:
            root (Container): The root container
        """
        self.deque = deque([root])
        self.depth_first = depth_first

    def next(self):
        """Returns the next element from the walker and adds its children.

        Returns:
            Container|FileEntry
        """
        if self.depth_first:
            next_element = self.deque.pop()
        else:
            next_element = self.deque.popleft()

        log.debug(f"Element returned is {next_element.container_type}")

        self.queue_children(next_element)

        return next_element

    def add(self, element: Container):
        """Adds an element to the data structure.

        Args:
            element (object): Element to add to the walker
        """
        self.deque.append(element)

    def add_many(self, elements: List[Container]):
        self.deque.extend(elements)

    def queue_children(self, element: Container):
        """Returns children of the element.

        Args:
            element (Container)

        Returns:
            list: the children of the element
        """
        container_type = element.container_type

        # No children of files
        if container_type == "file":
            return

        log.info(f"Queueing children for container {element.label or element.code}")

        self.extend(element.files or [])

        # Make sure that the analyses attribute is a list before iterating
        if container_type != "analysis" and isinstance(element.analyses, list):
            # TODO: Determine what containers have non-list element.analyses
            self.deque.extend(element.analyses)
            if container_type == "project":
                self.deque.extend(element.subjects())
            elif container_type == "subject":
                self.deque.extend(element.sessions())
            elif container_type == "session":
                self.deque.extend(element.acquisitions())

    def is_empty(self):
        """Returns True if the walker is empty.

        Returns:
            bool
        """
        return len(self.deque) == 0

    def walk(self):
        """Walks the hierarchy from a root container.

        Yields:
            Container|FileEntry
        """

        while not self.is_empty():
            yield self.next()
