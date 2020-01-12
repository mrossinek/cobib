build: cobib
	python setup.py build

install: build
	sudo python setup.py install
	sudo install -dm 755 /usr/share/zsh/site-functions
	sudo install -m 644 cobib /usr/share/zsh/site-functions/

