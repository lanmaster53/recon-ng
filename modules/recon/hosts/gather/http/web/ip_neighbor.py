import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.register_option('regex', '%s$' % (self.global_options['domain']['value']), 'no', 'regex to match for adding results to the database')
        self.info = {
                     'Name': 'My-IP-Neighbors.com Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks My-IP-Neighbors.com for other hosts hosted on the same server and updates the \'hosts\' table of the database with the results matching the given regex.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        regex = self.options['regex']

        cnt = 0
        new = 0
        for host in hosts:
            url = 'http://www.my-ip-neighbors.com/?domain=%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            results = re.findall(r'a href="http://whois.domaintools.com/(.+?)"', resp.text)
            if not results:
                self.verbose('No additional hosts discovered at the same IP address.')
                continue
            for result in results:
                cnt += 1
                self.output(result)
                if not regex or re.search(regex, result):
                    new += self.add_host(result)

        self.output('%d total hosts found.' % (cnt))
        if new: self.alert('%d NEW hosts found!' % (new))
