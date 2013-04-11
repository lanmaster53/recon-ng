import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'IPVoid IP Address Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks ipvoid.com for information about the security of the given IP Address.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }
   
    def module_run(self):
        addresses = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        if not addresses: return

        for address in addresses:
            url = 'http://www.ipvoid.com/scan/%s/' % (address)
            self.verbose('URL: %s' % url)
            try: resp = self.request(url)
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return

            if '<h1>AN ERROR OCCURRED</h1>' in resp.text:
                self.output('No data returned for \'%s\'' % (address))
                continue

            # Get and display the results
            blacklisted = re.search(r'Blacklist Status</td><td><span.+>(\w.+)</span>', resp.text)
            if blacklisted.group(1) == "BLACKLISTED":
                self.alert('\'%s\' is BLACKLISTED! (ruhroh)' % (address))
                detection = re.search(r'Detection Ratio</td><td>(\d+ / \d+) \(<font', resp.text)
                self.output('Detection Ratio was %s' % detection.group(1))
                detected_sites = re.findall(r'Favicon" />(.+?)</td><td><img src=".+?" alt="Alert" title="Detected!".+?"nofollow" href="(.+?)" title', resp.text)
                tdata = [['Site', 'Link']]
                for site in detected_sites:
                    tdata.append([site[0].strip(), site[1].strip()])
                self.table(tdata, True)
            else:
                self.output('\'%s\' not blacklisted...whew!' % (address))
            
            # Other Data scraped from the page
            reverse_dns = re.search(r'Reverse DNS</td><td>(.+)</td>', resp.text)
            city = re.search(r'City</td><td>(\w.+)</td>', resp.text)
            region = re.search(r'Region</td><td>(\w.+)</td>', resp.text)
            country = re.search(r'alt="Flag" /> \(\w+\) (.+)</td>', resp.text)
            lat_long = re.search(r'Latitude / Longitude</td><td>(.+)</td>',resp.text)
            # Output that additional stuff above
            self.output('Reverse DNS entry: %s' % (reverse_dns.group(1).strip()))
            self.output('Location: %s, %s, %s at %s' % (city.group(1).strip(), region.group(1).strip(), country.group(1).strip(), lat_long.group(1).strip()))
