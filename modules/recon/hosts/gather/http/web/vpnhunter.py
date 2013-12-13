import framework
# unique to module
import time

class Module(framework.module):
    def __init__(self, params):
        framework.module.__init__(self, params)
        self.info = {
            'Name': 'VPNHunter Lookup',
            'Author': 'Quentin Kaiser (contact[at]quentinkaiser.be)',
            'Description': 'Checks vpnhunter.com for SSL VPNs, remote accesses, email portals and generic login sites.',
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

        if not len(self.goptions['domain']['value']):
            self.error('The domain value is empty')
            return
        else:
            payload = {'fqdn': self.goptions['domain']['value']}
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
            if resp.status_code != 302:
                self.error("An error occured while requesting vpnhunter.com")
                return

            hash = resp.headers['location'].replace("/r/", "")

            headers['Referer'] = "http://www.vpnhunter.com/r/%s" % (hash)
            payload['hash'] = hash

            for service in self.services:
                payload['type'] = service
                self.output("Checking for %s on %s" % (self.services[service]['pretty'], payload['fqdn']))
                resp = self.request('http://www.vpnhunter.com/poll', headers=headers, payload=payload)
                if resp.status_code == 200:
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
                else:
                    self.error("An error occured while requesting vpnhunter.com")