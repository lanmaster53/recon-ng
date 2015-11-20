from cookielib import CookieJar
from io import StringIO
from lxml.html import fromstring
import getpass
import re
import urllib
import urllib2

'''
doesn't parse properly:
https://www.linkedin.com/pub/chris-gerwig/53/b27/8ab
'''

def parse_username(url):
    username = None
    try:
        url = url.split('/pub/')[1]
        username = url.split('/')[0]
    except IndexError:
        pass
    return username

def parse_company(tree, content, company, previous):
    company_found = _parse_company_exp(previous, content, company)
    if company_found is None:
        company_found = _parse_company_tree(tree, company)
    return company_found

def perform_login():
    cj = CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    resp = opener.open('https://www.linkedin.com/uas/login?goback=&trk=hb_signin')
    if resp is None:
        return None
    # get values required for authentication post
    tree = fromstring(resp.read())
    vals = {'isJsEnabled'       : 'true',
            'clickedSuggestion' : 'false',
            'session_key'       : '',
            'session_password'  : '',
            'signin'            : 'Sign In',
            'trk'               : 'hb_signin',
            'loginCsrfParam'    : '',
            'csrfToken'         : '',
            'sourceAlias'       : '' }
    try:
        vals['loginCsrfParam'] = tree.xpath('//input[@id="loginCsrfParam-login"]/@value')[0].strip()
        vals['csrfToken'] = tree.xpath('//input[@id="csrfToken-login"]/@value')[0].strip()
        vals['sourceAlias'] = tree.xpath('//input[@id="sourceAlias-login"]/@value')[0].strip()
    except IndexError:
        return None
    vals['session_key'] = raw_input('Please enter your linkedin email address:')
    vals['session_password'] = getpass.getpass('Please enter your linkedin password:')
    data = urllib.urlencode(vals)
    opener.addheaders = [
        ('Content-Type', 'application/x-www-form-urlencoded'),
        ('charset', 'UTF-8'),
        ('X-IsAJAXForm', '1')
    ]
    resp = opener.open('https://www.linkedin.com/uas/login-submit', data)
    if resp is None:
        return None
    resp_text = resp.read().encode('utf-8')
    if '"status":"ok"' in resp_text:
        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
        resp = opener.open('https://www.linkedin.com/nhome/?trk=hb_signin')
        if resp is None:
            return None
        else:
            print 'Retrieved cookies'
            return cj
    return None

def _parse_company_exp(previous, content, company):
    try:
        experiences = content.split('<ul class="positions">', 1)[1]
        experiences = experiences.split('</section>', 1)[0]
        experiences = experiences.split('</li>')
    except IndexError:
        try:
            experiences = content.split('<div id="experience-', 1)[1]
            experiences = experiences.split('-view">', 1)[1]
            experiences = experiences.split('<script>', 1)[0]
            experiences = experiences.split('</div></div>')
        except IndexError:
            return None
    for idx, experience in enumerate(experiences):
        # what is this for?
        if idx == (len(experiences) - 1):
            break
        try:
            experience = experience.split('</div>', 1)[0].lower()
        except IndexError:
            continue
        if company.lower() in experience or company.replace(' ','').lower() in experience:
            if previous or 'present' in experience:
                #print 'Found using content.'
                return company
    return None

def _parse_company_tree(tree, company):
    company_found = None
    try: company_found = tree.xpath('//ul[@class="current"]/li/a/span[@class="org summary"]/text()')[0]
    except IndexError:
        try: company_found = tree.xpath('//ul[@class="current"]/li/text()')[1].strip()
        except IndexError:
            try: company_found = tree.xpath('//p[@class="headline-title title"]/text()')[0].strip().split(" at ",1)[1]
            except IndexError:
                try: company_found = tree.xpath('//p[@class="headline title"]/text()')[0].strip().split(" at ",1)[1]
                except IndexError:
                    try: company_found = tree.xpath('//p[@class="title"]/text()')[0].strip().split(" at ",1)[1]
                    except IndexError:
                        try: company_found = tree.xpath('//tr[@id="overview-summary-current"]/td/ol/li/a/text()')[0]
                        except:
                            pass
    if company_found is not None:
        if company.lower() in company_found.lower():
            #print 'Found using tree.'
            return company_found
    return None

def parse_also_viewed(tree):
    parsed_urls = tree.xpath('//div[@class="browse-map"]/ul/li/a/@href')
    for idx, parsed_url in enumerate(parsed_urls):
        parsed_urls[idx] = parsed_url.split('?',1)[0]
    return parsed_urls

def parse_name(tree):
    name = None
    try:
        fname = tree.xpath('//span[@class="given-name"]/text()')[0].split(' ',1)[0]
        lname = tree.xpath('//span[@class="family-name"]/text()')[0].split(',',1)[0]
        name = ' '.join((fname, lname))
    except IndexError:
        try: name = tree.xpath('//h1[@class="fn"]/text()')[0]
        except IndexError:
            try: name = tree.xpath('//span[@class="full-name"]/text()')
            except IndexError:
                pass
    return name

def parse_title(tree):
    title = None
    try: title = tree.xpath('//ul[@class="current"]/li/text()')[0].strip()
    except IndexError:
        try: title = tree.xpath('//p[@class="headline title"]/text()')[0].strip()
        except IndexError:
            try: title = tree.xpath('//p[@class="title"]/text()')[0].strip().split(" at ",1)[0]
            except IndexError:
                try: title = tree.xpath('//p[@class="headline-title title"]/text()')[0].strip()
                except IndexError:
                    pass
    return title

def parse_region(tree):
    region = None
    try: region = tree.xpath('//span[@class="locality"]/text()')[0].strip()
    except IndexError:
        pass
    return region
