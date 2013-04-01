import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.register_option('store', False, 'yes', 'add discovered hosts to the database.')
        self.info = {
                     'Name': 'SameIP.org Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Checks SameIP.org for other hosts hosted on the same server and can update the \'hosts\' table of the database with the results if desired.',
                     'Comments': [
                                  'Source options: [ db | <hostname> | ./path/to/file | query <sql> ]',
                                  'Knowing what other hosts are hosted on a provider\'s server can sometimes yield interesting results and help identify additional targets for assessment.'
                                  ]
                     }
   
    def module_run(self):
        hosts = self.get_source(self.options['source']['value'], 'SELECT DISTINCT host FROM hosts WHERE host IS NOT NULL ORDER BY host')
        if not hosts: return
        store = self.options['store']['value']

        cnt = 0
        tot = 0
        for host in hosts:
            url = 'http://sameip.org/ip/%s' % (host)
            self.verbose('URL: %s' % url)
            try: resp = self.request(url)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            # get the sites this host's web site links to
            results = re.findall(r'<a href="http:\/\/[^"]+" rel=\'nofollow\' title="visit ([^"]+)"', resp.text)
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
