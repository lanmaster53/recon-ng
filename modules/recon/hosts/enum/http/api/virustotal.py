# packages required for framework integration
import framework

# module specific packages
from urlparse import urlparse
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)        
        self.register_option('search', '', 'yes', 'Information to search results for')    
        self.register_option('non_clean', 'True', 'yes', 'Shows only non-clean sites in the URL scan')     
        self.info = {
                     'Name': 'Virus Total Lookup',
                     'Author': 'Steven Dumolt (@dumolts)',
                     'Description': 'Uses Virus Total to gather data',
                     'Comments': ['NON_CLEAN options: [ True | False ]','SEARCH format options: [ URL | HOSTNAME | IP ]']
                    }

    def isIP(self,str):
        IP_REGEX = r'^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$'
        if not re.match(IP_REGEX,str) is None:
            return True
        else:
            return False

    def domainSearch(self,str):
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

    def ipSearch(self,str):
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

    def urlSearch(self,str):
        url = "https://www.virustotal.com/vtapi/v2/url/report"
        payload = {'resource': str,'apikey':self.get_key('VirusTotal')}
        resp = self.request(url, method="POST", payload=payload)

        if resp.json['response_code'] == 1:
            tdata = []
            tdata.append(['Scanner', 'Result'])
            clean=[]
            for k in sorted(resp.json['scans']):
                if self.options['non_clean'] == True:
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
       
        self.urlSearch(self.options['search'])        

        if 'http' in x.scheme:
            site = x.netloc
        elif x.scheme == '':
            site = x.path
        else:
            site=x.scheme        
        

        invalidChar = [':','/','\\']
        if not any(invalid in site for invalid in invalidChar): 
            if self.isIP(site)== True:
                self.ipSearch(site)            
            else:
                self.domainSearch(site)
        
                
        

        


