build: cobib/
	python setup.py build

install: build/
	sudo python setup.py install
	sudo install -dm 755 /usr/share/zsh/site-functions
	sudo install -m 644 cobib /usr/share/zsh/site-functions/

test: cobib/ test/
	python -m pytest test/

lint: cobib/ test/
	pylint -rn cobib test --disable=fixme

spell: cobib/ test/
	pylint -rn cobib test --disable=all --enable=spelling \
	    --spelling-dict=en_US --spelling-private-dict-file=.pylintdict
