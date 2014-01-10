import socket

try:
    _GLOBAL_DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT
except AttributeError:
    _GLOBAL_DEFAULT_TIMEOUT = object()
