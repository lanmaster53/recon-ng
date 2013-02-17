import framework
# unique to module
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('domain', self.goptions['domain']['value'], 'yes', self.goptions['domain']['desc'])
        self.register_option('verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'MyWOT Domain Lookup',
                     'Author': 'Micah Hoffman (@WebBreacher)',
                     'Description': 'Checks mywot.com site for information about the security of a domain.',
                     'Comments': []
                     }
   
    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.mywot()

    def mywot(self):
        verbose = self.options['verbose']['value']
        domain = self.options['domain']['value']

        url = 'http://api.mywot.com/0.4/public_query2?target=%s' % (domain)
        if verbose: self.output('URL being retrieved: %s' % url)
        try: resp = self.request(url)
        except KeyboardInterrupt:
            print ''
            return
        except Exception as e:
            self.error(e.__str__())
            return

        # Get the security results
        findings = re.findall(r'<application name="(\d)" r="(\d+)" c="(\d+)"', resp.text)
        
        tdata = []
        tdata.append(['Description', 'Reputation', 'Confidence'])
        for line in findings:

            # Description
            if line[0] == '0':
                descr = 'Trustworthiness'
            elif line[0] == '1':
                descr = 'Vendor Reliability'
            elif line[0] == '2':
                descr = 'Privacy'
            elif line[0] == '4':
                descr = 'Child Safety'

            # Reputation Scores
            repTmp = int(line[1])
            if repTmp >= 80:
                rep = 'Excellent'
            elif 80 > repTmp >= 60:
                rep = 'Good'
            elif 60 > repTmp >= 40:
                rep = 'Unsatisfactory'
            elif 40 > repTmp >= 20:
                rep = 'Poor'
            elif 20 > repTmp >= 0:
                rep = 'Very poor'

            # Confidence Scores
            confTmp = int(line[2])
            if confTmp >= 45:
                conf = '5 - High'
            elif 45 > confTmp >= 34:
                conf = '4 - MedHigh'
            elif 34 > confTmp >= 23:
                conf = '3 - Medium'
            elif 23 > confTmp >= 12:
                conf = '2 - MedLow'
            elif 12 > confTmp >= 6:
                conf = '1 - Low'
            else:
                conf = '0 - None'

            tdata.append([descr, rep, conf])

        self.table(tdata, True)
