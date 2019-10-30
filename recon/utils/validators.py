import re


# Gingerly lifted from Django 1.3.x:
# https://github.com/django/django/blob/stable/1.3.x/django/core/validators.py#L45
# <3 y'all!
#
# Restolen from colander
# https://github.com/Pylons/colander/blob/master/colander/__init__.py
URL_REGEX = (
    # {http,ftp}s:// (not required)
    r"^((?:http|ftp)s?://)?"
    # Domain
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+"
    r"(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
    # Localhost
    r"localhost|"
    # IPv6 address
    r"\[[a-f0-9:]+\]|"
    # IPv4 address
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    # Optional port
    r"(?::\d+)?"
    # Path
    r"(?:/?|[/?]\S+)$"
)


# Regex for email addresses.
#
# Stolen from the WhatWG HTML spec:
# https://html.spec.whatwg.org/multipage/input.html#e-mail-state-(type=email)
#
# If it is good enough for browsers, it is good enough for us!
#
# Restolen from colander
# https://github.com/Pylons/colander/blob/master/colander/__init__.py
EMAIL_RE = (
    r"^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


class ValidationException(Exception):
    def __init__(self, input, validator):
        Exception.__init__(self, f"{input} does not look like a valid {validator}")


class Validator(object):
    """ Regular expression validator
    """

    def __init__(self, regex, validator=None, flags=0):
        if isinstance(regex, str):
            self.match_object = re.compile(regex, flags)
        else:
            self.match_object = regex
        self.validator = validator

    def __call__(self, value):
        if self.match_object.match(value) is None:
            raise ValidationException(value, self.validator)


class EmailValidator(Validator):
    """Email address validator
    """

    def __init__(self):
        email_regex = EMAIL_RE
        super(EmailValidator, self).__init__(email_regex, "email")


test_email_val = EmailValidator()
test_email_val("test@mail.com")
