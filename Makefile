PREFIX ?= /usr/local
BINDIR ?= $(DESTDIR)$(PREFIX)/bin
DOCDIR ?= $(DESTDIR)$(PREFIX)/share/doc/crema
CONFDIR ?= /home/$(USER)/.config/crema

.PHONY: all install uninstall

all:

install:
	sudo install -m755 -d $(BINDIR)
	sudo install -m755 -d $(DOCDIR)
	sudo install -m755 crema $(BINDIR)/crema
	sudo install -m644 README.md $(DOCDIR)
	install -m755 -o $(USER) -g $(USER) -d $(CONFDIR)
	install -m644 -o $(USER) -g $(USER) docs/default.ini $(CONFDIR)/config.ini

uninstall:
	sudo rm -f $(BINDIR)/crema
	sudo rm -rf $(DOCDIR)
