import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'URLVoid Domain Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks urlvoid.com for information about the security of the given domain.',
                     'Comments': []
                     }
   
    def module_run(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']

        url = 'http://www.urlvoid.com/scan/%s/' % (domain)
        if verbose: self.output('URL: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # Get the security results
        av_engines = re.findall(r'<td>(.+)</td>\n.*images/(.+)\.png" alt=""', resp.text)
        tdata = []
        tdata.append(['Site', 'Status'])
        for line in av_engines:
            tdata.append([line[0], line[1]])
        self.table(tdata, True)
