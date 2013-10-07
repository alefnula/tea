__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '02 August 2012'
__copyright__ = 'Copyright (c) 2012 Viktor Kerkez'

import json
import logging
from collections import defaultdict
# tornado imports
from tornado import web

logger = logging.getLogger(__name__)


STATUS_MESSAGES = defaultdict(lambda: 'UNKNOWN', **{
    200: 'OK',
    400: 'BAD_REQUEST',
    401: 'UNAUTHORIZED',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    500: 'INTERNAL_ERROR',
    501: 'NOT_IMPLEMENTED',
    502: 'BAD_GATEWAY',
    503: 'SERVICE_UNAVAILABLE',
    504: 'GATEWAY_TIMEOUT',
})


class JsonHandler(web.RequestHandler):
    def prepare(self):
        try:
            self.request.json_body = (json.loads(self.request.body)
                                      if self.request.body else None)
        except Exception:
            self.send_error(400, message='Error parsing JSON')

    def send_error(self, status_code=500, **kwargs):
        if self._headers_written:
            logger.error('Cannot send error response after headers written')
            if not self._finished:
                self.finish()
            return
        self.clear()
        message = kwargs.get('message', 'Error')
        if status_code == 500:
            message = 'Server error'
        logger.warning('[%s] %s' % (status_code, message))
        self.respond(message, status_code)

    def respond(self, obj, status_code=200):
        self.set_status(status_code)
        content_type = 'application/json'
        data = json.dumps({
            'status': STATUS_MESSAGES[status_code],
            'message': obj
        }, default=lambda obj: (obj.__json__() if hasattr(obj, '__json__')
                                else obj))
        # Check if it's jsonp request
        callback = self.get_argument('callback', None)
        if callback is not None:
            content_type = 'application/javascript'
            data = '%s(%s);' % (callback, data)
        self.set_header('Content-Type', content_type)
        return self.finish(data)
