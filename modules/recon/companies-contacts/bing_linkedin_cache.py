from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'Bing Cache Linkedin Profile and Contact Harvester',
        'author':'Joe Black (@MyChickenNinja) and @fullmetalcache',
        'description': 'Harvests profiles from LinkedIn by querying the Bing API cache for LinkedIn pages related to the given companies, and adds them to the \'profiles\' table. The module will then parse the resulting information to extract the user\'s full name and job title (title parsing is a bit spotty currently). The user\'s full name and title are then added to the \'contacts\' table. This module does not access LinkedIn at any time.',
        'comments': (
            'Be sure to set the \'SUBDOMAINS\' option to the region your target is located in.',
            'You will get better results if you use more subdomains other than just \'www\'.',
            'Multiple subdomains can be provided in a comma separated list.',
        ),
        'query': 'SELECT DISTINCT company FROM companies WHERE company IS NOT NULL',
        'options': (
            ('limit', 0, True, 'limit total number of pages per api request (0 = unlimited)'),
            ('subdomains', None, False, 'subdomain(s) to search on LinkedIn: www, ca, uk, etc.'),
        ),
    }

    def module_run(self, companies):
        for company in companies:
            self.heading(company, level=0)
            self.get_profiles(company)
            if " " in company:
                company = company.replace(" ", "")
                self.get_profiles(company)

    def get_profiles(self, company):
        results = []
        subdomains = self.options['subdomains']
        subdomain_list = [''] if not subdomains else [x.strip()+'.' for x in subdomain.split(',')]
        for subdomain in subdomain_list:
            base_query = [
                "site:\"%slinkedin.com/in/\" && %s" % (subdomain, company),
                "site:%slinkedin.com -jobs && %s" % (subdomain, company),
                "site:%slinkedin.com instreamset:(url):\"pub\" -instreamset:(url):\"dir\" && %s" % (subdomain, company)
            ]
            for query in base_query:
                results = self.search_bing_api(query, self.options['limit'])
                for result in results:
                    url = result['Url']
                    description = result['Description']
                    title = result['Title']
                    cache = (title, description)
                    # still getting quite a few false positives for former employees
                    # also, getting a log of jobs, article, etc. that aren't people
                    if '/pub/dir/' not in url and company.lower() not in title.lower():
                        if company.lower() in description.lower():
                            self.alert('Probable match: %s' % (url))
                            self.verbose('Parsing \'%s\'...' % (url))
                            username = self.parse_username(url)
                            self.add_profiles(username=username, url=url, resource='LinkedIn', category='social')
                            self.get_contact_info(cache)

    def parse_username(self, url):
        username = None
        # skip this for now. too unreliable
        return username
        # regex might be better for this
        if '/in/' in url:
            url = url.split('/in/')[1]
            url = url.split('?')[0]
            username = url.rsplit('-',1)[0]
        elif '/pub/' in url:
            url = url.split('/pub/')[1]
            url = url.split('?')[0]
            username = url.split('/')[0]
        return username

    def get_contact_info(self, cache):
        title = cache[0]
        description = cache[1]
        fullname, fname, mname, lname = self.parse_fullname(title)
        jobtitle = self.parse_jobtitle(fullname, description)
        self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=jobtitle)

    def parse_fullname(self, title):
        fullname = title.split(" |")[0]
        fullname = fullname.split(",")[0]
        fname, mname, lname = self.parse_name(fullname)
        return fullname, fname, mname, lname

    def parse_jobtitle(self, fullname, description):
        jobtitle = 'Employee'
        titles = description.split(' at ')
        if len(titles) > 1:
            try:
                jobtitle = titles[0].split(fullname)[1]
                jobtitle = jobtitle.replace(', ', '', 1)
                jobtitle = jobtitle.replace('. ', '', 1)
            except IndexError:
                pass
        return jobtitle
