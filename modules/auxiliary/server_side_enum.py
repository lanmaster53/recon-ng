import framework
# unique to module
import os
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', 'www.google.com', 'yes', 'target host')
        self.register_option('protocol', 'http', 'yes', 'protocol of the host: http, https')
        self.register_option('redirect', False, 'yes', 'follow redirects')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'Server Side Enumerator',
                     'Author': 'Tim Tomes (@LaNMaSteR53) and Kenan Abdullahoglu (@kyabd)',
                     'Description': 'Analyzes response headers, cookies, and errors to determine which server-side technology is being used (PHP, .NET, JSP, CF, etc.).',
                     'Comments': []
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.enumerate()

    def enumerate(self):
        host = self.options['host']['value']
        protocol = self.options['protocol']['value']
        redirect = self.options['redirect']['value']
        verbose = self.options['verbose']['value']

        # make request
        url = '%s://%s' % (protocol, host)
        try: resp = self.request(url, redirect=redirect)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
        if not resp: return
        
        # check for redirect
        if url != resp.url:
            if verbose: self.output('URL => %s' % (url))
            if verbose: self.output('REDIR => %s' % (resp.url)) 
        else:
            if verbose: self.output('URL => %s' % (resp.url))

        # check file ext
        from urlparse import urlparse
        path = urlparse(url).path
        if path:
            filename = path.split('/')[-1]
            if verbose: self.output('FILENAME => %s' % (filename))
            if '.' in filename:
                ext = filename.split('.')[-1]
                self.output('EXT => %s' % (ext))

        # check headers
        for header in resp.headers:
            if header.lower() in ['server', 'x-powered-by', 'location']:
                self.output('%s => %s' % (header.upper(), resp.headers[header]))

        # check cookies
        for cookie in resp.cookies:
            if 'sess' in cookie.name.lower():
                self.output('COOKIE => %s' % (cookie.name))