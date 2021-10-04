"""coBib's configuration module.

The configuration has undergone a major revision during v3.0 when it was redesigned from loading a
`INI` file with the `configparser` module to become a standalone Python object.
The configuration will be read from the file that appears first in the following list:

1. a file pointed to by the `--config` command-line option.
2. the XDG-default location: `~/.config/cobib/config.py`.
3. the *legacy* XDG-default location: `~/.config/cobib/config.ini`. This option will be removed on
   January 1st, 2022.
4. if none of the above are found, coBib will fallback to the default configuration.

A configuration file is *not* required to set all attributes itself.
In fact, it is required to import the default configuration first and then simply overwrite any
settings to the user's liking.

```python
from cobib.config import config
```

For more information take a look at the example configuration, `cobib.config.example`.
"""

from .config import LabelSuffix as LabelSuffix
from .config import config as config
from .event import Event as Event
