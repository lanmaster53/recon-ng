import module
# unique to module
import re
import urllib

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('company', self.global_options['company'], 'yes', self.global_options.description['company'])
        self.register_option('company_url', None, 'no', 'direct url to the company page (skip discovery)')
        self.info = {
                     'Name': 'Jigsaw Contact Enumerator',
                     'Description': 'Harvests contacts from Jigsaw.com and updates the \'contacts\' table of the database with the results.',
                     'Comments': [
                                  'Discovery does not always succeed due to alphabetical inconsistencies in the Data.com data sets. Use the following link to drill down to the target company and set the \'COMPANY_URL\' option.',
                                  'Link: http://www.data.com/connect/index.jsp'
                                  ]
                     }

    def module_run(self):
        if self.options['company_url']:
            self.get_contacts(self.options['company_url'])
        else:
            host = 'https://connect.data.com'
            resource = self.get_company_url(host)
            if resource:
                self.get_contacts(host + resource)

    def get_company_url(self, host):
        self.output('Fetching Company URL...')
        resource = '/directory/company/%s' % (self.options['company'][0].lower())
        while True:
            # widdle down through the alphabetical list of companies
            url = host + resource
            self.verbose('Query: %s' % (url))
            resp = self.request(url)
            # check to see if companies have been reached
            if re.search('/directory/company/list', resp.text):
                return self.choose_company(resp)
            # keep widdling
            tags = re.findall('[^>]<a href="(/directory/company/[^"]*)">([^<]*)</a>', resp.text)
            # conduct an alphabetical comparison to determing which range to select
            for tag in tags:
                first = tag[1].split(' - ')[0].lower()
                last = tag[1].split(' - ')[1].lower()
                middle = self.options['company'].lower()
                order = [first, middle, last]
                ordered = sorted(order)
                if order == ordered:
                    resource = tag[0]
                    self.output('Alphabetical range identified: %s' % (tag[1]))
                    break
            # resource should equal tag[0] if range was found, otherwise return nothing
            if resource != tag[0]:
                self.output('Company not found in the provided alphabetical ranges.')
                return

    def choose_company(self, resp):
        companies = []
        tags = re.findall('<a href="(/directory/company/list/[^"]*)">([^<]*)</a>', resp.text)
        # build companies list of possible matches
        for tag in tags:
            if self.options['company'].lower() in tag[1].lower():
                companies.append(tag)
        # return nothing if there are no matches
        if not companies:
            self.output('No Company Matches Found.')
            return
        # return a unique match in such exists
        elif len(companies) == 1:
            self.alert('Unique Company Match Found: %s' % (companies[0][1]))
            return companies[0][0]
        # prompt the user to choose from multiple matches
        else:
            # display the choices
            choices = range(0, len(companies))
            for i in choices:
                self.output('[%d] %s' % (i, companies[i][1]))
            choice = raw_input('Choose a Company [0]: ')
            # the first choice is the default
            if choice is '':
                return companies[0][0]
            # make sure the choice is valid
            elif choice not in [str(x) for x in choices]:
                self.output('Invalid choice.')
                return
            # return the chosen company id
            else:
                return companies[int(choice)][0]

    def get_contacts(self, url):
        self.output('Fetching Contacts...')
        payload = {'page': 1}
        cnt = 0
        new = 0
        while True:
            self.verbose('Query: %s?%s' % (url, urllib.urlencode(payload)))
            resp = self.request(url, payload=payload)
            if 'Sorry. No contacts found for' in resp.text: break
            #if not re.search('\?page='): break
            values = re.findall('<td class="ellipsis">[^>]*>([^<]*)</span>', resp.text, re.DOTALL)
            contacts = [values[i:i+6] for i in range(0, len(values), 6)]
            for contact in contacts:
                fname = self.html_unescape(contact[1])
                # fname includes the preferred name as an element that needs to be removed
                fname = ' '.join(fname.split()[:2]) if len(fname.split()) > 2 else fname
                lname = self.html_unescape(contact[0])
                name = '%s %s' % (fname, lname)
                fname, mname, lname = self.parse_name(name)
                title = self.html_unescape(contact[2])
                loc1 = self.html_unescape(contact[5])
                loc2 = self.html_unescape('')
                region = []
                for item in [loc1, loc2]:
                    if item: region.append(item)
                region = ', '.join(region)
                self.output('%s - %s (%s)' % (name, title, region))
                cnt += 1
                new += self.add_contact(fname=fname, mname=mname, lname=lname, title=title, region=region)
            payload['page'] += 1
        self.output('%d total contacts found.' % (cnt))
        if new: self.alert('%d NEW contacts found!' % (new))
