import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('host', self.goptions['domain']['value'], 'yes', 'fully qualified target hostname')
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name':        'Gender Analyzer Lookup',
                     'Author':      'Brendan Coles (bcoles[at]gmail.com)',
                     'Description': 'Attempts to guess the author\'s gender using genderanalyzer.com.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.gender_lookup()

    def gender_lookup(self):
        verbose = self.options['verbose']['value']
        host  = self.options['host']['value']

        # request the author's gender
        url = 'http://genderanalyzer.com/?url=%s' % (host)
        if verbose: self.output('URL for genderanalyzer.com: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # extract and present results
        content = resp.text
        result = re.search(r'<strong>(written by a [a-z]+<\/strong> \(\d+%\))', content)
        if result:
            gender     = re.search(r"written by a ([a-z]+)", result.group(1)).group(1)
            confidence = re.search(r"\((\d+%)\)", result.group(1)).group(1)
            self.output('Genderanalyzer.com believes the author of %s is a %s (%s).' % (host, gender, confidence))
        else:
            self.output('Genderanalyzer.com was unable to determine the gender of the author.')
