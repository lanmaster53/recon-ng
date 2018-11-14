from recon.core.module import BaseModule
import re

class Module(BaseModule):

    meta = {
        'name': 'Bing Cache Linkedin Profile and Contact Harvester',
        'author':'Joe Black (@MyChickenNinja), @fullmetalcache, and Brian King',
        'description': 'Harvests profiles from LinkedIn by querying the Bing API cache for LinkedIn pages related to the given companies, and adds them to the \'profiles\' table. The module will then parse the resulting information to extract the user\'s full name and job title (title parsing recently improved). The user\'s full name and title are then added to the \'contacts\' table. This module does not access LinkedIn at any time.',
        'required_keys': ['bing_api'],
        'comments': (
            'Be sure to set the \'SUBDOMAINS\' option to the region your target is located in.',
            'You will get better results if you use more subdomains other than just \'www\'.',
            'Multiple subdomains can be provided in a comma separated list.',
            'Results will include historical associations, not just current employees.',
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
        subdomain_list = [''] if not subdomains else [x.strip()+'.' for x in subdomains.split(',')]
        for subdomain in subdomain_list:
            base_query = [
                "site:\"%slinkedin.com/in/\" \"%s\"" % (subdomain, company),
                "site:\"%slinkedin.com\" -jobs \"%s\"" % (subdomain, company),
            ]
            for query in base_query:
                results = self.search_bing_api(query, self.options['limit'])
                for result in results:
                    name     = result['name']
                    url      = result['displayUrl']
                    snippet  = result['snippet']
                    username = self.parse_username(url)
                    cache    = (name,snippet,url,company)
                    self.get_contact_info(cache)

    def parse_username(self, url):
        username = None
        username = url.split("/")[-1]
        return username

    def get_contact_info(self, cache):
        (name, snippet, url, company) = cache
        fullname, fname, mname, lname = self.parse_fullname(name)
        if fname is None or 'LinkedIn' in fullname or 'profiles' in name.lower() or re.search('^\d+$',fname): 
            # if 'name' has these, it's not a person.
            pass
        elif u'\u2013' in snippet:
            # unicode hyphen between dates here usually means no longer at company.
            # Not always, but nothing available seems more consistent than that.
            pass
        else:
            username = self.parse_username(url)
            jobtitle = self.parse_jobtitle(company, snippet)
            self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=jobtitle)
            self.add_profiles(username=username, url=url, resource='LinkedIn', category='social')

    def parse_fullname(self, name):
        fullname = name.split(" -")[0]
        fullname = fullname.split(" |")[0]
        fullname = fullname.split(",")[0]
        fname, mname, lname = self.parse_name(fullname)
        return fullname, fname, mname, lname

    def parse_jobtitle(self, company, snippet):
        # sample 'snippet' strings with titles. (all contain this string: ' at ')
        # "John Doe. Director of QA at companyname. Location New York, New York Industry Electrical/Electronic Manufacturing"
        # "View John Doe\u2019s professional profile on LinkedIn. ... New Products Curator at companyname. Jane Doe. Sales Operations Analyst at othercompany", 

        # sample 'snippet' strings that are troublemakers
        # View John Doe\u2019s professional profile on ... children will have jobs. ... Security Researcher and Consultant at companyname. Jack ..."

        # sample 'snippet' strings with *no* titles. (none contain this string: ' at ')
        # "View John Doe\u2019s professional profile on LinkedIn. LinkedIn is the world's largest business network, helping professionals like John Doe ...", 
        # "View John Doe\u2019s professional profile on LinkedIn. ... companyname; Education: Carnegie Mellon University; 130 connections. View John\u2019s full profile."

        # outliers (contain a title, but we don't detect it)
        # Jane Doe. cfo, acompanyname. Location Greater New York City Area Industry Electrical/Electronic Manufacturing"

        company = company[:5].lower()   # if no variant of company name in snippet, then no title.
        jobtitle = 'Undetermined'       # default if no title found
        chunks   = snippet.split('...') # if more than one '...' then no title or can't predict where it is
        if ' at ' in snippet and not 'See who you know' in snippet and company in snippet.lower() and len(chunks) < 3:
            if re.search('^View ', snippet):    # here we want the string after " ... " and before " at "
                m = re.search('\.{3} (?P<title>.+?) at ', snippet)
            else:                                   # here we want the string after "^$employeename. " and before " at "
                m = re.search('^[^.]+. (?P<title>.+?) at ', snippet)
            try:
                jobtitle = m.group('title')
            except AttributeError:
                pass
        return jobtitle

