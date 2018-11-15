from recon.core.module import BaseModule
import lxml

class Module(BaseModule):
    meta = {
        'name': 'FindSubDomains DNS search',
        'author': 'Pedro Rodrigues (@Pedro_SEC_R)',
        'description': 'Queries the FindSubDomain page for sub-domain information in a domain.',
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
    }

    def module_run(self, domains):
        for domain in domains:
            self.heading(domain, level=0)
            resp = self.request(url='https://findsubdomains.com/subdomains-of/%s' % domain)

            if resp.status_code == 200:
                doc = lxml.html.document_fromstring(resp.text)
                el = doc.xpath("//a[contains(@class, 'aggregated-link mobile-hidden')]")
                for elem in el:
                    hostname = u''.join(elem.text.strip())
                    self.add_hosts(host=hostname)
            else:
                self.error("Error retrieving results")
