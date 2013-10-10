#!/usr/bin/env python
"""
Recon-ng RPC Interface

This module provides the foundation for RPC functionality for Recon-ng. Both
JSONRPC and XMLRPC are supported.  ReconState uses session IDs to ensure that 
each connection has its own Recon-ng session.

The following code can be used to test the XMLRPC interface:

    import xmlrpclib
    client = xmlrpclib.Server('http://localhost:4141')
    sid = client.init()
    client.global_set('WORKSPACE', 'rpc', sid)
    client.use('recon/hosts/gather/http/web/bing_domain', sid)
    client.set('DOMAIN', 'sunyit.edu', sid)
    client.run(sid)
    hosts = client.show('hosts', sid)
    print hosts

To test the JSONRPC interface, replace xmlrpclib with jsonrpclib.

"""
__author__ = "Anthony Miller-Rhodes (@_s1lentjudge)"

import sys
sys.path.append('./core/')
sys.path.append('./libs/')
import base

import random
import argparse


class ReconState:

    def __init__(self):
        self.sessions = {}

    def init(self):
        sid = random.randint(0, 1000000)
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
        self.sessions[sid]["module"].do_run(None)

    def show(self, param, sid):
        tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
        param_query = 'SELECT * FROM "%s" ORDER BY 1' % (param)
        tables = self.sessions[sid]["module"].query(tables_query)
        if param in [ x[0] for x in  tables ]:
            return self.sessions[sid]["module"].query(param_query)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--type", type=str, action="store", default='jsonrpc',
                                help="Set RPC server type", dest="server_type")
    parser.add_argument("-a", "--address", type=str, action="store", default='0.0.0.0',
                                help="Set RPC server bind address", dest="address")
    parser.add_argument("-p", "--port", type=int, action="store", default=4141,
                                help="Set RPC server port", dest="port")
    args = parser.parse_args()

    if args.server_type == 'xmlrpc':
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        RPCServer = SimpleXMLRPCServer
        server = RPCServer((args.address, args.port), allow_none=True)
    elif args.server_type == 'jsonrpc':
        from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
        RPCServer = SimpleJSONRPCServer
        server = RPCServer((args.address, args.port))

    server.register_instance(ReconState())
    print "[+] Serving on %s:%d" % (args.address, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "\n[+] Exiting"

