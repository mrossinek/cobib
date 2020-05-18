build: cobib/
	python setup.py build

install: build/
	sudo python setup.py install
	sudo install -dm 755 /usr/share/zsh/site-functions
	sudo install -m 644 _cobib /usr/share/zsh/site-functions/
	sudo install -m 644 cobib.1 /usr/local/share/man/man1/

lint: cobib/ test/
	pylint -rn cobib test --disable=fixme,duplicate-code

spell: cobib/ test/
	pylint -rn cobib test --disable=all --enable=spelling \
	    --spelling-dict=en_US --spelling-private-dict-file=.pylintdict

.PHONY: test
test:
	python -m pytest test/
