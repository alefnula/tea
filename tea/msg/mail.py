"""Simple and complete library for sending emails."""

__all__ = [
    "SMTPConnection",
    "EmailMessage",
    "EmailMultiAlternatives",
    "send_mail",
    "send_mass_mail",
]


import os
import time
import socket
import random
import smtplib
import logging
import mimetypes
from email import charset as Charset
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.encoders import encode_base64
from email.utils import formatdate, parseaddr, formataddr

from tea.utils.html import strip_tags
from tea.utils.encoding import smart_text, smart_bytes


logger = logging.getLogger(__name__)


# Don't BASE64-encode UTF-8 messages so that we avoid unwanted attention from
# some spam filters.
Charset.add_charset("utf-8", Charset.SHORTEST, Charset.QP, "utf-8")

# Default MIME type to use on attachments (if it is not explicitly given
# and cannot be guessed).
DEFAULT_ATTACHMENT_MIME_TYPE = "application/octet-stream"

# Default charset
DEFAULT_CHARSET = "utf-8"


# Cache the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName(object):
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, "_fqdn"):
            self._fqdn = socket.getfqdn()
        return self._fqdn


DNS_NAME = CachedDnsName()


# Copied from Python standard library, with the following modifications:
# * Used cached hostname for performance.
# * Added try/except to support lack of getpid() in Jython (#5496).
def make_msgid(idstring=None, utc=False):
    """Return a string suitable for RFC 2822 compliant Message-ID.

    E.g: <20020201195627.33539.96671@nightshade.la.mastaler.com>

    Optional idstring if given is a string used to strengthen the
    uniqueness of the message id.
    """
    if utc:
        timestamp = time.gmtime()
    else:
        timestamp = time.localtime()
    utcdate = time.strftime("%Y%m%d%H%M%S", timestamp)
    try:
        pid = os.getpid()
    except AttributeError:
        # No getpid() in Jython, for example.
        pid = 1
    randint = random.randrange(100000)
    if idstring is None:
        idstring = ""
    else:
        idstring = "." + idstring
    idhost = DNS_NAME
    msgid = "<%s.%s.%s%s@%s>" % (utcdate, pid, randint, idstring, idhost)
    return msgid


class BadHeaderError(ValueError):
    pass


def forbid_multi_line_headers(name, val):
    """Forbid multi-line headers, to prevent header injection."""
    val = smart_text(val)
    if "\n" in val or "\r" in val:
        raise BadHeaderError(
            "Header values can't contain newlines "
            "(got %r for header %r)" % (val, name)
        )
    try:
        val = val.encode("ascii")
    except UnicodeEncodeError:
        if name.lower() in ("to", "from", "cc"):
            result = []
            for item in val.split(", "):
                nm, addr = parseaddr(item)
                nm = str(Header(nm, DEFAULT_CHARSET))
                result.append(formataddr((nm, str(addr))))
            val = ", ".join(result)
        else:
            val = Header(val, DEFAULT_CHARSET)
    else:
        if name.lower() == "subject":
            val = Header(val)
    return name, val


class SafeMIMEText(MIMEText):
    def __setitem__(self, name, val):
        name, val = forbid_multi_line_headers(name, val)
        MIMEText.__setitem__(self, name, val)


class SafeMIMEMultipart(MIMEMultipart):
    def __setitem__(self, name, val):
        name, val = forbid_multi_line_headers(name, val)
        MIMEMultipart.__setitem__(self, name, val)


