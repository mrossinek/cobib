build: crema
	python setup.py build

install: build
	sudo python setup.py install
	sudo install -dm 755 /usr/share/zsh/site-functions
	sudo install -m 644 _crema /usr/share/zsh/site-functions/

