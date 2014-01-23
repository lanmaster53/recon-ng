import framework
# unique to module
from urlparse import urlparse
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', self.global_options.description['domain'])
        self.register_option('iterations', 1, 'yes', 'number of searches to perform to retrieve domains')
        self.info = {
                     'Name': 'Bing API Hostname Enumerator',
                     'Author': 'Marcus Watson (@BranMacMuffin)',
                     'Description': 'Leverages the Bing API and "domain:" advanced search operator and updates the \'hosts\' table of the database with the results.',
                     'Comments': ['Iterations are designed to set a limit on the number of transactions on the API per query.']
                     }

    def module_run(self):
        domain = self.options['domain']
        iterations = self.options['iterations']

        hosts = []
        current_iteration = 0
        cnt = 0
        base_query = '\'domain:%s' % (domain)
        new_results_found = True
        query_limit_reached = False

        while new_results_found == True and query_limit_reached == False and current_iteration<iterations:

            new_results_found = False
            query = base_query

            for host in hosts:
                omit_domain = ' -domain:%s' % (host)

                if len(query)+len(omit_domain)<1024:
                    query += omit_domain
                else:
                    #No point in searching after this - no more domains can be added to the filter
                    query_limit_reached = True
                    break

            query += '\''

            results = self.search_bing_api(query)
            if type(results) != list:
                break
            if not results:
                self.verbose('No additional hosts discovered for \'%s\'.' % (domain))

            for result in results:
                host = urlparse(result['Url']).netloc
                if not host in hosts:
                    hosts.append(host)
                    self.output(host)
                    cnt += self.add_host(host)
                    new_results_found = True

            current_iteration+=1

        self.output('%d total hosts found.' % (len(hosts)))
        if cnt>0: self.alert('%d NEW hosts found!' % (cnt))
