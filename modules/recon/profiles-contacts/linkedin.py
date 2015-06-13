from recon.core.module import BaseModule
from io import StringIO
from lxml.html import fromstring
import re
import time

class Module(BaseModule):

    meta  = {
        'name': 'Linkedin Contact Crawler',
        'author':'Mike Larch and Brian Fehrman',
        'description': 'Harvests contact information from linkedin.com by parsing the link(s) given and adding the info to the \'contacts\' table.',
        'query': 'SELECT DISTINCT url FROM profiles WHERE url IS NOT NULL ORDER BY url',
    }
    

    def module_run(self, urls):
        num_urls = len(urls)
        for url_curr in urls:
            self.verbose('{0} URLs remaining.'.format(num_urls))
            self.get_info(url_curr)
            num_urls -= 1

    def get_info(self, url):
        time.sleep(1)
        self.verbose('Parsing \'%s\'...' % (url))

        resp = self.request(url)
            
        tree = fromstring(resp.text)
        
        title = self.parse_title(tree)
        
        if title is None:
            title = 'Employee'
        
        try:
            fname = tree.xpath('//span[@class="given-name"]/text()')[0].split(' ',1)[0]
            mname = ''
            lname = tree.xpath('//span[@class="family-name"]/text()')[0].split(',',1)[0]
        except IndexError:
            name = tree.xpath('//span[@class="full-name"]/text()')
            if name:
                fname, mname, lname = self.parse_name(name[0])
            else:
                return
        try:
            region = tree.xpath('//span[@class="locality"]/text()')[0].strip()
        except IndexError:
            region = ''
        
        # output the results
        self.alert('%s %s - %s (%s)' % (fname, lname, title, region))
        self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title, region=region)
        
    def parse_title(self, tree):
        title = None
        
        #try parsing via the tree method
        title = self.parse_title_tree(tree)
                
        return title

    def parse_title_tree(self, tree):
        title = None
                
        try: title = tree.xpath('//ul[@class="current"]/li/text()')[0].strip()
        except IndexError:
            try: title = tree.xpath('//p[@class="headline-title title"]/text()')[0].strip()
            except IndexError:
                try: title = tree.xpath('//p[@class="title"]/text()')[0].strip().split(" at ",1)[0]
                except IndexError:
                    pass
        return title
