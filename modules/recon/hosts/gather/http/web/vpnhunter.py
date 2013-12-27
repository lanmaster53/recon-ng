import framework
# unique to module

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', 'domain to check for remote access')
        self.info = {
            'Name': 'VPNHunter Lookup',
            'Author': 'Quentin Kaiser (contact[at]quentinkaiser.be)',
            'Description': 'Checks vpnhunter.com for SSL VPNs, remote accesses, email portals and generic login sites.',
            'Comments': []
        }

    def module_run(self):

        domain = self.options['domain']['value']
        self.services = {
            'sslvpn': 'SSL VPN',
            'remoteaccess': 'remote access',
            'emailportals': 'email portal',
            'genericlogin': 'generic login page'
        }

        payload = {'fqdn': domain}
        resp = self.request(
            'http://www.vpnhunter.com/',
            method='POST',
            payload=payload,
            redirect=False
        )
        if resp.status_code != 302:
            self.error("vpnhunter.com can't obtain results.")
            return

        hash = resp.headers['location'].replace("/r/", "")
        payload['hash'] = hash

        for service in self.services:
            payload['type'] = service
            self.output("Checking for %s on %s." % (self.services[service], domain))
            resp = self.request('http://www.vpnhunter.com/poll', payload=payload)
            if resp.status_code == 200:
                for result in resp.json["result"]:
                    if len(result['address']) == 2:
                        self.alert("Found 1 %s running %s on %s (port %s)" %
                                   (self.services[service], result['vendor'], result['address'][0], result['address'][1]))
                    else:
                        self.alert("Found 1 %s running %s on %s" %
                                   (self.services[service], result['vendor'], result['address']))
            else:
                self.error("An error occured while requesting vpnhunter.com.")
