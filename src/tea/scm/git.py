__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import logging
from tea.process import execute
from tea.scm.base import SCM

logger = logging.getLogger(__name__)


class Git(SCM):
    def __init__(self, repository):
        self.repository = repository

    def _git(self, operation, *args):
        """Execute the hg command substituting variables like repository path,
        remote repository URI, masked URI (masking password for logging)
        """
        data = {
            'path': self.repository.path,
            'uri': self.repository.uri,
            'muri': self.repository.muri,
        }
        pargs = [a % data for a in args]
        largs = [a.replace('%(uri)s', '%(muri)s') % data for a in args]
        logger.info('Execute: git %s %s' % (operation, ' '.join(largs)))
        status = 1
        output = ''
        error = ''
        try:
            status, output, error = execute('git', operation, *pargs)
            logger.info('Exit Code %s: hg %s %s',
                        status, operation, ' '.join(largs))
        except:
            logger.exception('git failed! Exception thrown!')
        return status, output, error

    def _gitr(self, operation, *args):
        """Execute hg command, on existing repository.

        Same as _hg but adds --repository %(path) to the command line,
        """
        return self._hg(operation, '--work-tree', '%(path)s', '--git-dir',
                        os.path.join('%(path)s', '.git'), *args)

    def clone(self):
        """Clone repository"""
        return self._git('clone', '%(uri)s', '%(path)s')

    def status(self, show_all=False, modified=False, added=False,
               removed=False, deleted=False, clean=False, unknown=False,
               ignored=False, no_status=False, copies=False):
        """Perform git status"""
        status, output, error = self._gitr('status', '-s')
        if status == 0:
            status = 0 if output.strip() == '' else 1
        return status, output, error
