"""coBib's database module.

coBib uses a plain-test YAML file to store the bibliographic database.
This module contains the components which represent this database at runtime.

.. warning::

   If you feel like coBib spends an awful lot of time reading in your database, you can try to
   improve performance by _linting your database_. Running `cobib _lint_database` will print any
   logging messages that occur during the database parsing, indicating the coBib had to apply some
   changes manually at runtime (which will happen every time you need to read-in the database). You
   can automatically fix all these linting suggestions based on how coBib automatically treats the
   entries internally by adding the `--format` argument: `cobib _lint_database -f`.

.. note::

   As of version 4.4.0 coBib also has a primitive caching mechanism which will significantly improve
   the startup performance. You can configure the location of the cache via the
   `cobib.config.config.DatabaseConfig.cache` setting or disable it entirely by changing this
   setting to `None`.
   Note, that linting your database will still improve startup performance when your cache becomes
   outdated for any reason (for example manual editing of the database file or syncing it via the
   git integration).
"""

from .author import Author as Author
from .database import Database as Database
from .entry import Entry as Entry
