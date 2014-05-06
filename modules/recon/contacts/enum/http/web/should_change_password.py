import module
# unique to module

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')
        self.info = {
                     'Name': 'Should I Change My Password Breach Check',
                     'Author': 'Dan Woodruff (@dewoodruff)',
                     'Description': 'Leverages ShouldIChangeMyPassword.com to determine if email addresses are associated with leaked credentials. Adds compromised email addresses to the \'creds\' table.'
                     }

    def module_run(self, emails):
        total = 0
        emailsFound = 0
        # lookup each hash
        url = 'https://shouldichangemypassword.com/check-single'
        for emailstr in emails:
            # build the request
            payload = {'email': emailstr}
            resp = self.request(url, method="POST", payload=payload)
            # retrieve the json response
            jsonobj = resp.json
            numFound = jsonobj['num']
            # if any breaches were found, show the number found and the last found date
            if numFound > 0:
                last = jsonobj['last']
                self.alert('%s => Found! Seen %s times as recent as %s.' % (emailstr, numFound, last))
                emailsFound += self.add_creds(emailstr)
                total += 1
            else:
                self.verbose('%s => safe.' % (emailstr))
        self.summarize(emailsFound, total)
