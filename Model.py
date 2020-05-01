#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import collections
import concurrent.futures
import contextlib
import datetime
import enum
import glob
import os
import sys
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
        self._readPackages(onReady)
        self._indexPackages(onReady)


    @property
    def allSections(self):
        return self.namesForSection.keys()


    @property
    def allNames(self):
        return self.debForName.keys()


    def query(self, query):
        haveSection = set()
        haveDescription = set()
        haveName = set()
        constrainToSection = False
        constrainToDescription = False
        constrainToName = False
        if bool(query.section):
            constrainToSection = True
            haveSection = self.namesForSection.get(query.section)
        if bool(query.descriptionWords):
            constrainToDescription = True
            words = _stemmedWords(query.descriptionWords)
            for word in words:
                names = self.namesForStemmedDescription.get(word)
                if names is not None:
                    haveDescription |= set(names)
            # haveDescription is names matching Any word
            # Only accept matching All (doesn't apply if only one word)
            if len(words) > 1 and not query.matchAnyDescriptionWord:
                for word in words:
                    names = self.namesForStemmedDescription.get(word)
                    if names is not None:
                        haveDescription &= set(names)
        if bool(query.nameWords):
            constrainToName = True
            words = _stemmedWords(query.nameWords)
            for word in words:
                names = self.namesForStemmedName.get(word)
                if names is not None:
                    haveName |= set(names)
            # haveName is names matching Any word
            # Only accept matching All (doesn't apply if only one word)
            if len(words) > 1 and not query.matchAnyNameWord:
                for word in words:
                    names = self.namesForStemmedName.get(word)
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
                    not '-lib' in name):
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
    'modul', 'of', 'on', 'packag', 'runtim', 'support', 'the', 'to',
    'tool', 'version', 'with'}


def _genericSection(section):
    return section.split('/')[-1]


