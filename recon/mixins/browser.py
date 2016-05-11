import mechanize
import socket

class BrowserMixin(object):

    def get_browser(self):
        '''Returns a mechanize.Browser object configured with the framework's global options.'''
        br = mechanize.Browser()
        # set the user-agent header
        br.addheaders = [('User-agent', self._global_options['user-agent'])]
        # set debug options
        if self._global_options['verbosity'] >= 2:
            br.set_debug_http(True)
            br.set_debug_redirects(True)
            br.set_debug_responses(True)
        # set proxy
        if self._global_options['proxy']:
            br.set_proxies({'http': self._global_options['proxy'], 'https': self._global_options['proxy']})
        # additional settings
        br.set_handle_robots(False)
        # set timeout
        socket.setdefaulttimeout(self._global_options['timeout'])
        return br
