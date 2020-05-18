#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import collections
import concurrent.futures
import contextlib
import datetime
import enum
import fnmatch
import glob
import os
import pickle
import sys
import tempfile
import time

import regex as re
import Stemmer


DATA_DIR = '/var/lib/apt/lists'
PACKAGE_PATTERN = '*Packages'
DESC_PATTERN = '*i18n_Translation-en'


Deb = collections.namedtuple(
    'Deb', ('name', 'version', 'section', 'desc', 'url', 'size'))


@enum.unique
class FutureKind(enum.Enum):
    DEBS = 0
    DESCS = 1


@enum.unique
class Match(enum.Enum):
    ALL_WORDS = 0
    ANY_WORD = 1

    def __str__(self):
        return self.name[:3].title()


class _Deb:

    def __init__(self):
        self.clear()


    @property
    def valid(self):
        return bool(self.name)


    def clear(self):
        self.name = ''
        self.version = ''
        self.section = ''
        self.desc = ''
        self.url = ''
        self.size = 0


    def update(self, key, value):
        if key == 'Package':
            self.name = value
            return False
        if key == 'Version':
            self.version = value
            return False
        if key == 'Section':
            self.section = _genericSection(value)
            return False
        if key == 'Description' or key == 'Npp-Description': # Ignore Npp?
            self.desc += value
            return True
        if key == 'Homepage':
            self.url = value
            return False
        if key == 'Installed-Size':
            self.size = int(value)
            return False
        return False


    @property
    def totuple(self):
        return Deb(self.name, self.version, self.section, self.desc,
                   self.url, self.size)


