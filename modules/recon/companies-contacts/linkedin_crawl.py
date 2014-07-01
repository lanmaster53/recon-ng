import module
# unique to module
from io import StringIO
from lxml import etree
import re
import time

class Module(module.Module):

    def __init__(self, params):
        module.Module.__init__(self, params)
        self.register_option('url', None, 'yes', 'public LinkedIn profile URL (seed)')
        self.register_option('company', None, 'no', 'override the company name harvested from the seed \'URL\'')
        self.info = {
                     'Name': 'Linkedin Contact Crawler',
                     'Author':'Mike Larch',
                     'Description': 'Harvests contacts from linkedin.com by spidering through "Viewers of this profile also viewed" links, adding them to the \'contacts\' table of the database. URL must be for a public linkedin page. The User of that page must currently be working at the targeted company.'
                     }

    def module_run(self):
        company = self.get_company()
        if company is not None:
            self.heading(company, level=0)
            self.get_info(company)
        else:
            self.error('No company found on seed profile page.')

    def get_company(self):
        company = self.options['company']
        if company is None:
            resp = self.request(self.options['url'])
            tree = etree.parse(StringIO(resp.text), etree.HTMLParser())
            company = parse_company(tree)
        return(company)

    def get_info(self, company):
        temp_urls = [self.options['url']]
        accepted = []
        rejected = []
        i = len(temp_urls)
        new = 0
        cnt = 0
        while i > 0:
            temp_url = temp_urls.pop(0)
            time.sleep(1)
            self.verbose('Parsing \'%s\'...' % (temp_url))
            resp = self.request(temp_url)
            tree = etree.parse(StringIO(resp.text), etree.HTMLParser())
            temp_company = parse_company(tree)
            if company is not None and temp_company is not None and company in temp_company:
                accepted.append(temp_url)
                try:
                    fname = tree.xpath('//span[@class="given-name"]/text()')[0].split(' ',1)[0]
                    mname = ''
                    lname = tree.xpath('//span[@class="family-name"]/text()')[0].split(',',1)[0]
                except IndexError:
                    name = tree.xpath('//span[@class="full-name"]/text()')
                    if name:
                        fname, mname, lname = self.parse_name(name[0])
                    else:
                        continue
                try:
                    region = tree.xpath('//span[@class="locality"]/text()')[0].strip()
                except:
                    region = ''
                title = '%s at %s' % (parse_title(tree), temp_company)
                # parse "also viewed" urls
                parsed_urls = tree.xpath('//li[@class="with-photo"]/a/@href')
                if not parsed_urls:
                    parsed_urls = tree.xpath('//div[@class="insights-browse-map"]/ul/li/a/@href')
                # add unique urls to the list of urls to be crawled
                temp_urls += [x for x in parsed_urls if x not in temp_urls+accepted+rejected]
                # output the results
                self.alert('%s %s - %s (%s)' % (fname, lname, title, region))
                cnt += 1
                new += self.add_contacts(first_name=fname, middle_name=mname, last_name=lname, title=title, region=region)
            else:
                rejected.append(temp_url)
            i = len(temp_urls)
            self.verbose('%d URLs remaining.' % (i))
        self.summarize(new, cnt)
        return

def parse_title(tree):
    title = 'Employee'
    try: title = tree.xpath('//ul[@class="current"]/li/text()')[0].strip()
    except IndexError:
        try: title = tree.xpath('//p[@class="headline-title title"]/text()')[0].strip()
        except IndexError:
            try: title = tree.xpath('//p[@class="title "]/text()')[0].strip().split(" at ",1)[0]
            except IndexError:
                pass
    return title

def parse_company(tree):
    company = None
    try: company = tree.xpath('//ul[@class="current"]/li/a/span[@class="org summary"]/text()')[0]
    except IndexError:
        try: company = tree.xpath('//ul[@class="current"]/li/text()')[1].strip()
        except IndexError:
            try: company = tree.xpath('//p[@class="headline-title title"]/text()')[0].strip().split(" at ",1)[1]
            except IndexError:
                try: company = tree.xpath('//p[@class="title "]/text()')[0].strip().split(" at ",1)[1]
                except IndexError:
                    try: company = tree.xpath('//tr[@id="overview-summary-current"]/td/ol/li/a/text()')[0]
                    except:
                        pass
    return company
