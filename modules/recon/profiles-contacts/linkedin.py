from recon.core.module import BaseModule
from recon.utils.linkedin import parse_name, parse_title, parse_region, perform_login
from lxml.html import fromstring
import time

class Module(BaseModule):

    meta = {
        'name': 'Linkedin Contact Crawler',
        'author': 'Mike Larch and Brian Fehrman',
        'description': 'Harvests contacts from linkedin.com by parsing known profiles and adding the info to the \'contacts\' table.',
        'query': 'SELECT DISTINCT url FROM profiles WHERE url IS NOT NULL AND resource LIKE \'linkedin\'',
    }

    def module_run(self, urls):
        num_urls = len(urls)
        cookiej = None
        for url in urls:
            self.verbose('{0} URLs remaining.'.format(num_urls))
            cookiej = self.get_info(url, cookiej)
            num_urls -= 1

    def get_info(self, url, cookiej):
        time.sleep(0.333)
        self.verbose('Parsing \'%s\'...' % (url))
        retries = 5
        resp = None
        resp_text = None
        while 0 < retries:
            try:
                retries -= 1
                resp = self.request(url, cookiejar=cookiej)
                resp_text = resp.text
                if 'D8E90337EA is the' in resp_text:
                    self.verbose('Linkedin is limiting profile views, try logging in or re-login with a new account')
                    cookiej = perform_login()
                    retries += 1
                    continue
                break
            except Exception as e:
                self.error('{0}, {1} retries left'.format(e, retries))
        if resp_text is None:
            return cookiej
        resp = self.request(url)
        tree = fromstring(resp.text)
        name = parse_name(tree)
        if name is None:
            return cookiej
        fname, mname, lname = self.check_name(*self.parse_name(name))
        title = parse_title(tree) or 'Employee'
        region = parse_region(tree) or ''
        # output the results
        self.alert('%s %s - %s (%s)' % (fname, lname, title, region))
        self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title, region=region)
        return cookiej
        
    def check_name(self, fname, mname, lname):
        titles = ['CISSP', 'CPA', 'DDS', 'ERPA', 'LLM', 'MBA', 'PhD', 'PHD']
        if lname is not None:
            lname = lname.split(',')[0]
            lname = lname.replace('.', '')
            for title in titles:
                if title in lname:
                    lname = mname
                    mname = ''
        if fname is not None:
            fname = fname.split('/')[0]
        return fname, mname, lname
