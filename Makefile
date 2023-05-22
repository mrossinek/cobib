prefix?=/usr

install_extras: cobib.1
	install -Dm644 cobib.1 $(DESTDIR)$(prefix)/share/man/man1/cobib.1
