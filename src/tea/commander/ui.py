__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '18 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import abc
import getpass

from tea.console.color import cprint, Color
from tea.parsing import ConsoleFormatter



class UserInterface(object):
    '''Abstract class representing user interface object for commander.
    
    Commander Application can be provided with a custom implementation
    of the UserInterface so it can be used in different environments, i.e.
    console, gui, web application...
    
    Every command will receive a UserInterface object in it's constructor
    and can call all methods to provide user feedback.
    '''
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self):
        '''Initialization method'''
        self._formatter = None
    
    def get_formatter(self):
        return self._formatter
    def set_formatter(self, value):
        self._formatter = value
    formatter = abc.abstractproperty(get_formatter, set_formatter)

    @abc.abstractmethod
    def ask(self, message=None, password=False):
        '''Ask for user input
        
        This method should ask the user for input, presenting to user
        a message and returning a string. Also if password is set to
        True, user should not be able to see what he types
        '''
    
    @abc.abstractmethod
    def info(self, message):
        '''Present an information message to the user'''
    
    @abc.abstractmethod
    def warn(self, message):
        '''Present a warning message to the user'''
    
    @abc.abstractmethod
    def error(self, message):
        '''Present an error message to the user'''
    
    @abc.abstractmethod
    def report(self, obj, status=0, data=None):
        '''This is the central part of the user interface. Every command
        does some amount of work. This work can be representet in steps.
        Command should report to the user interface on every finished
        step so the user can have a live stream of information from the
        command. Every report contains three parts::
        
        :param obj     The object on which the operation is performed. The
                       object should be either a dictionary or have a
                       __serialize__ method that serializes it to dict
        :param status  Status of the operation. No status is considered to
                       be successfull or unsuccessfull. It's just an integer
                       that represents the status of the operation.
        :param data    Custom data proveded by the command. This also has to
                       be either dict or has a __serialize__ method, that
                       serializes it to dict.
        '''




class ConsoleUserInterface(UserInterface):
    '''Simple implemntation of the user interface inteted for usage in
    console applications.
    
    If no other UserInterface implementation is proveded to commander
    it will use this user interface
    '''
    def __init__(self):
        self._report = []
        self._formatter = ConsoleFormatter()
    
    def get_formatter(self):
        return self._formatter
    def set_formatter(self, value):
        self._formatter = value
    formatter = property(get_formatter, set_formatter)
        
    def ask(self, message=None, password=False):
        message = message or ''
        if password:
            return getpass.getpass(message)
        return raw_input(message)

    def info(self, message):
        cprint('%s\n' % message, Color.blue)
    
    def warn(self, message):
        cprint('%s\n' % message, Color.yellow)

    def error(self, message):
        cprint('%s\n' % message, Color.red)
    
    def report(self, obj, status=0, data=None):
        data = {
            'object' : obj,
            'status' : status,
            'data'   : data,
        }
        self._report.append(data)
        self.formatter.format(data)
