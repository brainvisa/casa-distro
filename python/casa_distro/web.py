# -*- coding: utf-8 -*-
from __future__ import print_function

import os

try:
    # Python 2 imports
    from urllib import urlopen, urlretrieve
    from HTMLParser import HTMLParser
except ImportError:
    # Python 3 imports
    from urllib.request import urlopen, urlretrieve
    from html.parser import HTMLParser

class ListdirHTMLParser(HTMLParser):
    '''
    Class used by url_listdir to extract
    the list of file entries returned by
    Apache for an URL corresponding to a
    directory.
    '''
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_td = False
        self.record_data = False
        self.listdir = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
        if self.in_td and tag == 'a':
            self.record_data = True

    def handle_endtag(self, tag):
        if tag == 'td':
            self.in_td = False
        elif tag == 'a':
            self.record_data = False

    def handle_data(self, data):
        if self.record_data:
            self.listdir.append(data)

def url_listdir(url):
    '''
    Return the list of file or directory entries given a web URL corresponding
    to a directory. This function is specialized in parsing directories as 
    returned by an Apache server when no index.html file is present.
    '''
    parser = ListdirHTMLParser()
    parser.feed(urlopen(url).read().decode('utf8'))
    return parser.listdir[1:]

