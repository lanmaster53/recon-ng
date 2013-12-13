import framework

import time

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.info = {
            'Name': 'VPNHunter Lookup',
            'Author': 'Quentin Kaiser (contact[at]quentinkaiser.be)',
            'Description': 'Checks vpnhunter.com SSL VPNs, Remote Access, Email Portals and Generic Login Sites.',
            'Comments': [
            ]
        }

    def module_run(self):

        fqdn = self.goptions['domain']['value']
        payload = {'fqdn' : fqdn}
        headers = {
            'Host' : 'www.vpnhunter.com',
            'Origin' : 'http://www.vpnhunter.com/',
            'Referer' : 'http://www.vpnhunter.com/'
        }
        resp = self.request('http://www.vpnhunter.com/', method='POST', headers=headers, payload=payload, redirect=False)
        hash = resp.headers['location'].replace("/r/", "")
        self.hunt(fqdn, hash, "sslvpn", headers)
        self.hunt(fqdn, hash, "remoteaccess", headers)
        self.hunt(fqdn, hash, "emailportals", headers)
        self.hunt(fqdn, hash, "genericlogin", headers)

    def hunt(self, fqdn, hash, resource_type, headers):

        payload = {
            "fqdn" : fqdn,
            "type" :resource_type,
            "hash" : hash,
            "_" : time.time()
        }
        headers = {
            'Host' : 'www.vpnhunter.com',
            'Origin' : 'http://www.vpnhunter.com/',
            'Referer' : "http://www.vpnhunter.com/r/%s"%(hash)
        }
        self.output("Checking %s for %s"%(resource_type, fqdn))
        resp = self.request('http://www.vpnhunter.com/poll', headers=headers, payload=payload)
        content = resp.json
        if len(content["result"]):
            for result in content["result"]:
                self.alert("Found 1 %s running %s on %s"%(resource_type, result['vendor'], result['address']))