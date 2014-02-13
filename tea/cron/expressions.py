import re
from calendar import monthrange
from tea.utils import six


def asint(value):
    if value is not None:
        if isinstance(value, six.string_types):
            return int(value, 10)
        return int(value)
    return None

WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


class AllExpression(object):
    value_re = re.compile(r'\*(?:/(?P<step>\d+))?$')

    def __init__(self, step=None):
        self.step = asint(step)
        if self.step == 0:
            raise ValueError('Increment must be higher than 0')

    def get_next_value(self, date, field):
        start = field.get_value(date)
        minval = field.get_min(date)
        maxval = field.get_max(date)
        start = max(start, minval)

        if not self.step:
            next_value = start
        else:
            distance_to_next = (self.step - (start - minval)) % self.step
            next_value = start + distance_to_next

        if next_value <= maxval:
            return next_value

    def __str__(self):
        if self.step:
            return '*/%d' % self.step
        return '*'

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.step)


class RangeExpression(AllExpression):
    value_re = re.compile(
        r'(?P<first>\d+)(?:-(?P<last>\d+))?(?:/(?P<step>\d+))?$'
    )

    def __init__(self, first, last=None, step=None):
        super(RangeExpression, self).__init__(step)
        first = asint(first)
        last = asint(last)
        if last is None and step is None:
            last = first
        if last is not None and first > last:
            raise ValueError('The minimum value in a range must not be '
                             'higher than the maximum')
        self.first = first
        self.last = last

    def get_next_value(self, date, field):
        start = field.get_value(date)
        minval = field.get_min(date)
        maxval = field.get_max(date)

        # Apply range limits
        minval = max(minval, self.first)
        if self.last is not None:
            maxval = min(maxval, self.last)
        start = max(start, minval)
        if not self.step:
            next_value = start
        else:
            distance_to_next = (self.step - (start - minval)) % self.step
            next_value = start + distance_to_next
        if next_value <= maxval:
            return next_value

    def __str__(self):
        if self.last != self.first and self.last is not None:
            range_str = '%d-%d' % (self.first, self.last)
        else:
            range_str = str(self.first)

        if self.step:
            return '%s/%d' % (range_str, self.step)
        return range

    def __repr__(self):
        args = [str(self.first)]
        if self.last != self.first and self.last is not None or self.step:
            args.append(str(self.last))
        if self.step:
            args.append(str(self.step))
        return "%s(%s)" % (self.__class__.__name__, ', '.join(args))


class WeekdayRangeExpression(RangeExpression):
    value_re = re.compile(r'(?P<first>[a-z]+)(?:-(?P<last>[a-z]+))?',
                          re.IGNORECASE)

    def __init__(self, first, last=None):
        try:
            first_num = WEEKDAYS.index(first.lower())
        except ValueError:
            raise ValueError('Invalid weekday name "%s"' % first)

        if last:
            try:
                last_num = WEEKDAYS.index(last.lower())
            except ValueError:
                raise ValueError('Invalid weekday name "%s"' % last)
        else:
            last_num = None

        RangeExpression.__init__(self, first_num, last_num)

    def __str__(self):
        if self.last != self.first and self.last is not None:
            return '%s-%s' % (WEEKDAYS[self.first], WEEKDAYS[self.last])
        return WEEKDAYS[self.first]

    def __repr__(self):
        args = ["'%s'" % WEEKDAYS[self.first]]
        if self.last != self.first and self.last is not None:
            args.append("'%s'" % WEEKDAYS[self.last])
        return "%s(%s)" % (self.__class__.__name__, ', '.join(args))


class LastDayOfMonthExpression(AllExpression):
    value_re = re.compile(r'last', re.IGNORECASE)

    def __init__(self):
        pass

    def get_next_value(self, date, field):
        return monthrange(date.year, date.month)[1]

    def __str__(self):
        return 'last'

    def __repr__(self):
        return "%s()" % self.__class__.__name__
