from recon.core.module import BaseModule
from recon.mixins.search import GoogleWebMixin
import recon.utils.parsers as parsers
import itertools

# to do:
# extract email addresses from text
# add info to database

class Module(BaseModule, GoogleWebMixin):

    meta = {
        'name': 'Meta Data Extractor',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Searches for files associated with the provided domain(s) and extracts any contact related metadata.',
        'comments': (
            'Currently supports doc, docx, xls, xlsx, ppt, pptx, and pdf file types.',
        ),
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        'options': (
            ('extract', False, True, 'extract metadata from discovered files'),
        ),
    }

    def module_run(self, domains):
        exts = {
            'ole': ['doc', 'xls', 'ppt'],
            'ooxml': ['docx', 'xlsx', 'pptx'],
            'pdf': ['pdf'],
        }
        search = 'site:%s ' + ' OR '.join(['filetype:%s' % (ext) for ext in list(itertools.chain.from_iterable(exts.values()))])
        for domain in domains:
            self.heading(domain, level=0)
            results = self.search_google_web(search % domain)
            for result in results:
                self.output(result)
                # metadata extraction
                if self.options['extract']:
                    # parse the extension of the discovered file
                    ext = result.split('.')[-1]
                    # search for the extension in the extensions dictionary
                    # the extensions dictionary key indicates the file type
                    for key in exts:
                        if ext in exts[key]:
                            # check to see if a parser exists for the file type
                            if hasattr(parsers, key+'_parser'):
                                try:
                                    func = getattr(parsers, key + '_parser')
                                    resp = self.request(result)
                                    # validate that the url resulted in a file 
                                    if resp.headers['content-type'].startswith('application'):
                                        meta = func(resp.raw)
                                        # display the extracted metadata
                                        for key in meta:
                                            if meta[key]:
                                                self.alert('%s: %s' % (key.title(), meta[key]))
                                    else:
                                        self.error('Resource not a valid file.')
                                except Exception:
                                    self.print_exception()
                            else:
                                self.alert('No parser available for file type: %s' % ext)
                            break
            self.alert('%d files found on \'%s\'.' % (len(results), domain))
