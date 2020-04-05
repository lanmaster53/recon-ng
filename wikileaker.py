#!/usr/bin/env python3


# module specific imports
from recon.core.module import BaseModule
from recon.mixins.threads import ThreadingMixin
import os
import sys
import time
import re
import requests
from bs4 import BeautifulSoup
import pandas as pd


class Module(BaseModule, ThreadingMixin):

    meta = {
        'name': 'WikiLeaker',
        'author': 'Joe Gray (@C_3PJoe)',
        'version': '1.0',
        'description': 'A WikiLeaks scraper inspired by the Datasploit module previously written in Python2.',
        'dependencies': ['pandas', 're', 'requests', 'time', 'sys', 'bs4'],
        'query': 'SELECT DISTINCT domain FROM domains WHERE domain IS NOT NULL',
        #   'comments': ('This module, inspired by the module written in Python2 as part of Datasploit, searches Wikileaks for leaks containing the subject domain. If anything is found, this module will seek to parse out the URL, Sender Email, Date, Leak, and Subject of the email. This will upate the \'Contacts\' table with the results.'),
    }

    def module_run(self, domains):
        URL_REGEX = re.compile(r"\<h4\>\<a\shref\=\"(?P<URL>https\:\/\/wikileaks\.org\S+)\"\>")
        SUBJ_REGEX = re.compile(r"\<h4\>\<a\shref\=\"https\:\/\/wikileaks\.org\S+\"\>\s(?P<subj>\S.+)\<\/a")
        SENDR1_REGEX = re.compile(r"email\:\s(?P<sender>\S.+\@\S.+\.\w{3}) ")
        SENDR2_REGEX = re.compile(r"email\:\s(?P<sender>\S+[\.|\<b\>]\w+)\<\/b\>")
        LEAK_REGEX = re.compile(r"leak\-label\"\>\n\<div\>\<b\>(?P<date>\S.+)\<\/b\>")
        DATE_REGEX = re.compile(r"Created\<br\/>\n\<span\>(?P<date>\d{4}\-\d{2}\-\d{2})")
        for domain in domains:
            DOMAIN = domain
            URL = 'https://search.wikileaks.org/?query=&exact_phrase='+DOMAIN+'&include_external_sources=True&order_by=newest_document_date'
            self.verbose(URL)
            REQ_VAR = self.request('GET', URL)
            time.sleep(1)
            wiki_df = pd.DataFrame(columns=['Date', 'Sender', 'Subject', 'URL', 'Leak'])
            soup_var = BeautifulSoup(REQ_VAR.content, "lxml")
            divtag_var = soup_var.findAll('div', {'class': 'result'})
            for a in divtag_var:
                url_var = URL_REGEX.findall(str(a))
                date_var = DATE_REGEX.findall(str(a))
                subj_var = SUBJ_REGEX.findall(str(a))
                sendr1_var = SENDR1_REGEX.findall(str(a))
                sendrx_var = SENDR2_REGEX.findall(str(a))
                leak_var = LEAK_REGEX.findall(str(a))
                sendr2_var = re.sub(r'\<b\>', '', str(sendrx_var))
                if sendr1_var:
                    sendr_var = sendr1_var
                elif sendr2_var:
                    sendr_var = sendr2_var
                wiki_df = wiki_df.append({'Date': date_var, 'Sender': sendr_var, 'Subject': subj_var, 'URL': url_var, 'Leak': leak_var}, ignore_index=True, sort=True)
            for index, r in wiki_df.iterrows():
                date_var = r['Date']
                sendr_var = r['Sender']
                subj_var = r['Subject']
                url_var = r['URL']
                leak_var = r['Leak']
                self.alert(f'Leak: {leak_var}')
                self.output(f'URL: {url_var}')
                self.verbose(f'Date: {date_var}')
                self.verbose(f'Sender: {sendr_var}')
                self.verbose(f'Subject: {subj_var}')
                self.insert_contacts(email=sendr_var)
