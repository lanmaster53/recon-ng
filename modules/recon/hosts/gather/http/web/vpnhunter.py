from framework import *
# unique to module

class Module(Framework):
    def __init__(self, params):
        Framework.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', 'domain to check for remote access')
        self.info = {
            'Name': 'VPNHunter Lookup',
            'Author': 'Quentin Kaiser (contact[at]quentinkaiser.be)',
            'Description': 'Checks vpnhunter.com for SSL VPNs, remote accesses, email portals and generic login sites.',
            'Comments': []
        }

    def module_run(self):

        domain = self.options['domain']
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
            self.error("Unable to obtain results from VPNHunter.")
            return

        hash = resp.headers['location'].replace("/r/", "")
        payload['hash'] = hash
        cnt = 0
        new = 0

        for service in self.services:
            error = None
            payload['type'] = service
            self.output("Checking for %s on %s." % (self.services[service], domain))
            resp = self.request('http://www.vpnhunter.com/poll', payload=payload)
            if resp.status_code == 200:
                if type(resp.json["result"]) != unicode:
                    for result in resp.json["result"]:
                        if len(result['address']) == 2:
                            self.alert("Found 1 %s running %s on %s (port %s)" % (self.services[service], result['vendor'], result['address'][0], result['address'][1])) 
                            host = result['address'][0]
                        else:
                            self.alert("Found 1 %s running %s on %s" % (self.services[service], result['vendor'], result['address']))
                            host = result['address'].split('//')[-1]
                        new += self.add_host(host)
                        cnt += 1
                else:
                    error = resp.json["result"]
                    break
            else:
                error = str(resp.status_code)
                break

        if error != None: self.error("An error occured while requesting info from VPNHunter (%s)." % (error))
        self.output('%d total hosts found.' % (cnt))
        if new: self.alert('%d NEW hosts found!' % (new))
