# packages required for framework integration
import framework
# module specific packages
from urlparse import urlparse
from time import sleep
import re

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.register_option('sleep', '30', 'yes', 'seconds to wait between processing hosts')
        self.info = {
                     'Name': 'VirusTotal Host Lookup',
                     'Author': 'Steven Dumolt (@dumolts)',
                     'Description': 'Uses the VirusTotal API to gather information about the given host(s).',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Note: VirusTotal allows 4 request per minute for the default public api.'
                                  ]
                     }

    def _domain_search(self, string):
        url = "https://www.virustotal.com/vtapi/v2/domain/report"
        payload = {'domain': string, 'apikey': self.api_key}
        resp = self.request(url, method="GET", payload=payload)
        if resp.json['response_code'] == 1:
            tdata = []
            for k in sorted(resp.json['resolutions']):
                tdata.append([k['ip_address'], k['last_resolved']])
            if tdata:
                self.table(tdata, header=['Ip Address', 'Last Resolved'])
        else:
            self.error(resp.json['verbose_msg'])

    def _ip_search(self, string):
        url = "https://www.virustotal.com/vtapi/v2/ip-address/report"
        payload = {'ip': string, 'apikey': self.api_key}
        resp = self.request(url, method="GET", payload=payload)
        if resp.json['response_code'] == 1:
            tdata = []
            for k in sorted(resp.json['resolutions']):
                tdata.append([k['hostname'], k['last_resolved']])
            if tdata:
                self.table(tdata, header=['Hostname', 'Last Resolved'])
        else:
            self.error(resp.json['verbose_msg'])

    def _url_search(self, string):
        url = "https://www.virustotal.com/vtapi/v2/url/report"
        payload = {'resource': string, 'apikey':self.api_key}
        resp = self.request(url, method="POST", payload=payload)
        if resp.json['response_code'] == 1:
            tdata = []
            clean = []
            for k in sorted(resp.json['scans']):
                if self.global_options['verbose'] == True:
                    if resp.json['scans'][k]['detected'] == True or 'clean' not in resp.json['scans'][k]['result']:
                        tdata.append([k, resp.json['scans'][k]['result']])
                    else:
                        clean.append(k)
                else:
                    tdata.append([k, resp.json['scans'][k]['result']])
            if tdata:
                self.table(tdata, header=['Scanner', 'Result'])
            if clean:
                self.output('Clean Scanners: %s'  % (', '.join(clean)))
        else:
            self.error(resp.json['verbose_msg'])
    
    def module_run(self):
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        self.api_key = self.get_key('virustotal_api')
        for i in range(0, len(hosts)):
            self.heading(hosts[i], 0)
            self._url_search(hosts[i])
            x = urlparse(hosts[i])
            if 'http' in x.scheme:
                site = x.netloc
            elif not x.scheme:
                site = x.path
            else:
                site = x.scheme
            invalidChar = [':', '/', '\\']
            if not any(invalid in site for invalid in invalidChar): 
                if re.search(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', site):
                    self._ip_search(site)
                else:
                    self._domain_search(site)
            if i < len(hosts)-1: sleep(self.options['sleep'])
