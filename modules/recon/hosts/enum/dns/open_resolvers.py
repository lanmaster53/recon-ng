import framework
# unique to module

import re
import time
class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of hosts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Open Recursive DNS Resolvers Check',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages the Open DNS Resolver Project data at openresolverproject.org to check the class C subnets for open recursive DNS resolvers.',
                     'Comments': [
                                  'Source options: [ db | <address> | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        ips = self.get_source(self.options['source']['value'], 'SELECT DISTINCT ip_address FROM hosts WHERE ip_address IS NOT NULL ORDER BY ip_address')
        classCs = []

        # for each ip, get it's class C equivalent and add to a list
        for ip in ips:
            classC = '.'.join(ip.split('.')[:-1])
            # only add unique subnets to the list
            if classC not in classCs:
                classCs.append(classC)

        # get the cookie first for all other requests
        mainUrl = 'http://openresolverproject.org'
        setupResponse = self.request(mainUrl)
        hv = ""
        for cookie in setupResponse.cookies:
            if cookie.name == 'hv':
                hv = cookie.value
        # it seems we need to briefly sleep so the server has time to register the session, otherwise we don't get results back
        time.sleep(1)

        allFound = []
        self.output("Open resolvers and last checked time:")
        # for each subnet, look for open resolvers
        for subnet in classCs:
            url = 'http://openresolverproject.org/search.cgi?botnet=yessir&search_for=%s' % (subnet + ".0")
            self.verbose('URL: %s' % url)

            # build the request as expected by the open resolver project
            response = self.request(url, cookies={"hv":hv}, headers={"Referer":"http://openresolverproject.org"})

            rows = re.findall("<TR>.+</TR>", response.text)
            # skip the first row since that is the table header
            for row in rows[1:]:
                # if the rcode (field 4) is 0, there was no error so display
                fields = re.search(r'<TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD><TD>(.*)</TD>', row)
                if fields.group(4) == "0":
                    allFound.append(fields)

        if len(allFound) > 0:
            tableData = [["IP Queried", "Responding IP (if different)", "Time Detected", "RCode"]]
            for host in allFound:
                tableData.append([host.group(1), host.group(2), time.ctime( float( host.group(3) )), host.group(4)])
            self.table(tableData, header=True)
            self.output("Total open resolvers: %d" % len(allFound))
        else: self.output("No open resolvers found.")
