import framework
# unique to module
import os
import re

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option(self.options, 'source', 'database', 'yes', 'source of module input')
        self.register_option(self.options, 'verbose', self.goptions['verbose']['value'], 'yes', self.goptions['verbose']['desc'])
        self.info = {
                     'Name': 'PwnedList Validator',
                     'Author': 'Tim Tomes (@LaNMaSteR53)',
                     'Description': 'Leverages PwnedList.com to determine if email addresses are associated with leaked credentials. This module updates the \'creds\' table of the database with the positive results.',
                     'Comments': [
                                  'Source options: database, <email@address>, <path/to/infile>'
                                  ]
                     }

    def do_run(self, params):
        if not self.validate_options(): return
        # === begin here ===
        self.check_pwned()

    def check_pwned(self):
        verbose = self.options['verbose']['value']
        
        # handle sources
        source = self.options['source']['value']
        if source == 'database':
            accounts = [x[0] for x in self.query('SELECT DISTINCT email FROM contacts WHERE email IS NOT NULL ORDER BY email')]
            if len(accounts) == 0:
                self.error('No email addresses in the database.')
                return
        elif os.path.exists(source): accounts = open(source).read().split()
        else: accounts = [source]

        # retrieve status
        pattern = "class='query_result_footer'>... we found your email in our database a total of (\d+?) times. It was last seen on ([\d-]+?). Please read on. <div"
        i, pwned = 0, 0
        while i < len(accounts):
            status = None
            account = accounts[i].encode('utf-8')
            url = 'http://pwnedlist.com/query'
            payload = {'query_input' : account, 'query_input_hash' : 'empty', 'submit' : 'CHECK' }
            try: resp = self.request(url, payload=payload, method='POST', redirect=False)
            except KeyboardInterrupt:
                print ''
                break
            except Exception as e:
                self.error(e.__str__())
                break
            the_page = resp.text
            if 'Gotcha!' in the_page:
                self.error('Hm... Got a captcha.')
                return
            elif '>NOPE!<' in the_page:
                status = 'safe'
                if verbose: self.output('%s => %s.' % (account, status))
            elif '>YES<' in the_page:
                status = 'pwned'
                m = re.search(pattern, the_page)
                qty = m.group(1)
                last = m.group(2)
                self.alert('%s => %s! Seen %s times as recent as %s.' % (account, status, qty, last))
                self.add_cred(account)
                pwned += 1
            else:
                self.error('Response not understood.')
                return
            i += 1
        self.output('%d/%d targets pwned.' % (pwned, i))