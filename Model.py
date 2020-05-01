#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import collections
import concurrent.futures
import contextlib
import datetime
import glob
import os
import pickle
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
            self.section = _genericSection(value)
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


class Query:

    def __init__(self, *, section='', descriptionWords='',
                 matchAnyDescriptionWord=False, nameWords='',
                 matchAnyNameWord=False, includeLibraries=False):
        self.section = _genericSection(section)
        self.descriptionWords = descriptionWords
        self.matchAnyDescriptionWord = matchAnyDescriptionWord
        self.nameWords = nameWords
        self.matchAnyNameWord = matchAnyNameWord
        self.includeLibraries = includeLibraries


    def clear(self):
        self.section = ''
        self.descriptionWords = ''
        self.matchAnyDescriptionWord = False
        self.nameWords = ''
        self.matchAnyNameWord = False
        self.includeLibraries = False


    def __str__(self):
        matchDesc = 'Any' if self.matchAnyDescriptionWord else 'All'
        matchName = 'Any' if self.matchAnyNameWord else 'All'
        lib = ' Lib' if self.includeLibraries else ''
        return (f'section={self.section} desc={self.descriptionWords!r}'
                f'{matchDesc} name={self.nameWords!r}{matchName}{lib}')


class Model:

    def __init__(self, onReady):
        self.load(onReady)


    def _clear(self):
        self._debForName = {} # key = name, value = Deb
        # namesFor*: key = stemmed word, value = set of names
        self._namesForStemmedDescription = {}
        self._namesForStemmedName = {}
        self._namesForSection = {}
        self.timer = time.monotonic()


    def __len__(self):
        return len(self._debForName)


    def load(self, onReady, *, refresh=False):
        '''onReady is a callback: onReady(message: str,  done: bool)
        To refresh call model.load(onReady, refresh=True)
        '''
        self._clear()
        loaded = False
        if not refresh:
            loaded = self._loadFromCache(onReady)
        if not loaded:
            self._readPackages(onReady)
            self._indexPackages(onReady)
            self._saveToCache()


    @property
    def allSections(self):
        return self._namesForSection.keys()


    @property
    def allNames(self):
        return self._debForName.keys()


    def query(self, query):
        haveSection = set()
        haveDescription = set()
        haveName = set()
        constrainToSection = False
        constrainToDescription = False
        constrainToName = False
        if bool(query.section):
            constrainToSection = True
            haveSection = self._namesForSection.get(query.section)
        if bool(query.descriptionWords):
            constrainToDescription = True
            words = _stemmedWords(query.descriptionWords)
            for word in words:
                names = self._namesForStemmedDescription.get(word)
                if names is not None:
                    haveDescription |= set(names)
            # haveDescription is names matching Any word
            # Only accept matching All (doesn't apply if only one word)
            if len(words) > 1 and not query.matchAnyDescriptionWord:
                for word in words:
                    names = self._namesForStemmedDescription.get(word)
                    if names is not None:
                        haveDescription &= set(names)
        if bool(query.nameWords):
            constrainToName = True
            words = _stemmedWords(query.nameWords)
            for word in words:
                names = self._namesForStemmedName.get(word)
                if names is not None:
                    haveName |= set(names)
            # haveName is names matching Any word
            # Only accept matching All (doesn't apply if only one word)
            if len(words) > 1 and not query.matchAnyNameWord:
                for word in words:
                    names = self._namesForStemmedName.get(word)
                    if names is not None:
                        haveName &= set(names)
        names = set(self.allNames)
        if constrainToSection:
            names &= haveSection
        if constrainToDescription:
            names &= haveDescription
        if constrainToName:
            names &= haveName
        if query.includeLibraries:
            return names
        noLibNames = set()
        for name in names:
            if (('libre' in name or not name.startswith('lib')) and
                    '-lib' not in name):
                noLibNames.add(name)
        return noLibNames


    def _readPackages(self, onReady):
        try:
            count = 0
            filenames = glob.iglob(f'{PACKAGE_DIR}/{PACKAGE_PATTERN}')
            onReady('Reading Packages files…', False)
            with concurrent.futures.ProcessPoolExecutor() as executor:
                for debs in executor.map(self._readPackageFile, filenames):
                    count += 1
                    for deb in debs:
                        self._debForName[deb.name] = deb
            onReady(f'Read {len(self._debForName):,d} packages from '
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
        onReady(f'Indexing {len(self._debForName):,d} packages…', False)
        for name, deb in self._debForName.items(): # concurrency no help
            nameWords = _stemmedWords(name)
            for word in nameWords:
                self._namesForStemmedName.setdefault(word, set()).add(name)
            for word in _stemmedWords(deb.description) + nameWords:
                self._namesForStemmedDescription.setdefault(word,
                                                            set()).add(name)
            self._namesForSection.setdefault(deb.section, set()).add(name)
        onReady(f'Read and indexed {len(self._debForName):,d} packages in '
                f'{time.monotonic() - self.timer:0.1f}sec.', True)

    @staticmethod
    def _cacheFilename():
        return (f'{tempfile.gettempdir()}/'
                f'debfind-{datetime.date.today()}.cache')


    def _loadFromCache(self, onReady):
        filename = self._cacheFilename()
        if not os.path.exists(filename):
            return False
        try:
            with open(filename, 'rb') as file:
                data = pickle.load(file)
            debForName = data['debs']
            namesForStemmedDescription = data['descs']
            namesForStemmedName = data['names']
            namesForSection = data['sects']
            self._debForName = debForName
            self._namesForStemmedDescription = namesForStemmedDescription
            self._namesForStemmedName = namesForStemmedName
            self._namesForSection = namesForSection
            onReady(f'Read {len(self._debForName):,d} packages and indexes '
                    f'in {time.monotonic() - self.timer:0.1f}sec.', True)
            return True
        except (KeyError, pickle.PickleError, OSError) as err:
            print(f'Failed to write cache: {err}')
            self._deleteCache()
        return False


    def _saveToCache(self):
        data = dict(debs=self._debForName,
                    descs=self._namesForStemmedDescription,
                    names=self._namesForStemmedName,
                    sects=self._namesForSection)
        try:
            with open(self._cacheFilename(), 'wb') as file:
                pickle.dump(data, file, protocol=4)
        except (pickle.PickleError, OSError) as err:
            print(f'Failed to write cache: {err}')
            self._deleteCache()


    def _deleteCache(self):
        with contextlib.suppress(FileNotFoundError):
            os.remove(self._cacheFilename())


class _State:

    def __init__(self):
        self.inDescription = False
        self.inContinuation = False


def _genericSection(section):
    return section.split('/')[-1]


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
                not word.startswith('lib') and word not in _COMMON_STEMS]


_COMMON_STEMS = {
    'and', 'applic', 'bit', 'compil', 'data', 'debug', 'develop',
    'document', 'file', 'for', 'gnu', 'in', 'kernel', 'librari', 'linux',
    'modul', 'of', 'on', 'packag', 'runtim', 'support', 'the', 'to',
    'tool', 'version', 'with'}
