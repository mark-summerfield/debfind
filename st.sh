tokei -s lines -f -t=Python
unrecognized.py -q
flake . | grep -v Model.*E127
vulture --exclude ddebfind,gravitatewx . | \
    grep -v Model.py.*unused.*allSections | \
    grep -v Model.py.*unused.*dumpIndexes
git status
