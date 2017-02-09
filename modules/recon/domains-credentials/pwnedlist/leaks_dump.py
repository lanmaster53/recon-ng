from recon.core.module import BaseModule

class Module(BaseModule):

    meta = {
        'name': 'PwnedList - Leak Details Retriever',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Queries the PwnedList API for information associated with all known leaks. Updates the \'leaks\' table with the results.',
        'required_keys': ['pwnedlist_api', 'pwnedlist_secret'],
        'comments': (
            'API Query Cost: 1 query per request.',
        ),
        'query': 'SELECT DISTINCT leak_id FROM leaks WHERE leak_id IS NOT NULL',
    }

    def module_run(self, leak_ids):
        for leak_id in leak_ids:
            self.get_pwnedlist_leak(leak_id)
