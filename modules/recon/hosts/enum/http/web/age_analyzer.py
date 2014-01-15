import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', self.global_options['domain'], 'yes', 'fully qualified target hostname')
        self.info = {
                     'Name': 'Age Analyzer Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Attempts to guess the author\'s age using ageanalyzer.com.',
                     'Comments': []
                     }
   
    def module_run(self):
        host  = self.options['host']

        # request the author's age
        url = 'http://ageanalyzer.com/?url=%s' % (host)
        self.verbose('URL: %s' % url)
        resp = self.request(url)

        # extract and present results
        content = resp.text
        result = re.search(r'written by someone <strong>(.+)<\/strong> years old', content)
        if result:
            self.output('Ageanalyzer.com believes the author of %s to be %s years old.' % (host, result.group(1)))
        else:
            self.output('Ageanalyzer.com was unable to determine the age of the author.')
