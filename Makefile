prefix?=/usr

install_extras: _cobib cobib.1
	install -Dm644 _cobib $(DESTDIR)$(prefix)/share/zsh/site-functions/_cobib
	install -Dm644 cobib.1 $(DESTDIR)$(prefix)/share/man/man1/cobib.1
