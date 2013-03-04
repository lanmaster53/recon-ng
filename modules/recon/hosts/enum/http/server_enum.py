import framework
# unique to module
from random import choice
import textwrap
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', 'www.google.com', 'yes', 'target host')
        self.register_option('protocol', 'http', 'yes', 'protocol of the host: http, https')
        self.register_option('redirect', False, 'yes', 'follow redirects')
        self.info = {
                     'Name': 'Server Side Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53), Kenan Abdullahoglu (@kyabd), Matteo Cantoni (nothink.org)',
                     'Description': 'Analyzes response headers, cookies, and errors to determine which server-side technology is being used (PHP, .NET, JSP, CF, etc.).',
                     'Comments': []
                     }

    def lookup(self, db, name, value):
        matches = []
        for platform in db:
            for i in db[platform][name.lower()]:
                if i.lower() in value.lower():
                    matches.append(platform)
        if matches:
            return ', '.join(list(set(matches)))
        return None

    def module_run(self):
        host = self.options['host']['value']
        protocol = self.options['protocol']['value']
        redirect = self.options['redirect']['value']

        # dictionaries of search terms for each platform and check
        # dictionary for server side scripting technologies
        ss_script = {
            'PHP': {
                'ext':     ['php'],
                'cookie':  ['phpsession', 'phpsessid'],
                'powered': ['php']
                },
            'ASP/.NET': {
                'ext':     ['asp', 'aspx'],
                'cookie':  ['aspsessionid', 'asp.net_sessionid', 'aspsessid'],
                'powered': ['asp', 'asp.net', 'vb.net']
                },
            'ColdFusion': {
                'ext':     ['cfc', 'cfm', 'cfml', 'dbm', 'dbml'],
                'cookie':  ['cfid', 'cftoken', 'cfglobals'],
                'powered': ['coldfusion', 'cfmx']
                },
            'Java/J2E': {
                'ext':     ['jsp', 'jspx', 'jspf'],
                'cookie':  ['jsessionid', 'jsessid'],
                'powered': ['jsp', 'jboss']
                },
            'Rails': {
                'ext':     [],
                'cookie':  [],
                'powered': ['rails']
                }
            }
        # dictionary for server side server technologies
        ss_server = {
            'Apache': {
                'server': ['apache'],
                'error':  ['apache']
                },
            'IIS': {
                'server': ['iis'],
                'error':  ['iis']
                },
            'Nginx': {
                'server': ['nginx'],
                'error':  ['nginx']
                },
            'Python': {
                'server': ['python'],
                'error':  ['python', 'django']
                },
            'Ruby': {
                'server': ['ruby'],
                'error':  ['ruby']
                }
            }

        # make request
        url = '%s://%s' % (protocol, host)
        try: resp = self.request(url, redirect=redirect)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return
        
        if self.goptions['verbose']['value']:
            print 'START'.center(50, self.ruler)
            self.output('ORIG_URL: %s' % (url))
            self.output('DEST_URL: %s' % (resp.url))
            print 'HEADERS'.center(50, self.ruler)
            for header in resp.headers:
                self.output('%s: %s' % (header.upper(), textwrap.fill(resp.headers[header], 100, initial_indent='', subsequent_indent=self.spacer*2)))
            print 'COOKIES'.center(50, self.ruler)
            for cookie in resp.cookies:
                self.output('%s: %s' % (cookie.name.upper(), textwrap.fill(cookie.value, 100, initial_indent='', subsequent_indent=self.spacer*2)))
            print 'META TAGS'.center(50, self.ruler)
            pattern = '<META NAME=["\'](.+?)["\'] CONTENT=["\'](.+?)["\'][ /]*?>'
            tags = re.findall(pattern, resp.text, re.IGNORECASE)
            for tag in tags:
                self.output('%s: %s' % (tag[0].upper(), textwrap.fill(tag[1], 100, initial_indent='', subsequent_indent=self.spacer*2)))
            print 'END'.center(50, self.ruler)

        tdata = []
        # check file ext
        from urlparse import urlparse
        path = urlparse(resp.url).path
        if path:
            filename = path.split('/')[-1]
            if self.goptions['verbose']['value']:
                tdata.append(['FILENAME', filename, '--'])
            if '.' in filename:
                ext = filename.split('.')[-1]
                platform = self.lookup(ss_script, 'ext', ext)
                if not platform: platform = 'Unknown'
                tdata.append(['FILETYPE', ext, platform])

        # check headers
        for header in resp.headers:
            if header.lower() == 'location': platform = '--'
            elif header.lower() == 'server': platform = self.lookup(ss_server, 'server', resp.headers[header])
            elif header.lower() == 'x-powered-by': platform = self.lookup(ss_script, 'powered', resp.headers[header])
            else: continue
            # all ifs will end here if successful
            if not platform: platform = 'Unknown'
            tdata.append([header.upper(), resp.headers[header], platform])

        # check cookies
        for cookie in resp.cookies:
            platform = self.lookup(ss_script, 'cookie', cookie.name)
            if platform:
                tdata.append(['COOKIE', cookie.name, platform])
            elif 'sess' in cookie.name.lower(): 
                tdata.append(['COOKIE', cookie.name, 'Unknown'])

        # check error
        seq = ''.join(map(chr, range(97, 123)))
        pre = ''.join(choice(seq) for x in range(10))
        suf = ''.join(choice(seq) for x in range(3))
        bad_file = '%s.%s' % (pre, suf)
        bad_url = '%s/%s' % (url, bad_file)
        try:
            resp = self.request(bad_url, redirect=False)
            platform = self.lookup(ss_server, 'error', resp.text)
            if not platform: platform = 'Unknown'
            tdata.append(['ERROR', '%s (/%s)' % (str(resp.status_code), bad_file), platform])
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())

        self.table(tdata)
