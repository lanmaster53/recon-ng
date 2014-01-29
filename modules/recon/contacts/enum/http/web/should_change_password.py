import framework
# unique to module

class Module(framework.Module):

    def __init__(self, params):
        framework.Module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.info = {
                     'Name': 'Should I Change My Password Breach Check',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages ShouldIChangeMyPassword.com to determine if email addresses are associated with leaked credentials and updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: [ db | email.address@domain.com | ./path/to/file | query <sql> ]',
                                  ]
                     }

    def module_run(self):
        emails = self.get_source(self.options['source'], 'SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        
        total = 0
        emailsFound = 0
        # lookup each hash
        url = 'https://shouldichangemypassword.com/check-single.php'
        for emailstr in emails:
            # build the request
            payload = {'email': emailstr}
            resp = self.request(url, method="POST", payload=payload)
            # retrieve the json response
            jsonobj = resp.json
            numFound = jsonobj['num']
            total += 1
            # if any breaches were found, show the number found and the last found date
            if numFound != "0":
                last = jsonobj['last']
                self.alert('%s => Found! Seen %s times as recent as %s.' % (emailstr, numFound, last))
                emailsFound += 1
            else:
                self.verbose('%s => safe.' % (emailstr))
        self.output('%d/%d targets breached.' % (emailsFound, total))
