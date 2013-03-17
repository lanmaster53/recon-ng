import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('ip', False, 'yes', 'Enter the IP you would like to search for')
        self.info = {
                     'Name': 'IPVoid IP Address Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks ipvoid.com for information about the security of the given IP Address.',
                     'Comments': []
                     }
   
    def module_run(self):
        ip = self.options['ip']['value']

        url = 'http://www.ipvoid.com/scan/%s/' % (ip)
        self.verbose('URL: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # Get and display the results
        self.heading('Results for %s' % ip, 1)
        blacklisted = re.search(r'Blacklist Status</td><td><span.+>(\w.+)</span>', resp.text)
        if blacklisted.group(1) == "BLACKLISTED":
            self.alert('Status: %s' % blacklisted.group(1))
            detected_line = re.search(r'\s+<tr><td><img src="(.+)', resp.text)
            detected_sites = re.findall(r'Favicon" />(.+?)</td><td><img src=".+?" alt="Alert" title="Detected!" ', detected_line.group(1))
            for site in detected_sites:
                self.alert(site)
        
        detection = re.search(r'Detection Ratio</td><td>(\d+ / \d+) \(<font', resp.text)
        reverse_dns = re.search(r'Reverse DNS</td><td>(.+)</td>', resp.text)
        country = re.search(r'alt="Flag" /> \(\w+\) (.+)</td>', resp.text)
        city = re.search(r'City</td><td>(\w.+)</td>', resp.text)
        region = re.search(r'Region</td><td>(\w.+)</td>', resp.text)
        lat_long = re.search(r'Latitude / Longitude</td><td>(.+)</td>',resp.text)
        
        
        
        detected_sites = re.findall(r'Favicon" />(.+?)</td><td><img src=".+" alt="Alert" title="Detected!" ', resp.text)
        
        
        # Output
        
        self.output('Status: %s' % blacklisted.group(1))
        
        if detected_sites:
            for site in detected_sites:
                self.output(site)
        else:
            "Not currently blacklisted on any sites"
                
        
        
        '''tdata = []
        tdata.append(['Site', 'Status'])
        for line in av_engines:
            tdata.append([line[0], line[1]])
        self.table(tdata, True)'''
