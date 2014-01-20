import framework
# unique to module
from cookielib import CookieJar
import re
import time

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of addresses for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Open Recursive DNS Resolvers Check',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages data provided by the Open DNS Resolver Project at openresolverproject.org to check class C subnets for open recursive DNS resolvers.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        ips = self.get_source(self.options['source'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY ip_address')
        classCs = []

        # for each ip, get it's class C equivalent and add to a list
        for ip in ips:
            classC = '.'.join(ip.split('.')[:-1])
            # only add unique subnets to the list
            if classC not in classCs:
                classCs.append(classC)

        # get the cookie first for all other requests
        mainUrl = 'http://openresolverproject.org'

        cookiejar = CookieJar()
        resp = self.request(mainUrl, cookiejar=cookiejar)
        cookiejar = resp.cookiejar
        # it seems we need to briefly sleep so the server has time to register the session, otherwise we don't get results back
        time.sleep(1)

        allFound = []
        # for each subnet, look for open resolvers
        for subnet in classCs:
            url = 'http://openresolverproject.org/search.cgi?botnet=yessir&search_for=%s.0/24' % (subnet)
            self.verbose('URL: %s' % url)

            # build the request as expected by the open resolver project
            response = self.request(url, headers={"Referer":"http://openresolverproject.org"}, cookiejar=cookiejar)

            rows = re.findall("<TR>.+</TR>", response.text)
            # skip the first row since that is the table header
            for row in rows[1:]:
                # if the rcode (field 4) is 0, there was no error so display
                fields = re.search(r'<TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD>', row)
                if fields.group(4) == '0' and fields.group(5) == '1':
                    allFound.append(fields)

        if len(allFound) > 0:
            tableData = [["IP Queried", "Responding IP (if different)", "Time Detected"]]
            for host in allFound:
                tableData.append([host.group(1), host.group(2), time.ctime(float(host.group(3)))])
            self.table(tableData, header=True)
            self.output("Total open resolvers: %d" % len(allFound))
        else: self.output("No open resolvers found.")
