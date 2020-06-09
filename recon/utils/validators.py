import re


class ValidationException(Exception):
    def __init__(self, input, validator):
        Exception.__init__(self, f"Input failed {validator} validation: {input}")


class BaseValidator(object):

    def __init__(self, regex, validator=None, flags=0):
        if isinstance(regex, str):
            self.match_object = re.compile(regex, flags)
        else:
            self.match_object = regex
        self.validator = validator

    def validate(self, value):
        if self.match_object.match(value) is None:
            raise ValidationException(value, self.validator)


class CompanyValidator(BaseValidator):

    def __init__(self):
        regex = (
            r".*"
        )
        super(CompanyValidator, self).__init__(regex, 'company')


class CoordinateValidator(BaseValidator):

    def __init__(self):
        regex = (
            r".*"
        )
        super(CoordinateValidator, self).__init__(regex, 'coordinate')


class DomainValidator(BaseValidator):

    def __init__(self):
        regex = (
            r"(?=^.{4,253}\.?$)(^((?!-)[a-zA-Z0-9-]{1,63}(?<!-)\.)+[a-zA-Z]{2,63}\.?$)"
        )
        super(DomainValidator, self).__init__(regex, 'domain')


class EmailValidator(BaseValidator):

    def __init__(self):
        regex = (
            r"^[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9]"
            r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9]"
            r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
        )
        super(EmailValidator, self).__init__(regex, 'email')


class HashValidator(BaseValidator):

    def __init__(self):
        regex = (
            r".*"
        )
        super(HashValidator, self).__init__(regex, 'hash')


class HostValidator(BaseValidator):

    def __init__(self):
        regex = (
            r".*"
        )
        super(HostValidator, self).__init__(regex, 'host')


class IPAddressValidator(BaseValidator):

    def __init__(self):
        regex = (
            r".*"
        )
        super(IPAddressValidator, self).__init__(regex, 'IP address')


class NetblockValidator(BaseValidator):

    def __init__(self):
        regex = (
            r".*"
        )
        super(NetblockValidator, self).__init__(regex, 'netblock')


class UrlValidator(BaseValidator):

    def __init__(self):
        regex = (
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
        super(UrlValidator, self).__init__(regex, 'url')
