import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'My-IP-Neighbors Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks My-IP-Neighbors.com for other hosts hosted on the same server and can update the \'hosts\' table of the database with the results if desired.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        store = self.options['store']['value']

        cnt = 0
        tot = 0
        for host in hosts:
            url = 'http://www.my-ip-neighbors.com/?domain=%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            # get the sites this host's web site links to
            results = re.findall(r'a href="http://whois.domaintools.com/(.+?)"', resp.text)
            if not results:
                self.verbose('No additional hosts discovered at the same IP address.')
                continue
            
            # display the output
            for result in results:
                tot += 1
                self.output(result)
                # add each host to the database
                if store: cnt += self.add_host(result)
        self.output('%d total hosts found.' % (tot))
        if store and cnt: self.alert('%d NEW hosts found!' % (cnt))
