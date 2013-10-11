import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.register_option('regex', '%s$' % (self.goptions['domain']['value']), 'no', 'regex to match for adding results to the database')
        self.info = {
                     'Name': 'SameIP.org Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Checks SameIP.org for other hosts hosted on the same server and updates the \'hosts\' table of the database with the results matching the given regex.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  'Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL')
        regex = self.options['regex']['value']

        cnt = 0
        new = 0
        for host in hosts:
            url = 'http://sameip.org/ip/%s' % (host)
            self.verbose('URL: %s' % url)
            resp = self.request(url)
            results = re.findall(r'rel=\'nofollow\' title="([^"]+) whois"', resp.text)
            if not results:
                self.verbose('No additional hosts discovered at the same IP address.')
                continue
            for result in results:
                cnt += 1
                self.output(result)
                if not regex or re.search(regex, host):
                    new += self.add_host(result)

        self.output('%d total hosts found.' % (cnt))
        if new: self.alert('%d NEW hosts found!' % (new))
