import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', '', 'yes', 'target host')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.register_option('add_to_db', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'My-IP-Neighbors Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks my-ip-neighbors.com site for other hosts hosted on the same server. This module can update the \'hosts\' table of the database with the results.',
                     'Comments': ['Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.']
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.ip_neigh()

    def ip_neigh(self):
        verbose = self.options['verbose']['value']
        host = self.options['host']['value']
        add_hosts = self.options['add_to_db']['value']

        url = 'http://www.my-ip-neighbors.com/?domain=%s' % (host)
        if verbose: self.output('URL being retrieved: %s' % url)
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
