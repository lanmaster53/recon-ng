from recon.core.module import BaseModule
from cookielib import CookieJar
import hashlib
import ssl

class Module(BaseModule):

    meta = {
        'name': 'VPNHunter Lookup',
        'author': 'Quentin Kaiser (contact[at]quentinkaiser.be)',
        'description': 'Checks vpnhunter.com for SSL VPNs, remote accesses, email portals and generic login sites. Updates the \'hosts\' table with the results.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        self.services = {
            'sslvpn': 'SSL VPN',
            'remoteaccess': 'remote access',
            'emailportals': 'email portal',
            'genericlogin': 'generic login page'
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        cookiejar = CookieJar()
        for domain in domains:
            self.heading(domain, level=0)
            resp = self.request('https://labs.duosecurity.com/vpnhunter/', method="GET", cookiejar=cookiejar)
            xsrf = [c.value for c in resp.cookiejar if c.name == '_xsrf'][0]
            payload = {"fqdn": domain, "_xsrf": xsrf}
            resp = self.request('https://labs.duosecurity.com/vpnhunter/', method="POST", payload=payload, headers=headers, cookiejar=cookiejar)
            payload["hash"] = hashlib.sha1(domain).hexdigest()[0:16]
            for service in self.services:
                error = None
                payload['type'] = service
                self.output("Checking for %s on %s..." % (self.services[service], domain))
                # vpnhunter can take a long time to resolve the desired information,
                # so loop for as long as the SSL connection continues to time out
                while True:
                    try:
                        resp = self.request('https://labs.duosecurity.com/vpnhunter/poll', method="GET", payload=payload, headers=headers, cookiejar=cookiejar)
                        break
                    except ssl.SSLError:
                        self.verbose('Polling...')
                if resp.status_code == 200:
                    if type(resp.json["result"]) != unicode:
                        for result in resp.json["result"]:
                            if len(result['address']) == 2 and result['address'][1] != 'None':
                                host = '%s:%s' % tuple(result['address'])
                            else:
                                host = result['address'][0]
                            self.alert("Found 1 %s running %s on %s" % (self.services[service], result['vendor'], host))
                            self.add_hosts(result['address'][0].split('//')[-1])
                    else:
                        error = resp.json["result"]
                        break
                else:
                    error = str(resp.status_code)
                    break
            if error != None:
                self.error("An error occured while requesting info from VPNHunter (%s)." % (error))
