from jsonrpclib.config import Config
config = Config.instance()
from jsonrpclib.history import History
history = History.instance()
from jsonrpclib.jsonrpc import Server, MultiCall, Fault
from jsonrpclib.jsonrpc import ProtocolError, loads, dumps
