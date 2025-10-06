cobib-plugin-dummy(7) -- dummy plugin for cobib(1)
==================================================

## SYNOPSIS

```
cobib dummy
cobib add --dummy
cobib export --dummy
cobib import --dummy
```

## DESCRIPTION

This plugin provides no actual features.
Its only purpose is to provide examples for how to add custom implementation of coBib various [entry-points](https://setuptools.pypa.io/en/latest/pkg_resources.html#entry-points) (see *cobib-plugins(7)*).
To see how the man-pages provided by this dummy plugin are registered, check out the `cobib_dummy` [plugin source code](https://gitlab.com/cobib/cobib/-/tree/master/plugin/).

## SEE ALSO

*cobib(1)*, *cobib-plugins(7)*

[//]: # ( vim: set ft=markdown tw=0: )
