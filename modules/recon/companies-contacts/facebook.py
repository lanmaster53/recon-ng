import module
# unique to module
import json
import re
import urllib

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params, query='SELECT DISTINCT company FROM companies WHERE company IS NOT NULL ORDER BY company')
        self.info = {
            'Name': 'Facebook Contact Enumerator',
            'Author': 'Quentin Kaiser (@qkaiser) and Tim Tomes (@LaNMaSteR53)',
            'Description': 'Harvests contacts from Facebook.com. Updates the \'contacts\' table with the results.',
        }

    def module_run(self, companies):
        self.br = self.browser()
        username = self.get_key('facebook_username')
        password = self.get_key('facebook_password')
        if self.login(username, password):
            for company in companies:
                self.heading(company, level=0)
                company_id = self.get_company_id(company)
                if company_id:
                    self.get_contacts(str(company_id))

    def login(self, username, password):
        self.verbose('Authenticating to Facebook...')
        resp = self.br.open('https://www.facebook.com')
        for form in self.br.forms():
            if form.attrs['id'] == 'login_form':
                self.br.form = form
                break
        self.br["email"] = username
        self.br["pass"] = password
        resp = self.br.submit()
        headers = str(resp.info())
        if 'login_attempt' in headers:
            self.output('Authentication failed.')
            return False
        if 'checkpoint' in headers:
            resp = self.br.follow_link(nr=1)
            self.output('Checkpoint security active. Log in via browser and try again.')
            return False
        return True

    def get_company_id(self, company):
        search = '"people who work for %s"' % (company)
        self.verbose('Searching Facebook Graph API for: %s ...' % search)
        search = urllib.quote(search)
        resource = '/typeahead/search/facebar/query/?value=[%s]&grammar_version=9a4a4f16b0229da235ba203aa5cfa4d59acfa507&max_results=10&__a=1' % (search)
        resp = self.br.open(resource)
        content = resp.read()
        companies = json.loads(content[9:])['payload']['entities']
        # return nothing if there are no matches
        if not companies:
            self.output('No company matches found.')
            return
        # return a unique match in such exists
        elif len(companies) == 1:
            self.alert('Unique company match found: %s' % (companies[0]['text']))
            return companies[0]['uid']
        # prompt the user to choose from multiple matches
        else:
            # display the choices
            choices = range(0, len(companies))
            for i in choices:
                self.output('[%d] %s' % (i, companies[i]['text']))
            choice = raw_input('Choose a company [0]: ')
            # the first choice is the default
            if choice is '':
                return companies[0]['uid']
            # make sure the choice is valid
            elif int(choice) not in choices:
                self.output('Invalid choice.')
                return
            # return the chosen company id
            else:
                return companies[int(choice)]['uid']

    def get_contacts(self, company):
        self.verbose('Extracting results for entity ID \'%s\'...' % (company))
        entities = []
        # get first results from the page itself
        resp = self.br.open('/search/%s/employees/present' % (urllib.pathname2url(company)))
        content = resp.read()
        self.extract_entities(content.decode('utf-8'))
        # find bigpipe information
        bigpipe = re.search(r'\{"view":"[^"]*","encoded_query":"{\\"bqf\\":\\"([^\\]*)\\",\\"vertical\\":[^}]*}","encoded_title":"([^"]*)","ref":"[^"]*","logger_source":"[^"]*","typeahead_sid":"[^"]*","tl_log":[^,]*,"impression_id":"[^"]*","filter_ids":\{[^\}]*\},"experience_type":"[^"]*","exclude_ids":[^\}]*\}', content)
        if bigpipe:
            query = bigpipe.group(1)
            title = bigpipe.group(2)
            while True:
                cursor = re.search(r'\[\{"cursor":"([^"]*)","page_number":[^}]*\}\]', content)
                if all((cursor, 'End of results' not in content, 'partial matches' not in content)):
                    data = '{"view":"list","encoded_query":"%s","encoded_title":"%s","experience_type":"grammar","cursor":"%s","ads_at_end":true}' % (query, title, cursor.group(1))
                    url = 'https://www.facebook.com/ajax/pagelet/generic.php/BrowseScrollingSetPagelet?data=%s&__a=1' % (urllib.quote(data))
                    resp = self.br.open(url)
                    content = resp.read()
                    payload = json.loads(content[9:], encoding='utf-8')['payload']
                    self.extract_entities(payload)
                else:
                    break

    def extract_entities(self, content):
        names = re.findall(r'class=\"_5d-5\">([^<]*)', content)
        titles = re.findall(r'data-bt="[^"]*sub_headers[^"]*">(?:<a href="[^"]*" data-hovercard="[^"]*">([^<]*)</a>)*', content)
        if len(names) != len(titles):
            self.alert('Inconsistent quantity of names and titles parsed. Data corruption imminent.')
        for name, title in zip(names, titles):
            fname, mname, lname = self.parse_name(name)
            title = self.html_unescape(title or 'Employee')
            self.output('%s - %s' % (name, title))
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title)
