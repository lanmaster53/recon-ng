import framework
# unique to module

import re
class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Open Recursive DNS Resolvers Check',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages the Open DNS Resolver Project data at openresolverproject.org to check the class C subnets of \'hosts\' table entries for open recursive DNS resolvers.',
                     'Comments': [
                                  'Source options: [ db | ip_addr | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        ips = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY ip_address')
        if not ips: return
        classCs = list()

        # for each ip, get it's subnet and add to a list
        for ip in ips:
            indexOfLastOctet = ip.rfind(".")
            classC = ip[:indexOfLastOctet]
            # only add unique subnets to the list
            if classC not in classCs:
                classCs.append(classC)

        # for each subnet, look for open resolvers
        for subnet in classCs:
            url = 'http://openresolverproject.org/search.cgi?botnet=yessir&search_for=%s' % (subnet + ".1")
            self.verbose('URL: %s' % url)

            # build the request as expected by the open resolver project
            try: response = self.request(url, cookies={"hv":"7493717392"}, headers={"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language":"en-US,en;q=0.5", "Accept-Encoding":"gzip, deflate", "Connection":"keep-alive"})
            except KeyboardInterrupt:
                print ''
                return
            except Exception as e:
                self.error(e.__str__())
                return
            rows = re.findall("<TR>.+</TR>", response.text)
            # skip the first row since that is the header
            for row in rows[1:]:
                # if the rcode (field 4) is 0, there was no error so display
                fields = re.finditer('<TD>(.*)</TD>', row)
                self.output(fields.group(1))
                if fields.group(4) == 0:
                    self.output(row)
                

            #try: self.output(rows.group(1))
            #except Exception as e:
            #    continue
