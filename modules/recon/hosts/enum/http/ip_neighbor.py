import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', '', 'yes', 'target host')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'My-IP-Neighbors Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks My-IP-Neighbors.com for other hosts hosted on the same server and can update the \'hosts\' table of the database with the results if desired.',
                     'Comments': ['Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.']
                     }
   
    def module_run(self):
        host = self.options['host']['value']
        add_hosts = self.options['store']['value']

        url = 'http://www.my-ip-neighbors.com/?domain=%s' % (host)
        self.verbose('URL: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
      
        # Get the sites this host's web site links to
        sites = re.findall(r'a href="http://whois.domaintools.com/(.+?)"', resp.text)
        if not sites:
            self.alert('No other hosts discovered at the same IP address.')
            return
            
        # Display the output
        tdata = [] 
        tdata.append(['Other Hosts Found'])       
        for site in sorted(sites):
            tdata.append([site])
            # Add each host to the database
            if add_hosts: self.add_host(site)
        self.table(tdata, True)
