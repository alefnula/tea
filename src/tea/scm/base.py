__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '05 August 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import abc
from tea.utils import six


class SCM(six.with_metaclass(abc.ABCMeta)):
    """SCM is the base class for all source code management classes

    It defines all the methods that will be available for every SCM.
    It's subclasses will implement the specific things for every SCM
    in particular.
    """

    @abc.abstractmethod
    def __init__(self, repository):
        """Constructor receives a Repository instance

        :type repository: :class:`tea.scm.repository.Repository`
        """

    @abc.abstractmethod
    def clone(self):
        """Clone a remote repository"""

    @abc.abstractmethod
    def status(self):
        """Displays the current status of the repository"""
