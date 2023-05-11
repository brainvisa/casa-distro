# -*- coding: utf-8 -*-
import hashlib
import json
from urllib.request import urlopen


class Toolbox:
    def __init__(self, id, location):
        self.id = id
        self.location = location
        self._metadata = None

    @property
    def metadata(self):
        if self._metadata is None:
            with urlopen(self.location['metadata']) as f:
                j = f.read()
                expected_hash = self.location.get('metadata_hash')
                if expected_hash:
                    hash = hashlib.md5(j)
                    if hash.digest() != expected_hash:
                        raise ValueError(f'{self.location["metadata"]} '
                                         'content had been modified')
                self._metadata = json.loads(j)
        return self._metadata


class ToolboxesRepository:
    def __init__(self, url):
        self.url = url
        self._content = None

    @property
    def content(self):
        if self._content is None:
            with urlopen(self.url) as f:
                self._content = json.loads(f.read())
        return self._content

    def __iter__(self):
        return self.content.values()

    def toolbox(self, toolbox_id):
        toolbox_location = self.content[toolbox_id]
        return Toolbox(toolbox_id, toolbox_location)
