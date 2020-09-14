prefix?=/usr

build: cobib/
	python3 setup.py build

install_extras: _cobib cobib.1
	install -Dm644 _cobib $(DESTDIR)$(prefix)/share/zsh/site-functions/_cobib
	install -Dm644 cobib.1 $(DESTDIR)$(prefix)/share/man/man1/cobib.1

install: install_extras
	python3 setup.py install

.PHONY: dev
dev:
	pip3 install pylint pydocstyle pyenchant pyte

lint: cobib/ test/
	pylint -rn cobib test --disable=fixme,duplicate-code

doc: cobib/ test/
	pydocstyle --convention=google --match=".*\.py" cobib test

spell: cobib/ test/
	pylint -rn cobib test --disable=all --enable=spelling \
	    --spelling-dict=en_US --spelling-private-dict-file=.pylintdict

.PHONY: test
test:
	python3 -m pytest test/
