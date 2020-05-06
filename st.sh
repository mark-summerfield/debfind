tokei -s lines -f -t=Python -etest_*.py -eIcons.py
unrecognized.py -q
flake . \
    | grep -v Model.py.*E127 \
    | grep -v test_Model.py.*F401.*Model.Deb.*unused
vulture --exclude ddebfind,gravitatewx . \
    | grep -v Model.py.*unused.*allSections \
    | grep -v Model.py.*unused.*dumpIndexes \
    | grep -v HelpForm.py.*Unused.attribute...i \
    | grep -v WindowActions.py.*Unused.attribute..Name \
    | grep -v WindowActions.py.*Unused.attribute..Version \
    | grep -v WindowActions.py.*Unused.attribute..Description \
    | grep -v WindowActions.py.*Unused.attribute..Copyright \
    | grep -v WindowActions.py.*Unused.attribute..WebSite \
    | grep -v Window.py.*Unused.class..Window \
    | grep -v Window.py.*Unused.attribute..Title \
    | grep -v Window.py.*Unused.attribute..MinSize \
    | grep -v Window.py.*Unused.attribute..Selection
git status
