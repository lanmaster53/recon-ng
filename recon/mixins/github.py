import time


class GithubMixin(object):

    def query_github_api(self, endpoint, payload={}, options={}):
        opts = {'max_pages': None}
        opts.update(options)
        headers = {'Authorization': f"token {self.get_key('github_api')}"}
        base_url = 'https://api.github.com'
        url = base_url + endpoint
        results = []
        page = 1
        while True:
            # Github rate limit is 30 requests per minute
            time.sleep(2) # 60s / 30r = 2s/r
            payload['page'] = page
            resp = self.request('GET', url, headers=headers, params=payload)
            # check for errors
            if resp.status_code != 200:
                # skip 404s returned for no results
                if resp.status_code != 404:
                    self.error(f"Message from Github: {resp.json()['message']}")
                break
            # some APIs return lists, and others a single dictionary
            method = 'extend'
            if type(resp.json()) == dict:
                method = 'append'
            getattr(results, method)(resp.json())
            # paginate
            if 'link' in resp.headers and 'rel="next"' in resp.headers['link'] and (opts['max_pages'] is None or page < opts['max_pages']):
                page += 1
                continue
            break
        return results

    def search_github_api(self, query):
        self.verbose(f"Searching Github for: {query}")
        results = self.query_github_api(endpoint='/search/code', payload={'q': query})
        # reduce the nested lists of search results and return
        results = [result['items'] for result in results]
        return [x for sublist in results for x in sublist]
