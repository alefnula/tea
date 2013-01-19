__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import os
import logging
# tea imports
from tea.process import execute

logger = logging.getLogger(__name__)



class Hg(object):
    def __init__(self, repository):
        self.repository = repository

    def _hg(self, operation, *args):
        data = {
            'path' : self.repository.path,
            'uri'  : self.repository.uri,
            'muri' : self.repository.muri,
        }
        pargs = map(lambda a: a % data, args)
        largs = map(lambda a: a.replace('%(uri)s', '%(muri)s') % data, args)
        logger.info('Execute: hg %s %s' % (operation, ' '.join(largs)))
        status = 1
        output = ''
        error  = ''
        try:
            status, output, error = execute('hg', operation, *pargs)
            logger.info('Exit Code %s: hg %s %s' % (status, operation, ' '.join(largs)))
        except:
            logger.exception('hg failed! Exception thrown!')
        return status, output, error

    def identify(self):
        '''Returns the working directory revision
        return values:
            - None: error occured
            - str: revision in format {rev}:{node}
        '''
        if os.path.isdir(self.repository.path):
            status, output, _ = self._hg('identify', '--repository', '%(path)s', '-in')
            if status != 0: return None
            full, short = output.split()
            return '%s:%s' % (short, full)
        else:
            return None

    def clone(self):
        '''Clone repository'''
        return self._hg('clone', '%(uri)s', '%(path)s')

    def incoming(self):
        '''Checks if there are incoming changes in the repository'''
        return self._hg('incoming', '--repository', '%(path)s', '%(uri)s')

    def outgoing(self):
        '''Checks if there are outgoing changes in the repository'''
        return self._hg('outgoing', '--repository', '%(path)s', '%(uri)s')

    def update(self, revision=None, clean=True):
        '''Performs update clean on repository'''
        args = ['--repository', '%(path)s'] + (
               ['--clean'] if clean else[]) + (
               ['--rev', revision] if revision is not None else [])
        return self._hg('update', *args)

    def pull(self):
        '''Pushes the changes into remote repository'''
        if os.path.isdir(self.repository.path):
            return self._hg('pull', '--repository', '%(path)s', '%(uri)s')
        else:
            return self.clone()

    def fetch(self, message='Automated merge.'):
        '''Fetches the repository'''
        if os.path.isdir(self.repository.path):
            args = [
                '--repository', '%(path)s',
                '--config', 'extensions.hgext.fetch=',
                '--message', message, '%(uri)s',
            ]
            status, output, error = self._hg('fetch', *args)
            if 'no changes found' in output:
                status = 1
            elif 'outstanding uncommitted changes' in error:
                status = 2
            return status, output, error
        else:
            return self.clone()

    def commit(self, message, addremove=False, amend=False, user=None):
        '''Commits'''
        args = ['--repository', '%(path)s', '--message', message] + (
               ['--addremove'] if addremove else []) + (
               ['--amend'] if amend else []) + (
               ['--user', user] if user is not None else [])
        return self._hg('commit', *args)

    def push(self):
        '''Pushes the changes into remote repository'''
        return self._hg('push', '--repository', '%(path)s', '%(uri)s')

    def revert(self):
        '''Restores repository to earlier state'''
        return self._hg('revert', '--repository', '%(path)s', '--all', '--no-backup')

    def purge(self, purge_all=False, only_print=False):
        '''Restores repository to earlier state.'''
        args = ['--repository', '%(path)s'] + (
               # purge is extension, this will enable it if it is not enabled in mercurial.ini
               ['--config', 'extensions.hgext.purge=']) + (
               ['--all'] if purge_all else []) + (
               ['--print'] if only_print else [])
        return self._hg('purge', *args)

    def tag(self, tag, local=False, message=None, user=None):
        '''Tag repository with specified tag'''
        args = ['--repository', '%(path)s', tag] + (
               ['--local'] if local else []) + (
               ['--message', message] if message is not None else []) + (
               ['--user', user] if user is not None else [])
        return self._hg('tag', *args)
    
    def status(self, show_all=False, modified=False, added=False, removed=False,
                     deleted=False, clean=False, unknown=False, ignored=False,
                     no_status=False, copies=False):
        '''Perform hg status'''  
        args = ['--repository', '%(path)s'] + (
               ['--all'] if show_all else []) + (
               ['--modified'] if modified else []) + (
               ['--added'] if added else []) + (
               ['--removed'] if removed else []) + (
               ['--deleted'] if deleted else []) + (
               ['--clean'] if clean else []) + (
               ['--unknown'] if unknown else []) + (
               ['--ignored'] if ignored else []) + (
               ['--no-status'] if no_status else []) + (
               ['--copies'] if copies else [])
        status, output, error = self._hg('status', *args)
        if status == 0:
            status = 0 if output.strip() == '' else 1
        return status, output, error
    
    def log(self, no=3, follow=False, copies=False, graph=False, user=None, branch=None):
        '''Perform hg log'''  
        args = ['--limit', str(no), '--repository', '%(path)s'] + (
               ['--follow'] if follow else []) + (
               ['--copies'] if copies else []) + (
               ['--graph'] if graph else []) + (
               ['--user'] + user if user is not None else []) + (
               ['--branch'] + branch if branch is not None else [])
        return self._hg('log', *args)
        
    def diff(self, revision=None, change=None, text=False, git=False, 
                   show_function=False, reverse=False, ignore_all_space=False, 
                   ignore_space_change=False, ignore_blank_lines=False, 
                   unified=-1, stat=False):
        ''' Perform hg diff'''
        args = ['--repository', '%(path)s'] + (
               ['--rev', revision] if revision is not None else []) + (
               ['--change', change] if change is not None else []) + (
               ['--text'] if text else []) + (
               ['--git'] if git else []) + (
               ['--show-function'] if show_function else []) + (
               ['--reverse'] if reverse else []) + (
               ['--ignore--all-space'] if ignore_all_space else []) + (
               ['--ignore-space-change'] if ignore_space_change else []) + (
               ['--ignore-blank-lines'] if ignore_blank_lines else []) + (
               ['--unified', str(unified)] if unified != -1 else []) + (
               ['--stat'] if stat else [])
        return self._hg('diff', *args)
        
    def branch(self, name=None):
        ''' Perform hg branch'''
        return self._hg('branch', '--repository', '%(path)s', *([] if name is None else [name]))
    
    def branches(self):
        ''' Perfrom hg branches'''
        return self._hg('branches', '--repository', '%(path)s')
        
    def heads(self):
        ''' Perform hg heads'''
        return self._hg('heads', '--repository', '%(path)s')

    def churn(self, sort=False, changesets=False, diffstat=False):
        args = ['--repository', '%(path)s'] + (
               # churn is extension, this will enable it if it is not enabled in mercurial.ini
               ['--config', 'extensions.hgext.churn=']) + (
               ['--sort'] if sort else []) + (
               ['--changesets'] if changesets else []) + (
               ['--diffstat'] if diffstat else [])
        return self._hg('churn', *args)