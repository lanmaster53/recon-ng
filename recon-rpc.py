#!/usr/bin/env python

"""
Recon-ng RPC Interface

This module provides the foundation for RPC functionality for Recon-ng. Both
JSONRPC and XMLRPC are supported.  ReconState uses session IDs to ensure that 
each connection has its own Recon-ng session.

The following code can be used to test the RPC interface:

XML:
import xmlrpclib
client = xmlrpclib.Server('http://localhost:4141')
sid = client.init()
client.use('recon/hosts/gather/http/web/bing_domain', sid)
client.set('domain', 'sunyit.edu', sid)
results = client.run(sid)
print results

JSON:
import jsonrpclib
client = jsonrpclib.Server('http://localhost:4141')
...
"""

__author__ = "Anthony Miller-Rhodes (@_s1lentjudge)"

import uuid
import argparse
import sys
# prep python path for base module
sys.path.append('./core/')
import base
sys.path.append('./libs/')

def recon_rpc(args):
    if args.server_type.lower() == 'xmlrpc':
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        RPCServer = SimpleXMLRPCServer
        server = RPCServer((args.address, args.port), allow_none=True)
    elif args.server_type.lower() == 'jsonrpc':
        from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
        RPCServer = SimpleJSONRPCServer
        server = RPCServer((args.address, args.port))
    else:
        print '[!] Invalid RPC server type \'%s\'.' % (args.server_type)
        return
    server.register_multicall_functions()
    server.register_instance(ReconState())
    print "[+] Serving on %s:%d" % (args.address, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print ''

class ReconState:

    def __init__(self):
        self.sessions = {}

    def init(self):
        sid = str(uuid.uuid4())
        self.sessions[sid] = {
            "recon": base.Recon(mode=1),
            "module": None
        }
        self.sessions[sid]["module"] = self.sessions[sid]["recon"]
        return sid

    def use(self, param, sid):
        mod = self.sessions[sid]["recon"].do_use(param)
        self.sessions[sid]["module"] = mod

    def global_set(self, var, param, sid):
        self.sessions[sid]["recon"].do_set(var + " " + param)

    def set(self, var, param, sid):
        self.sessions[sid]["module"].do_set(var + " " + param)

    def run(self, sid):
        return self.sessions[sid]["module"].do_run(None)

    def show(self, param, sid):
        tables = self.sessions[sid]["module"].query('SELECT name FROM sqlite_master WHERE type=\'table\'')
        if param in [x[0] for x in tables]:
            return self.sessions[sid]["module"].query('SELECT * FROM %s ORDER BY 1' % (param))

    def workspace(self, param, sid):
        self.sessions[sid]["recon"].do_workspace(param)

parser = argparse.ArgumentParser()
parser.add_argument("-t", type=str, action="store", default='jsonrpc', help="Set RPC server type", dest="server_type", metavar="[jsonrpc|xmlrpc]")
parser.add_argument("-a", type=str, action="store", default='0.0.0.0', help="Set RPC server bind address", dest="address", metavar="address")
parser.add_argument("-p", type=int, action="store", default=4141, help="Set RPC server port", dest="port", metavar="port")
args = parser.parse_args()
recon_rpc(args)
