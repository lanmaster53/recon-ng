# packages required for framework integration
import framework

# module specific packages
from urlparse import urlparse
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)        
        self.register_option('search', '', 'yes', 'Information to search results for')       
        self.info = {
                     'Name': 'Virus Total Lookup',
                     'Author': 'Steven Dumolt (@dumolts)',
                     'Description': 'Uses Virus Total to gather data',
                     'Comments': ['SEARCH format options: [ URL | HOSTNAME | IP ]']
                    }

    def _domain_search(self,str):
        url = "https://www.virustotal.com/vtapi/v2/domain/report"
        payload = {'domain': str,'apikey':self.get_key('VirusTotal')}        
        resp = self.request(url, method="GET", payload=payload)
        
        if resp.json['response_code'] == 1:
            tdata = []
            tdata.append(['Ip Address', 'Last Resolved'])
            for k in sorted(resp.json['resolutions']):
                tdata.append([k['ip_address'],k['last_resolved']])
            self.table(tdata,True)

        else:
            self.error(resp.json['verbose_msg'])

    def _ip_search(self,str):
        url = "https://www.virustotal.com/vtapi/v2/ip-address/report"
        payload = {'ip': str,'apikey':self.get_key('VirusTotal')}        
        resp = self.request(url, method="GET", payload=payload)
        
        if resp.json['response_code'] == 1:
            tdata = []
            tdata.append(['Hostname', 'Last Resolved'])
            
            for k in sorted(resp.json['resolutions']):
                tdata.append([k['hostname'],k['last_resolved']])

            self.table(tdata,True)
        else:
            self.error(resp.json['verbose_msg'])

    def _url_search(self,str):
        url = "https://www.virustotal.com/vtapi/v2/url/report"
        payload = {'resource': str,'apikey':self.get_key('VirusTotal')}
        resp = self.request(url, method="POST", payload=payload)

        if resp.json['response_code'] == 1:
            tdata = []
            tdata.append(['Scanner', 'Result'])
            clean=[]
            for k in sorted(resp.json['scans']):
                if self.global_options['verbose'] == True:
                    if resp.json['scans'][k]['detected'] == True or not 'clean' in resp.json['scans'][k]['result']:    
                        tdata.append([k,resp.json['scans'][k]['result']])
                    else:
                        clean.append(k)      
                else: 
                    tdata.append([k,resp.json['scans'][k]['result']])

            self.table(tdata, True)
            if not clean is None:
                self.output('Clean Scanners:' + ','.join(clean))
        else:
            self.error(resp.json['verbose_msg'])
    
    def module_run(self):        
        x=urlparse(self.options['search'])

       
        self._url_search(self.options['search'])        

        if 'http' in x.scheme:
            site = x.netloc
        elif x.scheme == '':
            site = x.path
        else:
            site=x.scheme        
        

        invalidChar = [':','/','\\']
        if not any(invalid in site for invalid in invalidChar): 
            if re.search(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', site):
                self._ip_search(site)            
            else:
                self._domain_search(site)
        
                
        

        


