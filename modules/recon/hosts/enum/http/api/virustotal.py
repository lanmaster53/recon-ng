# packages required for framework integration
import framework

# module specific packages
from urlparse import urlparse
from time import sleep
import re


class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)        
        self.register_option('source', 'db', 'yes', 'Information to search results for')       
        self.register_option('sleep', '30', 'yes', 'Sleep after each system')  
        self.info = {
                     'Name': 'Virus Total Lookup',
                     'Author': 'Steven Dumolt (@dumolts)',
                     'Description': 'Uses Virus Total to gather data',
                     'Comments': [
                                    'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                    'Sleep(seconds) will wait after each system for the specified ammount of time. ',
                                    '[NOTE] Virustotal allows 4 request a minute for the default public api.'
                     ]
                    }

    def _domain_search(self,str):
        url = "https://www.virustotal.com/vtapi/v2/domain/report"
        payload = {'domain': str,'apikey':self.api_key}        
        resp = self.request(url, method="GET", payload=payload)
        
        if resp.json['response_code'] == 1:
            tdata = []
            
            for k in sorted(resp.json['resolutions']):
                tdata.append([k['ip_address'],k['last_resolved']])

            if tdata:
                tdata.insert(0,)
                self.table(tdata,header=['Ip Address', 'Last Resolved'])

        else:
            self.error(resp.json['verbose_msg'])

    def _ip_search(self,str):
        url = "https://www.virustotal.com/vtapi/v2/ip-address/report"
        payload = {'ip': str,'apikey':self.api_key}        
        resp = self.request(url, method="GET", payload=payload)
        
        if resp.json['response_code'] == 1:
            tdata = []
            
            
            for k in sorted(resp.json['resolutions']):
                tdata.append([k['hostname'],k['last_resolved']])

            if tdata:
                self.table(tdata,header=['Hostname', 'Last Resolved'])
        else:
            self.error(resp.json['verbose_msg'])

    def _url_search(self,str):
        url = "https://www.virustotal.com/vtapi/v2/url/report"
        payload = {'resource': str,'apikey':self.api_key}
        resp = self.request(url, method="POST", payload=payload)

        if resp.json['response_code'] == 1:
            tdata = []
            
            clean=[]
            for k in sorted(resp.json['scans']):
                if self.global_options['verbose'] == True:
                    if resp.json['scans'][k]['detected'] == True or not 'clean' in resp.json['scans'][k]['result']:    
                        tdata.append([k,resp.json['scans'][k]['result']])
                    else:
                        clean.append(k)      
                else: 
                    tdata.append([k,resp.json['scans'][k]['result']])
            if tdata:
                self.table(tdata, header=['Scanner', 'Result'])
            
            if clean:
                self.output('Clean Scanners:' + ','.join(clean))
        else:
            self.error(resp.json['verbose_msg'])
    
    def module_run(self):        

        self.api_key=self.get_key('virustotal_api')

        
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        
        for host in hosts:
            x=urlparse(host)
           
            self.heading(host,0)
            self._url_search(host)        

            if 'http' in x.scheme:
                site = x.netloc
            elif not x.scheme:
                site = x.path
            else:
                site=x.scheme        
            

            invalidChar = [':','/','\\']
            if not any(invalid in site for invalid in invalidChar): 
                if re.search(r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$', site):
                    self._ip_search(site)            
                else:
                    self._domain_search(site)

            sleep(self.options['sleep'])


        
                
        

        


