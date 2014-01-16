from framework import *
# unique to module
import re


class Module(Framework):

    def __init__(self, params):
        Framework.__init__(self, params)
        self.register_option('domain', self.global_options['domain'], 'yes', 'domain to check for subject alternative names (SAN)')
        self.info = {
                     'Name': 'SSL SAN Lookup',
                     'Author': 'Zach Grace (@ztgrace) zgrace@403labs.com',
                     'Description': 'This module uses the ssltools.com site to obtain the subject alternative name(s) for a domain.',
                     'Comments': [
                                  'For an alternative version see https://github.com/403labs/recon-ng_modules.'
                                  ]
                     }

    def module_run(self):
        domain = self.options['domain']
        url = 'http://www.ssltools.com/certificate_lookup/%s' % domain

        html = self.request(url).text
        match = re.search('<br>Subject Alternative Names :(.*?)<br>', html)

        if match is None:
            self.error('No Subject Alternative Names found for \'%s\'' % domain)
            return

        names = match.group(1)
        for name in names.split(','):
            self.output(name.strip())
