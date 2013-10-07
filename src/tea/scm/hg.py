__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import logging
from tea.process import execute
from tea.scm.base import SCM


logger = logging.getLogger(__name__)


class Hg(SCM):
    def __init__(self, repository):
        self.repository = repository

    def _hg(self, operation, *args):
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
        logger.info('Execute: hg %s %s' % (operation, ' '.join(largs)))
        status = 1
        output = ''
        error = ''
        try:
            status, output, error = execute('hg', operation, *pargs)
            logger.info('Exit Code %s: hg %s %s',
                        status, operation, ' '.join(largs))
        except:
            logger.exception('hg failed! Exception thrown!')
        return status, output, error

    def _hgr(self, operation, *args):
        """Execute hg command, on existing repository.

        Same as _hg but adds --repository %(path) to the command line,
        """
        return self._hg(operation, '--repository', '%(path)s', *args)

    def clone(self):
        """Clone repository"""
        return self._hg('clone', '%(uri)s', '%(path)s')

    def identify(self):
        """Returns the working directory revision
        return values:
            - None: error occurred
            - str: revision in format {rev}:{node}
        """
        if os.path.isdir(self.repository.path):
            status, output, _ = self._hgr('parents', '--template',
                                          '{rev}:{node}\n')
            if status != 0:
                return None
            return output.strip()
        else:
            return None

    def incoming(self):
        """Checks if there are incoming changes in the repository"""
        return self._hgr('incoming', '%(uri)s')

    def outgoing(self):
        """Checks if there are outgoing changes in the repository"""
        return self._hgr('outgoing', '%(uri)s')

    def update(self, revision=None, clean=True):
        """Performs update clean on repository"""
        args = ((['--rev', revision] if revision is not None else []) +
                (['--clean'] if clean else []))
        return self._hgr('update', *args)

    def pull(self):
        """Pushes the changes into remote repository"""
        if os.path.isdir(self.repository.path):
            return self._hgr('pull', '%(uri)s')
        else:
            return self.clone()

    def fetch(self, message='Automated merge.'):
        """Fetches the repository"""
        if os.path.isdir(self.repository.path):
            status, output, error = self._hgr(
                'fetch', '--config', 'extensions.hgext.fetch=',
                '--message', message, '%(uri)s')
            if 'no changes found' in output:
                status = 1
            elif 'outstanding uncommitted changes' in error:
                status = 2
            return status, output, error
        else:
            return self.clone()

    def commit(self, message, addremove=False, amend=False, user=None):
        """Commits"""
        args = (['--message', message] +
                (['--addremove'] if addremove else []) +
                (['--amend'] if amend else []) +
                (['--user', user] if user is not None else []))
        return self._hgr('commit', *args)

    def push(self, new_branch=False):
        """Pushes the changes into remote repository"""
        args = ['--new-branch'] if new_branch else []
        return self._hgr('push', '%(uri)s', *args)

    def revert(self):
        """Restores repository to earlier state"""
        return self._hgr('revert', '--all', '--no-backup')

    def purge(self, purge_all=False, only_print=False):
        """Restores repository to earlier state."""

        args = ['--all'] if purge_all else [] + (
               ['--print'] if only_print else [])
        # purge is extension, this will enable it if it is not enabled
        # in mercurial.ini
        return self._hgr('purge', '--config', 'extensions.hgext.purge=', *args)

    def tag(self, tag, local=False, message=None, user=None):
        """Tag repository with specified tag"""
        args = ((['--local'] if local else []) +
                (['--message', message] if message is not None else []) +
                (['--user', user] if user is not None else []))
        return self._hgr('tag', tag, *args)

    def status(self, show_all=False, modified=False, added=False,
               removed=False, deleted=False, clean=False, unknown=False,
               ignored=False, no_status=False, copies=False):
        """Perform hg status"""
        args = ((['--all'] if show_all else []) +
                (['--modified'] if modified else []) +
                (['--added'] if added else []) +
                (['--removed'] if removed else []) +
                (['--deleted'] if deleted else []) +
                (['--clean'] if clean else []) +
                (['--unknown'] if unknown else []) +
                (['--ignored'] if ignored else []) +
                (['--no-status'] if no_status else []) +
                (['--copies'] if copies else []))
        status, output, error = self._hgr('status', *args)
        if status == 0:
            status = 0 if output.strip() == '' else 1
        return status, output, error

    def log(self, no=3, follow=False, copies=False, graph=False, user=None,
            branch=None):
        """Perform hg log"""
        args = ((['--follow'] if follow else []) +
                (['--copies'] if copies else []) +
                (['--graph'] if graph else []) +
                (['--user'] + user if user is not None else []) +
                (['--branch'] + branch if branch is not None else []))
        return self._hgr('log', '--limit', str(no), *args)

    def diff(self, revision=None, change=None, text=False, git=False,
             show_function=False, reverse=False, ignore_all_space=False,
             ignore_space_change=False, ignore_blank_lines=False,
             unified=-1, stat=False):
        """Perform hg diff"""
        args = ((['--rev', revision] if revision is not None else []) +
                (['--change', change] if change is not None else []) +
                (['--text'] if text else []) +
                (['--git'] if git else []) +
                (['--show-function'] if show_function else []) +
                (['--reverse'] if reverse else []) +
                (['--ignore--all-space'] if ignore_all_space else []) +
                (['--ignore-space-change'] if ignore_space_change else []) +
                (['--ignore-blank-lines'] if ignore_blank_lines else []) +
                (['--unified', str(unified)] if unified != -1 else []) +
                (['--stat'] if stat else []))
        return self._hgr('diff', *args)

    def branch(self, name=None):
        """Perform hg branch"""
        return self._hgr('branch', *([] if name is None else [name]))

    def branches(self):
        """Perfrom hg branches"""
        return self._hgr('branches')

    def heads(self):
        """Perform hg heads"""
        return self._hgr('heads')

    def churn(self, sort=False, changesets=False, diffstat=False):
        args = ((['--sort'] if sort else []) +
                (['--changesets'] if changesets else []) +
                (['--diffstat'] if diffstat else []))
        # churn is extension, this will enable it if it is not enabled
        # in mercurial.ini
        return self._hgr('churn', '--config', 'extensions.hgext.churn=', *args)
