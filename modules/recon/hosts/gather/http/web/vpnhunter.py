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

        self.services = {
            'sslvpn': {'pretty': 'SSL VPN'},
            'remoteaccess': {'pretty': 'remote access'},
            'emailportals': {'pretty': 'email portal'},
            'genericlogin': {'pretty': 'generic login page'}
        }

        fqdn = self.goptions['domain']['value']
        payload = {'fqdn': fqdn}
        headers = {
            'Host': 'www.vpnhunter.com',
            'Origin': 'http://www.vpnhunter.com/',
            'Referer': 'http://www.vpnhunter.com/'
        }
        resp = self.request(
            'http://www.vpnhunter.com/',
            method='POST',
            headers=headers,
            payload=payload,
            redirect=False
        )
        hash = resp.headers['location'].replace("/r/", "")
        for service in self.services:
            self.hunt(fqdn, hash, service, headers)

    def hunt(self, fqdn, hash, service, headers):
        payload = {
            "fqdn": fqdn,
            "type": service,
            "hash": hash,
            "_": time.time()
        }
        headers = {
            'Host': 'www.vpnhunter.com',
            'Origin': 'http://www.vpnhunter.com/',
            'Referer': "http://www.vpnhunter.com/r/%s" % (hash)
        }
        self.output("Checking for %s on %s" % (self.services[service]['pretty'], fqdn))
        resp = self.request('http://www.vpnhunter.com/poll', headers=headers, payload=payload)
        content = resp.json
        if len(content["result"]):
            for result in content["result"]:
                if len(result['address']) == 2:
                    self.alert("Found 1 %s running %s on %s (port %s)" %
                               (self.services[service]['pretty'], result['vendor'], result['address'][0],
                                result['address'][1]))
                else:
                    self.alert("Found 1 %s running %s on %s" %
                               (self.services[service]['pretty'], result['vendor'], result['address']))