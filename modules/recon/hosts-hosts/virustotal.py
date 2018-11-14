from recon.core.module import BaseModule
from time import sleep

class Module(BaseModule):

    meta = {
        'name': 'Virustotal domains extractor',
        'author': 'USSC (thanks @jevalenciap)',
        'description': 'Harvests domains from the Virustotal by using the report API. Updates the \'hosts\' table with the results.',
        'required_keys': ['virustotal_api'],
        'query': 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL',
        'options': (
            ('interval', 15, True, 'interval in seconds between api requests'),
        ),
    }

    def module_run(self, addresses):
        key = self.get_key('virustotal_api')
        url = 'https://www.virustotal.com/vtapi/v2/ip-address/report'
        for ip in addresses:
            self.heading(ip, level=0)
            resp = self.request( url, payload = {'ip': ip, 'apikey': key} )
            if resp.json and 'resolutions' in resp.json.keys():
                for entry in resp.json['resolutions']:
                    hostname = entry.get('hostname')
                    if hostname:
                        self.add_hosts(host=hostname, ip_address=ip)
            sleep(self.options['interval'])
