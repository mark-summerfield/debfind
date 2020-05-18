#!/usr/bin/env python3
# Copyright © 2020 Qtrac Ltd. All rights reserved.

import sys

import Model
from Model import Deb # Needed for reading pickle


def main():
    if len(sys.argv) > 1 and sys.argv[1] in {'-h', '--help'}:
        raise SystemExit('usage: test_Model.py [-d|--dump]')

    model = Model.Model(onReady)

    if len(sys.argv) > 1 and sys.argv[1] in {'-d', '--dump'}:
        dumpIndexes(model)
        return

    print('Model tests')
    query = Model.Query() # Default is Match.ALL_WORDS for name & desc.

    query.clear()
    query.descWords = "haskell numbers"
    query.includeLibs = True
    names = model.query(query) # All
    check(1, query, names, {'libghc-random-dev'}, 2)

    query.clear()
    query.descWords = 'haskell numbers'
    query.descMatch = Model.Match.ANY_WORD
    query.includeLibs = True
    query.includeDocs = True
    names = model.query(query) # Any
    check(2, query, names, {'libghc-random-dev', 'haskell-doc',
                            'libghc-strict-dev'}, 800)

    query.clear()
    query.descWords = 'haskell daemon'
    names = model.query(query) # All
    check(3, query, names, {'hdevtools'}, 1, 1)

    query.clear()
    query.descWords = 'haskell daemon'
    query.descMatch = Model.Match.ANY_WORD
    query.includeLibs = True
    query.includeDocs = True
    names = model.query(query) # Any
    check(4, query, names, {'libghc-random-dev', 'haskell-doc',
                            'libghc-strict-dev'}, 1_000)

    query.clear()
    query.nameWords = 'python3'
    names = model.query(query) # All
    check(5, query, names, {'python3'}, 5_000)
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
    check(9, query, names, {'python3-django-memoize'}, 1, 5)
    n = len(names)

    query.clear()
    query.nameWords = 'python django memoize'
    names = model.query(query) # All
    check(10, query, names, {'python3-django-memoize'}, n, n)

    query.clear()
    query.nameWords = 'python django memoize'
    query.nameMatch = Model.Match.ANY_WORD
    names = model.query(query) # Any
    check(11, query, names, {
        'python-django-app-plugins', 'python3-affine', 'python3-distro',
        'python3-distutils', 'python3-gdbm', 'python3-pyx',
        'python3-requests-mock', 'python3-sparse', 'python3-yaml',
        'python3-django-memoize'}, 250)

    query.clear()
    query.section = 'vcs'
    names = model.query(query)
    check(12, query, names, {'git'}, 2)

    query.clear()
    query.section = 'math'
    names = model.query(query)
    check(13, query, names, {'bc', 'dc', 'lp-solve'})

    query.clear()
    query.section = 'math'
    query.includeLibs = True
    names = model.query(query)
    check(14, query, names, {'bc', 'dc', 'lp-solve'}, 3)

    query.clear()
    query.section = 'python'
    query.includeLibs = True
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
    query.nameMatch = Model.Match.ANY_WORD
    names = model.query(query) # Any
    check(19, query, names, {
        'python-django-appconf', 'python3-django', 'python-django-common',
        'python-django', 'python-django-openstack-auth',
        'python-django-compressor', 'python3-django-piston3',
        'python-django-pyscss', 'python3-django-maas'})

    query.clear()
    query.nameWords = 'memoize'
    names = model.query(query) # Any
    check(20, query, names, minimum=5)

    query.clear()
    query.nameWords = 'memoize python3'
    names = model.query(query) # Any
    check(21, query, names)

    query.clear()
    query.nameWords = 'memoize python3 django'
    names = model.query(query) # Any
    check(22, query, names)

    query.clear()
    query.nameWords = 'python django'
    query.nameMatch = Model.Match.ANY_WORD
    names = model.query(query) # Any
    check(23, query, names, minimum=5_000)

    query.clear()
    query.nameWords = 'python django'
    names = model.query(query) # All
    check(24, query, names, minimum=200)

    query.clear()
    query.nameWords = 'zzzzzz'
    names = model.query(query) # Any
    check(25, query, names, minimum=0, maximum=0)


def onReady(message, done):
    print(message)
    if done:
        print('Ready.')


def dumpIndexes(model):
    with open('allnames.txt', 'wt', encoding='utf-8') as file:
        for name in sorted(model.allNames):
            print(name, file=file)
    with open('stemmednames.txt', 'wt', encoding='utf-8') as file:
        for name, words in sorted(model._namesForStemmedName.items()):
            print(name, ', '.join(sorted(words)), file=file)
    with open('stemmeddescs.txt', 'wt', encoding='utf-8') as file:
        for name, words in sorted(
                model._namesForStemmedDescription.items()):
            print(name, ', '.join(sorted(words)), file=file)
    with open('sections.txt', 'wt', encoding='utf-8') as file:
        for name, words in sorted(model._namesForSection.items()):
            print(name, ', '.join(sorted(words)), file=file)
    print('Dumped indexes.')


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


if __name__ == '__main__':
    main()
