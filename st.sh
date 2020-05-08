tokei -s lines -f -t=Python -etest_*.py -eIcons.py
unrecognized.py -q
flake . \
    | grep -v Model.py.*E127 \
    | grep -v test_Model.py.*F401.*Model.Deb.*unused
vulture --exclude ddebfind,gravitatewx . \
    | grep -v Model.py.*unused.*allSections \
    | grep -v Model.py.*unused.*dumpIndexes \
    | grep -v HelpForm.py.*[Uu]nused.attribute...i \
    | grep -v WindowActions.py.*[Uu]nused.attribute..Name \
    | grep -v WindowActions.py.*[Uu]nused.attribute..Version \
    | grep -v WindowActions.py.*[Uu]nused.attribute..Description \
    | grep -v WindowActions.py.*[Uu]nused.attribute..Copyright \
    | grep -v WindowActions.py.*[Uu]nused.attribute..WebSite \
    | grep -v Window.py.*[Uu]nused.class..Window \
    | grep -v Window.py.*[Uu]nused.attribute..Title \
    | grep -v Window.py.*[Uu]nused.attribute..MinSize \
    | grep -v Window.py.*[Uu]nused.attribute..Selection
git status
