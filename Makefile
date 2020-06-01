build: cobib/
	python setup.py build

install_extras: _cobib cobib.1
	sudo install -dm 755 /usr/share/zsh/site-functions
	sudo install -m 644 _cobib /usr/share/zsh/site-functions/
	sudo install -dm 755 /usr/local/share/man/man1
	sudo install -m 644 cobib.1 /usr/local/share/man/man1/

install: install_extras
	sudo python setup.py install

lint: cobib/ test/
	pylint -rn cobib test --disable=fixme,duplicate-code

doc: cobib/ test/
	pydocstyle --convention=google --match=".*\.py" cobib test

spell: cobib/ test/
	pylint -rn cobib test --disable=all --enable=spelling \
	    --spelling-dict=en_US --spelling-private-dict-file=.pylintdict

.PHONY: test
test:
	python -m pytest test/
