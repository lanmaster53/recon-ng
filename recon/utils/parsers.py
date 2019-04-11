from urllib.parse import urlparse
import re

def parse_hostname(s):
    host = urlparse(s)
    if not host.scheme:
        host = urlparse('//'+s)
    return host.netloc

def parse_emails(s):
    return re.findall(r'([^\s]+@[^\s]+)', s)
