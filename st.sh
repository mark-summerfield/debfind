tokei -s lines -f -t=Python -etest_*.py
unrecognized.py -q
flake . | \
    grep -v Model.py.*E127 | \
    grep -v test_Model.py.*F401.*Model.Deb.*unused
vulture --exclude ddebfind,gravitatewx . | \
    grep -v Model.py.*unused.*allSections | \
    grep -v Model.py.*unused.*dumpIndexes
git status
