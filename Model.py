#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import collections
import concurrent.futures
import datetime
import glob
import tempfile
import time

import regex as re
import snowballstemmer


PACKAGE_DIR = '/var/lib/apt/lists'
PACKAGE_PATTERN = '*Packages'


Deb = collections.namedtuple('Deb', ('name', 'ver', 'section',
                                     'description', 'url', 'size'))

class _Deb:

    def __init__(self):
        self.clear()


    @property
    def valid(self):
        return bool(self.name)


    def clear(self):
        self.name = ''
        self.ver = ''
        self.section = ''
        self.description = ''
        self.url = ''
        self.size = 0


    def update(self, key, value):
        if key == 'Package':
            self.name = value
            return False
        if key == 'Version':
            self.ver = value
            return False
        if key == 'Section':
            self.section = value
            return False
        if key == 'Description' or key == 'Npp-Description': # Ignore Npp?
            self.description += value
            return True
        if key == 'Homepage':
            self.url = value
            return False
        if key == 'Installed-Size':
            self.size = int(value)
            return False
        return False


    def totuple(self):
        return Deb(self.name, self.ver, self.section, self.description,
                   self.url, self.size)


class Model:

    def __init__(self, onReady):
        self.refresh(onReady)


    def _clear(self):
        self.debForName = {} # key = name, value = Deb
        # namesFor*: key = stemmed word, value = set of names
        self.namesForStemmedDescription = {}
        self.namesForStemmedName = {}
        self.namesForSection = {}
        self.timer = time.monotonic()


    def __len__(self):
        return len(self.debForName)


    def refresh(self, onReady):
        '''onReady is a callback: onReady(message: str,  done: bool)'''
        self._clear()
        if not self._loadFromCache(onReady):
            self._readPackages(onReady)
            self._indexPackages(onReady)
            self._saveToCache()


    def allSections(self):
        return self.namesForSection.keys()


    def allNames(self):
        return self.debForName.keys()


    @staticmethod
    def cacheFilename():
        return (f'{tempfile.gettempdir()}/'
                f'debfind-{datetime.date.today()}.cache')


    def _readPackages(self, onReady):
        try:
            count = 0
            filenames = glob.iglob(f'{PACKAGE_DIR}/{PACKAGE_PATTERN}')
            onReady('Reading Packages files…', False)
            with concurrent.futures.ProcessPoolExecutor() as executor:
                for debs in executor.map(self._readPackageFile, filenames):
                    count += 1
                    for deb in debs:
                        self.debForName[deb.name] = deb
            onReady(f'Read {len(self.debForName):,d} packages from '
                    f'{count:,d} Packages files in '
                    f'{time.monotonic() - self.timer:0.1f}sec…', False)
        except OSError as err:
            print(err)


    def _readPackageFile(self, filename):
        try:
            state = _State()
            debs = []
            deb = _Deb()
            with open(filename, 'rt', encoding='utf-8') as file:
                for lino, line in enumerate(file, 1):
                    self._readPackageLine(filename, lino, line, debs, deb,
                                          state)
            if deb.valid:
                debs.append(deb.totuple())
            return debs
        except OSError as err:
            print(err)


    def _readPackageLine(self, filename, lino, line, debs, deb, state):
        if not line.strip():
            if deb.valid:
                debs.append(deb.totuple())
            deb.clear()
            return
        if state.inDescription or state.inContinuation:
            if line.startswith((' ', '\t')):
                if state.inDescription:
                    deb.description += line
                return
            state.inDescription = state.inContinuation = False
        key, value, ok = _maybeKeyValue(line)
        if not ok:
            state.inContinuation = True
        else:
            state.inDescription = deb.update(key, value)


    def _indexPackages(self, onReady):
        onReady(f'Indexing {len(self.debForName):,d} packages…', False)
        for name, deb in self.debForName.items(): # concurrency doesn't help
            nameWords = _stemmedWords(name)
            for word in nameWords:
                self.namesForStemmedName.setdefault(word, set()).add(name)
            for word in _stemmedWords(deb.description) + nameWords:
                self.namesForStemmedDescription.setdefault(word,
                                                           set()).add(name)
            self.namesForSection.setdefault(deb.section, set()).add(name)
        onReady(f'Read and indexed {len(self.debForName):,d} packages in '
                f'{time.monotonic() - self.timer:0.1f}sec.', True)


    def _saveToCache(self):
        print('TODO _saveToCache')


    def _loadFromCache(self, onReady):
        print('TODO _loadFromCache')

        #onReady(f'Read {len(self.debForName):,d} packages and indexes '
        #        f'from cache in {time.monotonic() - self.timer:0.1f}sec.',
        #        True)
        return False


class _State:

    def __init__(self):
        self.inDescription = False
        self.inContinuation = False


def _maybeKeyValue(line):
    i = line.find(':')
    if i == -1:
        return None, None, False
    key = line[:i].strip()
    value = line[i + 1:].strip()
    return key, value, True


def _stemmedWords(line):
    nonLetterRx = re.compile(r'\P{L}+')
    stemmer = snowballstemmer.stemmer('english')
    return [word for word in stemmer.stemWords(
                     nonLetterRx.sub(' ', line).casefold().split())
            if len(word) > 1 and not word.isdigit() and
               not word.startswith('lib') and not word in _COMMON_STEMS]


_COMMON_STEMS = {
    'and', 'applic', 'bit', 'compil', 'data', 'debug', 'develop',
    'document', 'file', 'for', 'gnu', 'in', 'kernel', 'librari', 'linux',
    'modul', 'of', 'on', 'packag', 'python', 'runtim', 'support', 'the',
    'to', 'tool', 'version', 'with'}


if __name__ == '__main__':
    def onReady(message, done):
        print(message)
        if done:
            print('Done.')

    print('Model tests')
    model = Model(onReady)
