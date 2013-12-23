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

        resp = self.request('https://rapportive.com/login_status?user_email=email@mail.com')

        if resp.status_code == 200 and 'session_token' in resp.json:
            session_token = resp.json['session_token']
            emails = self.get_source(self.options['source']['value'],
                "SELECT DISTINCT email FROM contacts ORDER BY email")
            new = 0
            for email in emails:
                new += self.call_api(session_token, email)
            if new: self.alert('%d NEW information about contacts found!' % (new))
        else:
            self.error("Can't obtain session token.")


    def call_api(self, session_token, email):

        first_name = ""
        last_name = ""
        region = ""
        country = ""
        location = ""
        job_title = ""
        found = 0

        headers = {'X-Session-Token' : session_token}
        resp = self.request('https://profiles.rapportive.com/contacts/email/%s'%(email), headers=headers)
        if resp.status_code == 200:
            if 'contact' in resp.json and resp.json['contact'] is not None:
                contact = resp.json['contact']
                if 'last_name' in contact and contact['last_name'] is not None and len(contact['last_name']):
                    #we consider that rapportive found this contact if it returns at least his/her last name
                    found = 1
                    last_name = contact['last_name']

                if 'first_name' in contact and contact['first_name'] is not None and len(contact['first_name']):
                    first_name = contact['first_name']

                if 'location' in contact and contact['location'] is not None and len(contact['location']):
                    location = contact['location']
                    if "," in location:
                        region = location.split(",")[0]
                        country = location.split(",")[1]

                if 'occupations' in contact:
                    for occupation in contact['occupations']:
                        if 'company' in occupation\
                           and occupation['company'] == self.goptions['company']['value']\
                           and 'job_title' in occupation and occupation['job_title'] is not None\
                        and len(occupation['job_title']):
                            job_title = occupation['job_title']

        self.query("UPDATE contacts SET lname = COALESCE(lname, '%s'), fname = COALESCE(fname, '%s'), "
                   "title = COALESCE(title, '%s'), region= COALESCE(region, '%s'), country = COALESCE(country, '%s') "
                   "WHERE email = '%s'" %(last_name, first_name, job_title, region, country, email))
        if found:
            self.output('%s => found' % (email))
        else:
            self.output('%s => not found' % (email))
        return found

