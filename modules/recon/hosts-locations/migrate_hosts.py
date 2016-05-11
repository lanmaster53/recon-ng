from recon.core.module import BaseModule
import os
import re

class Module(BaseModule):

    meta = {
        'name': 'Hosts to Locations Data Migrator',
        'author': 'Tim Tomes (@LaNMaSteR53)',
        'description': 'Adds a new location for all the locations stored in the \'hosts\' table.',
        'query': 'SELECT DISTINCT latitude, longitude FROM hosts WHERE latitude IS NOT NULL AND longitude IS NOT NULL',
    }

    def module_run(self, locations):
        for location in locations:
            self.add_locations(latitude=location[0], longitude=location[1])
