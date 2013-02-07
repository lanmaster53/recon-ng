#!/usr/bin/env python

from bs4 import BeautifulSoup
import optparse, re, urllib2

def printLinks(dom):
    url = "http://xssed.com/search?key=" + dom
    html = urllib2.urlopen(url)
    
    try:
        print '\n[-] Printing possible hits from XSSed.com for %s' % dom
        soup = BeautifulSoup(html.read())
        for link in soup.findAll('a', attrs={'href': re.compile("mirror")}):
            print "[+] Found http://xssed.com" + link.get('href')
 
            subhtml = urllib2.urlopen('http://xssed.com'+link.get('href'))
            subsoup = BeautifulSoup(subhtml.read())
            #rows = subsoup.findAll("th", {"class":"row3"})
            data = [a.get_text() for a in subsoup.findAll("th", {"class":"row3"})]
            print "[!]   %s\n[!]   %s\n[!]   %s, %s\n[!]   %s\n[!]   %s" % (data[5], data[8], data[0], data[1], data[3], data[6])
    except:
        pass
        
def main():
    parser = optparse.OptionParser('usage%prog -d <targetDomain>')
    parser.add_option('-d', dest='tgtDOMAIN', type='string', help='specify target domain')
    (options, args) = parser.parse_args()
    dom = options.tgtDOMAIN
    if dom == None:
        print parser.usage
        exit(0)
    else:
        printLinks(dom)
        
if __name__ == '__main__':
    main()
