import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Should I Change My Password',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Uses the Should I Change My Password service to check if already discovered contact email addresses have been part of a password breach.',
                     'Comments': [
                                  'Source options: [ db | email.address@domain.com | ./path/to/file ]',
                                  ]
                     }

    def module_run(self):
        emails = self.get_source(self.options['source']['value'], 'SELECT DISTINCT email FROM contacts')
        if not emails: return
        
        total = 0
        emailsFound = 0
        # lookup each hash
        url = 'https://shouldichangemypassword.com/check-single.php'
        for emailstr in emails:
            total += 1
            payload = {'email': emailstr}
            try: resp = self.request(url, method="POST", payload=payload)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                continue
            if resp.json: jsonobj = resp.json
            else:
                self.error('Invalid JSON response for \'%s\'.\n%s' % (account, resp.text))
                continue
            numFound = jsonobj['num']
            if numFound != "0":
                last = jsonobj['last']
                self.alert('%s compromises for %s found! Most recent: %s' % (numFound, emailstr, last))
                emailsFound += 1
            else:
                self.output('No matches found for: %s' % (emailstr))
        self.output('%d/%d email addresses had a compromise.' % (emailsFound, total))
