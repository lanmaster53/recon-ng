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
    client.global_set('workspace rpc', sid)
    client.use('recon/hosts/gather/http/web/bing_domain', sid)
    client.local_set('domain sunyit.edu', sid)
    client.run(sid)

To test the JSONRPC interface, replace xmlrpclib with jsonrpclib.

"""
__author__ = "Anthony Miller-Rhodes (@_s1lentjudge)"

import sys
sys.path.append('./core/')
sys.path.append('./libs/')
import base

import random
import optparse


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

    def global_set(self, param, sid):
        self.sessions[sid]["recon"].do_set(param)

    def local_set(self, param, sid):
        self.sessions[sid]["module"].do_set(param)

    def run(self, sid):
        self.sessions[sid]["module"].do_run(None)


if __name__ == '__main__':
    usage = './%prog [options]'
    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--type', help='Set server type', action="store",
                      dest='server_type')
    opts, args = parser.parse_args()

    addr = "0.0.0.0"
    port = 4141

    if not opts.server_type:
        opts.server_type = 'jsonrpc'

    if opts.server_type == 'xmlrpc':
        from SimpleXMLRPCServer import SimpleXMLRPCServer
        RPCServer = SimpleXMLRPCServer
        server = RPCServer((addr, port), allow_none=True)
    elif opts.server_type == 'jsonrpc':
        from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer

        RPCServer = SimpleJSONRPCServer
        server = RPCServer((addr, port))

    server.register_instance(ReconState())
    print "[+] Serving on %s:%d" % (addr, port)
    server.serve_forever()

