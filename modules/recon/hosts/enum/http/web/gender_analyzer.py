import framework
# unique to module
import re

class Module(framework.Framework):

    def __init__(self, params):
        framework.Framework.__init__(self, params)
        self.register_option('host', self.global_options['domain'], 'yes', 'fully qualified target hostname')
        self.info = {
                     'Name': 'Gender Analyzer Lookup',
                     'Author': 'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Attempts to guess the author\'s gender using genderanalyzer.com.',
                     'Comments': []
                     }
   
    def module_run(self):
        host  = self.options['host']

        # request the author's gender
        url = 'http://genderanalyzer.com/?url=%s' % (host)
        self.verbose('URL: %s' % url)
        resp = self.request(url)

        # extract and present results
        content = resp.text
        result = re.search(r'<strong>(written by a [a-z]+<\/strong> \(\d+%\))', content)
        if result:
            gender     = re.search(r"written by a ([a-z]+)", result.group(1)).group(1)
            confidence = re.search(r"\((\d+%)\)", result.group(1)).group(1)
            self.output('Genderanalyzer.com believes the author of %s is a %s (%s).' % (host, gender, confidence))
        else:
            self.output('Genderanalyzer.com was unable to determine the gender of the author.')