if __name__ == '__main__':
    import sys


    def onReady(message, done):
        print(message)
        if done:
            print('Ready.')


    def dumpIndexes(model):
        with open('allnames.txt', 'wt', encoding='utf-8') as file:
            for name in sorted(model.allNames):
                print(name, file=file)
        with open('stemmednames.txt', 'wt', encoding='utf-8') as file:
            for name, words in sorted(model.namesForStemmedName.items()):
                print(name, ', '.join(sorted(words)), file=file)
        with open('stemmeddescs.txt', 'wt', encoding='utf-8') as file:
            for name, words in sorted(
                    model.namesForStemmedDescription.items()):
                print(name, ', '.join(sorted(words)), file=file)
        with open('sections.txt', 'wt', encoding='utf-8') as file:
            for name, words in sorted(model.namesForSection.items()):
                print(name, ', '.join(sorted(words)), file=file)
        print('dumped indexes')
        sys.exit()


    def check(id, query, names, mustInclude=None, minimum=-1,
              maximum=sys.maxsize):
        print(f'{id:2d} "{query}" ', end='')
        if minimum == -1:
            minimum = len(mustInclude) if mustInclude is not None else 1
        assert minimum <= len(names) <= maximum, \
               f'wrong length ({len(names)})'
        if mustInclude is not None:
            assert (names & mustInclude) == mustInclude, \
                   'wrong/missing name(s)'
        print(f'{len(names):,d} OK')

    print('Model tests')
    model = Model(onReady)
    # dumpIndexes(model) # doesn't return

    query = Query()

    query.clear()
    query.descriptionWords = "haskell numbers"
    query.includeLibraries = True
    names = model.query(query) # All
    check(1, query, names, {'libghc-random-dev'}, 2);

    query.clear()
    query.descriptionWords = 'haskell numbers'
    query.matchAnyDescriptionWord = True
    query.includeLibraries = True
    names = model.query(query) # Any
    check(2, query, names, {'libghc-random-dev', 'haskell-doc',
                            'libghc-strict-dev'}, 800)

    query.clear()
    query.descriptionWords = 'haskell daemon'
    names = model.query(query) # All
    check(3, query, names, {'hdevtools'}, 1, 1)

    query.clear()
    query.descriptionWords = 'haskell daemon'
    query.matchAnyDescriptionWord = True
    query.includeLibraries = True
    names = model.query(query) # Any
    check(4, query, names, {'libghc-random-dev', 'haskell-doc',
                            'libghc-strict-dev'}, 1000)

    query.clear()
    query.nameWords = 'python3'
    names = model.query(query) # All
    check(5, query, names, {'python3'}, 6000)
    n = len(names)

    query.clear()
    query.nameWords = 'python'
    names = model.query(query) # All
    check(6, query, names, {'python'}, n, n)

    query.clear()
    query.nameWords = 'python3 django'
    names = model.query(query) # All
    check(7, query, names, {
        'python3-django-x509', 'python3-django',
        'python3-django-captcha', 'python3-django-compressor',
        'python3-django-environ', 'python3-django-imagekit',
        'python3-django-memoize', 'python3-django-rules',
        'python3-django-uwsgi', 'python3-django-xmlrpc',
        'python3-pylint-django', 'python3-pytest-django'}, 100)
    n = len(names)

    query.clear()
    query.nameWords = 'python django'
    names = model.query(query) # All
    check(8, query, names, {
        'python3-django-x509', 'python3-django',
        'python3-django-captcha', 'python3-django-compressor',
        'python3-django-environ', 'python3-django-imagekit',
        'python3-django-memoize', 'python3-django-rules',
        'python3-django-uwsgi', 'python3-django-xmlrpc',
        'python3-pylint-django', 'python3-pytest-django'}, n)

    query.clear()
    query.nameWords = 'python3 django memoize'
    names = model.query(query) # All
    check(9, query, names, {'python3-django-memoize'}, 1, 5);
    n = len(names)

    query.clear()
    query.nameWords = 'python django memoize'
    names = model.query(query) # All
    check(10, query, names, {'python3-django-memoize'}, n, n);

    query.clear()
    query.nameWords = 'python django memoize'
    query.matchAnyNameWord = True
    names = model.query(query) # Any
    check(11, query, names, {
        'python-django-app-plugins', 'python3-affine', 'python3-distro',
        'python3-distutils', 'python3-gdbm', 'python3-pyx',
        'python3-requests-mock', 'python3-sparse', 'python3-yaml',
        'python3-django-memoize'}, 250)

    query.clear()
    query.section = 'vcs'
    names = model.query(query)
    check(12, query, names, {'git'}, 2);

    query.clear()
    query.section = 'math'
    names = model.query(query)
    check(13, query, names, {'bc', 'dc', 'lp-solve'})

    query.clear()
    query.section = 'math'
    query.includeLibraries = True
    names = model.query(query)
    check(14, query, names, {'bc', 'dc', 'lp-solve'}, 3)

    query.clear()
    query.section = 'python'
    query.includeLibraries = True
    names = model.query(query)
    check(15, query, names, {'libpython-dev'}, 500)

    query.clear()
    query.section = 'python'
    names = model.query(query) # All
    check(16, query, names, {'python3'}, 200)

    query.clear()
    query.section = 'python'
    query.nameWords = 'django'
    names = model.query(query) # All
    check(17, query, names, {'python3-django'}, 5)

    query.clear()
    query.section = 'python'
    query.nameWords = 'django memoize'
    names = model.query(query) # All
    check(18, query, names, {'python-django-memoize',
                             'python3-django-memoize'}, 1, 5)

    query.clear()
    query.section = 'python'
    query.nameWords = 'django memoize'
    query.matchAnyNameWord = True
    names = model.query(query) # Any
    check(19, query, names, {
        'python-django-appconf', 'python3-django', 'python-django-common',
        'python-django', 'python-django-openstack-auth',
        'python-django-compressor', 'python3-django-piston3',
        'python-django-pyscss', 'python3-django-maas'})

    query.clear()
    query.nameWords = 'memoize'
    names = model.query(query) # All
    check(20, query, names, minimum=5)

    query.clear()
    query.nameWords = 'memoize python3'
    names = model.query(query) # All
    check(21, query, names)

    query.clear()
    query.nameWords = 'memoize python3 django'
    names = model.query(query) # All
    check(22, query, names)

    query.clear()
    query.nameWords = 'python3 django'
    query.matchAnyNameWord = True
    names = model.query(query) # Any
    check(23, query, names, minimum=2_500)

    query.clear()
    query.nameWords = 'zzzzzz'
    names = model.query(query) # All
    check(24, query, names, minimum=0, maximum=0)
