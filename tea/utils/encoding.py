__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '27 November 2009'
__copyright__ = 'Copyright (c) 2009 Viktor Kerkez'

from tea.utils import six


def smart_text(s, encoding='utf-8', strings_only=False, errors='strict'):
    """Returns a unicode object representing 's'. Treats bytes using the
    'encoding' codec.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, six.text_type):
        return s
    if strings_only and not isinstance(s, six.string_types):
        return s
    if not isinstance(s, six.string_types):
        if hasattr(s, '__unicode__'):
            s = s.__unicode__()
        else:
            if six.PY3:
                if isinstance(s, six.binary_type):
                    s = six.text_type(s, encoding, errors)
                else:
                    s = six.text_type(s)
            else:
                s = six.text_type(six.binary_type(s), encoding, errors)
    else:
        # Note: We use .decode() here, instead of six.text_type(s, encoding,
        # errors), so that if s is a SafeBytes, it ends up being a
        # SafeText at the end.
        s = s.decode(encoding, errors)
    return s


def smart_bytes(s, encoding='utf-8', strings_only=False, errors='strict'):
    """Returns a bytes version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, six.binary_type):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)
    if strings_only and not isinstance(s, six.text_type):
        return s
    if not isinstance(s, six.string_types):
        try:
            if six.PY3:
                return six.text_type(s).encode(encoding)
            else:
                return six.binary_type(s)
        except UnicodeEncodeError:
            return six.text_type(s).encode(encoding, errors)
    else:
        return s.encode(encoding, errors)