class SMTPConnection(object):
    """Wrapper that manages the SMTP network connection."""

    def __init__(
        self,
        host=None,
        port=None,
        username=None,
        password=None,
        use_tls=None,
        fail_silently=False,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = (use_tls is not None) and use_tls
        self.fail_silently = fail_silently
        self.connection = None

    def open(self):
        """Ensure we have a connection to the email server.

        Returns whether or not a new connection was required (True or False).
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False
        try:
            # If local_hostname is not specified, socket.getfqdn() gets used.
            # For performance, we use the cached FQDN for local_hostname.
            self.connection = smtplib.SMTP(
                self.host, self.port, local_hostname=DNS_NAME.get_fqdn()
            )
            if self.use_tls:
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()
            if self.username and self.password:
                self.connection.login(self.username, self.password)
            return True
        except Exception as e:
            logger.error(
                "Error trying to connect to server %s:%s: %s",
                self.host,
                self.port,
                e,
            )
            if not self.fail_silently:
                raise

    def close(self):
        """Close the connection to the email server."""
        try:
            try:
                self.connection.quit()
            except socket.sslerror:
                # This happens when calling quit() on a TLS connection
                # sometimes.
                self.connection.close()
            except Exception as e:
                logger.error(
                    "Error trying to close connection to server " "%s:%s: %s",
                    self.host,
                    self.port,
                    e,
                )
                if self.fail_silently:
                    return
                raise
        finally:
            self.connection = None

    def send_messages(self, messages):
        """Send one or more EmailMessage objects.

        Returns:
             int: Number of email messages sent.
        """
        if not messages:
            return
        new_conn_created = self.open()
        if not self.connection:
            # We failed silently on open(). Trying to send would be pointless.
            return
        num_sent = 0
        for message in messages:
            sent = self._send(message)
            if sent:
                num_sent += 1
        if new_conn_created:
            self.close()
        return num_sent

    def _send(self, message):
        """Send an email.

        Helper method that does the actual sending.
        """
        if not message.recipients():
            return False
        try:
            self.connection.sendmail(
                message.sender,
                message.recipients(),
                message.message().as_string(),
            )
        except Exception as e:
            logger.error(
                "Error sending a message to server %s:%s: %s",
                self.host,
                self.port,
                e,
            )
            if not self.fail_silently:
                raise
            return False
        return True


class EmailMessage(object):
    """Container for email information."""

    content_subtype = "plain"
    multipart_subtype = "mixed"
    encoding = None  # None => use settings default

    def __init__(
        self,
        subject="",
        body="",
        sender=None,
        to=None,
        cc=None,
        bcc=None,
        attachments=None,
        headers=None,
        connection=None,
    ):
        """Initialize a single email message.

        (It can be sent to multiple recipients.)

        All strings used to create the message can be unicode strings (or UTF-8
        bytestrings). The SafeMIMEText class will handle any necessary encoding
        conversions.
        """
        if to:
            if not isinstance(to, (list, tuple)):
                raise AssertionError('"to" argument must be a list or tuple')
            self.to = list(to)
        else:
            self.to = []
        if cc:
            if not isinstance(cc, (list, tuple)):
                raise AssertionError('"cc" argument must be a list or tuple')
            self.cc = list(cc)
        else:
            self.cc = []
        if bcc:
            if not isinstance(bcc, (list, tuple)):
                raise AssertionError('"bcc" argument must be a list or tuple')
            self.bcc = list(bcc)
        else:
            self.bcc = []
        self.sender = sender
        self.subject = subject
        self.body = body
        self.attachments = []
        for attachment in attachments or []:
            if isinstance(attachment, (tuple, list)):
                self.attach(*attachment)
            else:
                self.attach(attachment)
        self.extra_headers = headers or {}
        self.connection = connection

    def get_connection(self, fail_silently=False):
        if not self.connection:
            self.connection = SMTPConnection(fail_silently=fail_silently)
        return self.connection

    def message(self):
        encoding = self.encoding or DEFAULT_CHARSET
        msg = SafeMIMEText(
            smart_bytes(self.body, DEFAULT_CHARSET),
            self.content_subtype,
            encoding,
        )
        if self.attachments:
            body_msg = msg
            msg = SafeMIMEMultipart(_subtype=self.multipart_subtype)
            if self.body:
                msg.attach(body_msg)
            for attachment in self.attachments:
                if isinstance(attachment, MIMEBase):
                    msg.attach(attachment)
                else:
                    msg.attach(self._create_attachment(*attachment))
        msg["Subject"] = self.subject
        msg["From"] = self.sender
        msg["To"] = ", ".join(self.to)
        msg["Cc"] = ", ".join(self.cc)
        # Email header names are case-insensitive (RFC 2045), so we have to
        # accommodate that when doing comparisons.
        header_names = [key.lower() for key in self.extra_headers]
        if "date" not in header_names:
            msg["Date"] = formatdate()
        if "message-id" not in header_names:
            msg["Message-ID"] = make_msgid()
        for name, value in self.extra_headers.items():
            msg[name] = value
        return msg

    def recipients(self):
        """Return a list of all recipients of the email.

        Includes direct addressees as well as Bcc entries.
        """
        return self.to + self.cc + self.bcc

    def send(self, fail_silently=False):
        """Send the email message."""
        return self.get_connection(fail_silently).send_messages([self])

    def attach(self, filename=None, content=None, mimetype=None):
        """Attache a file with the given filename and content.

        The filename can be omitted (useful for multipart/alternative messages)
        and the mimetype is guessed, if not provided.

        If the first parameter is a MIMEBase subclass it is inserted directly
        into the resulting message attachments.
        """
        if isinstance(filename, MIMEBase):
            assert content is None and mimetype is None
            self.attachments.append(filename)
        elif content is None and os.path.isfile(filename):
            self.attach_file(filename, mimetype)
        else:
            assert content is not None
            self.attachments.append((filename, content, mimetype))

    def attach_file(self, path, mimetype=None):
        """Attache a file from the filesystem."""
        filename = os.path.basename(path)
        content = open(path, "rb").read()
        self.attach(filename, content, mimetype)

    def _create_attachment(self, filename, content, mimetype=None):
        """Convert the filename, content, mimetype triple to attachment."""
        if mimetype is None:
            mimetype, _ = mimetypes.guess_type(filename)
            if mimetype is None:
                mimetype = DEFAULT_ATTACHMENT_MIME_TYPE
        basetype, subtype = mimetype.split("/", 1)
        if basetype == "text":
            attachment = SafeMIMEText(
                smart_bytes(content, DEFAULT_CHARSET), subtype, DEFAULT_CHARSET
            )
        else:
            # Encode non-text attachments with base64.
            attachment = MIMEBase(basetype, subtype)
            attachment.set_payload(content)
            encode_base64(attachment)
        if filename:
            attachment.add_header(
                "Content-Disposition", "attachment", filename=filename
            )
        return attachment


class EmailMultiAlternatives(EmailMessage):
    """Email message with multipart/alternative content.

    A version of EmailMessage that makes it easy to send
    multipart/alternative messages. For example, including text and HTML
    versions of the text is made easier.
    """

    multipart_subtype = "alternative"

    def attach_alternative(self, content, mimetype=None):
        """Attach an alternative content representation."""
        self.attach(content=content, mimetype=mimetype)


def send_mail(
    subject,
    sender,
    to,
    message,
    html_message=None,
    cc=None,
    bcc=None,
    attachments=None,
    host=None,
    port=None,
    auth_user=None,
    auth_password=None,
    use_tls=False,
    fail_silently=False,
):
    """Send a single email to a recipient list.

    All members of the recipient list will see the other recipients in the 'To'
    field.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    if message is None and html_message is None:
        raise ValueError("Either message or html_message must be provided")
    if message is None:
        message = strip_tags(html_message)
    connection = SMTPConnection(
        host=host,
        port=port,
        username=auth_user,
        password=auth_password,
        use_tls=use_tls,
        fail_silently=fail_silently,
    )
    # Convert the to field just for easier usage
    if isinstance(to, str):
        to = [to]
    if html_message is None:
        email = EmailMessage(
            subject=subject,
            body=message,
            sender=sender,
            to=to,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            connection=connection,
        )
    else:
        email = EmailMultiAlternatives(
            subject=subject,
            body=message,
            sender=sender,
            to=to,
            cc=cc,
            bcc=bcc,
            attachments=attachments,
            connection=connection,
        )
        email.attach_alternative(html_message, "text/html")
    return email.send()


def send_mass_mail(
    datatuple, fail_silently=False, auth_user=None, auth_password=None
):
    """Send multiple emails to multiple recipients.

    Given a datatuple of (subject, message, sender, recipient_list), sends
    each message to each recipient list. Returns the number of e-mails sent.

    If auth_user and auth_password are set, they're used to log in.

    Note: The API for this method is frozen. New code wanting to extend the
    functionality should use the EmailMessage class directly.
    """
    connection = SMTPConnection(
        username=auth_user, password=auth_password, fail_silently=fail_silently
    )
    messages = [
        EmailMessage(subject, message, sender, recipient)
        for subject, message, sender, recipient in datatuple
    ]
    return connection.send_messages(messages)
