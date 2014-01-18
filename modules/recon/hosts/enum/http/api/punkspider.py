import framework
# unique to module
import urllib
import json
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('search_str', '"%s"' % (self.global_options['domain']), 'yes', 'string to search for')
        self.register_option('search_type', 'url', 'yes', 'type of search (see \'info\' for options)')
        self.register_option('bsqli', True, 'yes', 'search for blind SQL injection')
        self.register_option('sqli', True, 'yes', 'search for SQL injection')
        self.register_option('xss', True, 'yes', 'search for Cross-Site Scripting')
        self.register_option('trav', True, 'yes', 'search for path traversal')
        self.register_option('mxi', True, 'yes', 'search for mail header injection')
        self.register_option('osci', True, 'yes', 'search for OS command injection')
        self.register_option('xpathi', True, 'yes', 'search for XPath injection')
        self.register_option('show_vulns', True, 'yes', 'if found, display vulnerabily information')
        self.register_option('store_table', None, 'no', 'name of database table to store results')
        self.info = {
                     'Name': 'PunkSPIDER Vulnerabilty Finder',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and thrapt (thrapt@gmail.com)',
                     'Description': 'Leverages PunkSPIDER to search for previosuly discovered vulnerabltiies on the given host(s).',
                     'Comments': [
                                  'The default configuration searches for vulnerabilites in the globally set target domain.',
                                  'Type options: [ url | title ]',
                                  ]
                     }
   
    def module_run(self):
        vuln_types = ['bsqli', 'sqli', 'xss', 'trav', 'mxi', 'osci', 'xpathi']
        search_type = self.options['search_type']
        if search_type.lower() not in ['url', 'title']:
            self.error('Invalid search type \'%s\'.' % (search_type))
            return
        search_str = self.options['search_str']
        table = self.options['store_table']
        url = 'http://punkspider.hyperiongray.com/service/search/domain/'
        payload = {'searchKey': search_type, 'searchValue': search_str, 'filterType': 'OR'}
        payload['filters'] = []
        for item in vuln_types:
            if self.options[item]:
                payload['filters'].append(item)

        # get search results
        vuln_domains = {}
        tdata = []
        page = 1
        while True:
            payload['pageNumber'] = page
            self.verbose('URL: %s?%s' % (url, urllib.urlencode(payload)))
            resp = self.request(url, method='POST', payload=payload, content='json')
            jsonobj = resp.json
            results = jsonobj['output']['domainSummaryDTOs']
            if not results: break
            for result in results:
                rdata = [result['id'], result['timestamp']]
                for vuln_type in vuln_types:
                    rdata.append(result[vuln_type])
                if any(rdata[2:]):
                    vuln_domains[result['id']] = '.'.join(re.search('//(.+?)/', result['id']).group(1).split('.')[::-1])
                tdata.append(rdata)
            page += 1

        # display search results
        if tdata:
            tdata.insert(0, ['Host', 'Time'] + vuln_types)
            self.table(tdata, header=True)
            if table: self.add_table(table, tdata, header=True)
        else:
            self.output('No vulnerabilities found.')

        # get vulnerbilities for positive results
        vulns = 0
        if self.options['show_vulns'] and vuln_domains:
            self.heading('Vulnerabilties', 1)
            for domain in vuln_domains:
                url = 'http://punkspider.hyperiongray.com/service/search/detail/%s' % vuln_domains[domain]
                resp = self.request(url, payload=payload)
                jsonobj = resp.json
                results = jsonobj['data']
                if results:
                    self.alert('Domain: %s' % (domain))
                    for result in results:
                        print('')
                        vulns += 1
                        self.output('Bug: %s' % (result['bugType']))
                        self.output('URL: %s' % (result['vulnerabilityUrl']))
                        self.output('Parameter: %s' % (result['parameter']))
                print(self.ruler*50)

        # display summary
        if vulns: self.alert('%d vulnerabilties found!' % (vulns))
