import framework
# unique to module

class Module(framework.module):

    def __init__(self, params):
        framework.module.__init__(self, params)
        self.register_option('source', 'db', 'yes', 'source of accounts for module input (see \'info\' for options)')
        self.info = {
            'Name': 'Rapportive Contact Enumerator',
            'Author': 'Quentin Kaiser (@qkaiser, contact[at]quentinkaiser.be)',
            'Description': 'Harvests contacts informations from the Rapportive.com API and updates the \'contacts\' '
                           'table of the database with the results.',
            'Comments': []
        }
    def module_run(self):
        emails = self.get_source(self.options['source']['value'], "SELECT DISTINCT email FROM contacts ORDER BY email")
        new = 0
        for email in emails:
            new += self.call_api(email)

        if new: self.alert('%d NEW intel about contacts found!' % (new))

    def call_api(self, email):

        first_name = ""
        last_name = ""
        region = ""
        country = ""
        location = ""
        job_title = ""
        found = 0

        resp = self.request('https://rapportive.com/login_status?user_email=%s'%(email))

        if resp.status_code == 200 and resp.json is not None:
            if resp.json['status'] == 200 and 'session_token' in resp.json:
                headers = {'X-Session-Token' : resp.json['session_token']}
                resp = self.request('https://profiles.rapportive.com/contacts/email/%s'%(email), headers=headers)
                if resp.status_code == 200:
                    if 'contact' in resp.json and resp.json['contact'] is not None:
                        contact = resp.json['contact']
                        if 'last_name' in contact and contact['last_name'] is not None and len(contact['last_name']):
                            #we consider that rapportive found this contact if it returns at least his/her last name
                            found = 1
                            last_name = contact['last_name']
                            self.query("UPDATE contacts SET lname = '%s' WHERE email = '%s'" %(last_name, email))

                        if 'first_name' in contact and contact['first_name'] is not None and len(contact['first_name']):
                            first_name = contact['first_name']
                            self.query("UPDATE contacts SET fname= '%s' WHERE email = '%s'" %(first_name, email))

                        if 'location' in contact and contact['location'] is not None and len(contact['location']):
                            location = contact['location']
                            if "," in location:
                                region = location.split(",")[0]
                                country = location.split(",")[1]
                                self.query("UPDATE contacts SET region= '%s' WHERE email = '%s'" %(region, email))
                                self.query("UPDATE contacts SET country = '%s' WHERE email = '%s'" %(country, email))
                            else:
                                self.query("UPDATE contacts SET region= '%s' WHERE email = '%s'" %(location, email))

                        if 'occupations' in contact and contact['occupations'] is not None:
                            for occupation in contact['occupations']:
                                if 'company' in occupation\
                                   and occupation['company'] == self.goptions['company']['value']\
                                   and 'job_title' in occupation and occupation['job_title'] is not None\
                                and len(occupation['job_title']):
                                    job_title = occupation['job_title']
                                    self.query("UPDATE contacts SET title= '%s' WHERE email = '%s'" %(job_title, email))


        if found:
            self.output('%s => found' % (email))
        else:
            self.output('%s => not found' % (email))
        return found