class Query:

    def __init__(self, *, section='', descWords='',
                 descMatch=Match.ALL_WORDS, nameWords='',
                 nameMatch=Match.ALL_WORDS, includeLibs=False,
                 includeDocs=False):
        self.section = _genericSection(section)
        self.descWords = descWords
        self.descMatch = descMatch
        self.nameWords = nameWords
        self.nameMatch = nameMatch
        self.includeLibs = includeLibs
        self.includeDocs = includeDocs


    def clear(self):
        self.section = ''
        self.descWords = ''
        self.descMatch = Match.ALL_WORDS
        self.nameWords = ''
        self.nameMatch = Match.ALL_WORDS
        self.includeLibs = False
        self.includeDocs = False


    def __str__(self):
        lib = ' Lib' if self.includeLibs else ''
        doc = ' Doc' if self.includeDocs else ''
        return (f'section={self.section} '
                f'desc={self.descWords!r}{self.descMatch} '
                f'name={self.nameWords!r}{self.nameMatch}{lib}{doc}')


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


    def descForName(self, name):
        deb = self._debForName.get(name)
        if deb is None:
            return ''
        return deb.desc


    def debForName(self, name):
        return self._debForName.get(name)


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
        if bool(query.descWords):
            constrainToDescription = True
            words = _stemmedWords(query.descWords)
            for word in words:
                names = self._namesForStemmedDescription.get(word)
                if names is not None:
                    haveDescription |= set(names)
            # haveDescription is names matching Any word
            # Only accept matching All (doesn't apply if only one word)
            if len(words) > 1 and query.descMatch is Match.ALL_WORDS:
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
            if len(words) > 1 and query.nameMatch is Match.ALL_WORDS:
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
        if query.includeLibs and query.includeDocs:
            return names
        filteredNames = set()
        for name in names:
            if (not query.includeLibs and
                    (('libre' not in name or name.startswith('lib')) and
                     '-lib' in name)):
                continue
            if not query.includeDocs and name.endswith(('-doc', '-docs')):
                continue
            filteredNames.add(name)
        return filteredNames


    def _readPackages(self, onReady):
        wrongCpu = 'i386' if sys.maxsize > 2 ** 32 else 'amd64'
        packageFilenames = []
        descFilenames = []
        for name in glob.iglob(f'{DATA_DIR}/*'):
            if wrongCpu not in name and fnmatch.fnmatch(name,
                                                        PACKAGE_PATTERN):
                packageFilenames.append(name)
            elif fnmatch.fnmatch(name, DESC_PATTERN):
                descFilenames.append(name)
        onReady('Reading Packages files…', False)
        descForName = {}
        allDebs = []
        try:
            with concurrent.futures.ProcessPoolExecutor() as executor:
                futures = set()
                for filename in packageFilenames:
                    futures.add(executor.submit(self._readPackageFile,
                                filename))
                for filename in descFilenames:
                    futures.add(executor.submit(self._readDescFile,
                                filename))
                for future in concurrent.futures.as_completed(futures):
                    kind, data = future.result()
                    if kind is FutureKind.DEBS:
                        allDebs += data
                    elif kind is FutureKind.DESCS:
                        descForName.update(data)
            seen = set()
            for deb in allDebs:
                if deb.name in seen:
                    continue # Some debs appear in > 1 Packages files
                seen.add(deb.name)
                desc = descForName.get(deb.name)
                if desc is not None:
                    deb = deb._replace(desc=desc)
                self._debForName[deb.name] = deb
            onReady(f'Read {len(self._debForName):,d} packages from '
                    f'{len(packageFilenames):,d} Packages files in '
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
                debs.append(deb.totuple)
        except OSError as err:
            print(err)
        return (FutureKind.DEBS, debs)


    def _readPackageLine(self, filename, lino, line, debs, deb, state):
        if not line.strip():
            if deb.valid:
                debs.append(deb.totuple)
            deb.clear()
            return
        if state.inDescription or state.inContinuation:
            if line.startswith((' ', '\t')):
                if state.inDescription:
                    deb.desc += line
                return
            state.inDescription = state.inContinuation = False
        key, value, ok = _maybeKeyValue(line)
        if not ok:
            state.inContinuation = True
        else:
            state.inDescription = deb.update(key, value)


    def _readDescFile(self, filename):
        descRx = re.compile(r'Description(:?-\w+)?:\s+')
        inList = False
        nameForDesc = {}
        name = None
        desc = []
        try:
            with open(filename, 'rt', encoding='utf-8') as file:
                for line in file:
                    if name is None:
                        if line.startswith('Package:'):
                            if name is not None:
                                if inList:
                                    inList = False
                                    desc.append('\v-')
                                nameForDesc[name] = ' '.join(desc).strip()
                                desc.clear()
                            name = line[8:].strip()
                    elif line.startswith('Description-md5'):
                        continue
                    else: # start of desc or in desc or end of desc
                        match = descRx.match(line)
                        if match is not None:
                            desc = [line[match.end():].strip(), '\n']
                        else:
                            line = line.rstrip()
                            if not line:
                                nameForDesc[name] = ' '.join(desc).strip()
                                name = None
                                desc.clear()
                            if line == ' .':
                                if inList:
                                    inList = False
                                    desc.append('\v-')
                                desc.append('\n')
                            elif line.lstrip().startswith(('* ', '- ')):
                                if not inList:
                                    desc.append('\v+')
                                    inList = True
                                desc.append(f'\t{line.lstrip()[2:]}')
                            else:
                                if inList:
                                    inList = False
                                    desc.append('\v-')
                                desc.append(line)
            if name is not None:
                if inList:
                    inList = False
                    desc.append('\v-')
                nameForDesc[name] = ''.join(desc).strip()
        except OSError as err:
            print(err)
        return (FutureKind.DESCS, nameForDesc)


    def _indexPackages(self, onReady):
        size = len(self._debForName)
        onReady(f'Indexing {size:,d} packages…', False)
        for name, deb in self._debForName.items():
            for word in _stemmedWords(name):
                self._namesForStemmedName.setdefault(word, set()).add(name)
                self._namesForStemmedDescription.setdefault(word,
                                                            set()).add(name)
            for word in _stemmedWords(deb.desc):
                self._namesForStemmedDescription.setdefault(word,
                                                            set()).add(name)
            self._namesForSection.setdefault(deb.section, set()).add(name)
        onReady(f'Read and indexed {size:,d} packages in '
                f'{time.monotonic() - self.timer:0.1f}sec.', True)


    @staticmethod
    def _cacheFilename():
        return (f'{tempfile.gettempdir()}/'
                f'debfind-{datetime.date.today()}.cache')


    def _loadFromCache(self, onReady):
        filename = self._cacheFilename()
        if not os.path.exists(filename):
            return False
        onReady(f'Reading cache…', False)
        try:
            with open(filename, 'rb') as file:
                data = pickle.load(file)
            self._debForName = data['debs']
            self._namesForStemmedDescription = data['descs']
            self._namesForStemmedName = data['names']
            self._namesForSection = data['sects']
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
                pickle.dump(data, file, 4)
        except (TypeError, OSError) as err:
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
    stemmer = Stemmer.Stemmer('en')
    return [word for word in stemmer.stemWords(
            nonLetterRx.sub(' ', line).casefold().split())
            if len(word) > 1 and not word.isdigit() and
                not word.startswith('lib') and word not in _COMMON_STEMS]


_COMMON_STEMS = {
    'and', 'applic', 'bit', 'compil', 'data', 'debug', 'develop',
    'document', 'file', 'for', 'gnu', 'in', 'kernel', 'librari', 'linux',
    'modul', 'of', 'on', 'packag', 'runtim', 'support', 'the', 'to',
    'tool', 'version', 'with'}
