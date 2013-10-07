__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '01 January 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

import re
try:
    import urlparse
    from urllib2 import quote as urlquote
except ImportError:
    import urllib.parse as urlparse
    urlquote = urlparse.quote


# tea imports
from tea.scm.hg import Hg
from tea.scm.git import Git

NETLOC_RE = re.compile(
    '^(?:(?P<username>[^:]+)(?:\:(?P<password>[^@]+))?@)?(?P<netloc>.*)$'
)


def set_uri(uri, **kwargs):
    try:
        parsed = urlparse.urlparse(uri)
        match = NETLOC_RE.match(parsed.netloc)
        if match:
            gd = match.groupdict()
            for key, value in kwargs.items():
                gd[key] = value
            if gd['username'] and gd['password']:
                netloc = '%(username)s:%(password)s@%(netloc)s' % gd
            elif gd['username']:
                netloc = '%(username)s@%(netloc)s' % gd
            else:
                netloc = '%(netloc)s' % gd
            parsed = parsed._replace(netloc=netloc)
        return urlparse.urlunparse(parsed)
    except:
        return uri


class Repository(object):
    HG = 'hg'
    GIT = 'git'

    def __init__(self, name, path=None, source=None, username=None,
                 password=None, repo_type=HG):
        self.name = name
        self.path = path
        self.source = source
        self.username = None if username is None else urlquote(username)
        self.password = None if password is None else urlquote(password)
        self._uri = None
        self._muri = None
        self.repo_type = repo_type
        if self.repo_type == Repository.HG:
            self.scm = Hg(self)
        else:
            self.scm = Git(self)

    @property
    def uri(self):
        """Returns the full URI with username and password"""
        if self._uri is None:
            self._uri = set_uri(self.source, username=self.username,
                                password=self.password)
        return self._uri

    @property
    def muri(self):
        """Returns a full URI with username, but password is massked"""
        if self._muri is None:
            self._muri = set_uri(self.source, username=self.username,
                                 password='*****')
        return self._muri

    def __str__(self):
        return self.name

    def __repr__(self):
        return 'Repository <%s>' % self.name

    def __serialize__(self):
        return {
            'name': self.name,
            'type': 'Repository',
            'path': self.path,
            'source': self.source,
        }

    def __getattr__(self, attr):
        if hasattr(self.scm, attr):
            return getattr(self.scm, attr)
        raise AttributeError(attr)
