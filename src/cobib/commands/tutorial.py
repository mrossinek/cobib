"""coBib's guided tutorial.

.. include:: ../man/cobib-tutorial.1.html_fragment
"""

from __future__ import annotations

import argparse
import logging
import tempfile
from enum import Enum, unique
from pathlib import Path
from shutil import rmtree
from textwrap import dedent
from typing import TYPE_CHECKING

from rich.markdown import Markdown
from typing_extensions import override

from cobib.config import Event, config
from cobib.man import TUTORIAL_ADD_ENTRY, TUTORIAL_ADD_FILE, TUTORIAL_IMPORT_DATABASE
from cobib.utils.console import PromptConsole

from .base_command import Command

if TYPE_CHECKING:
    from cobib.ui import Shell

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class TutorialCommand(Command):
    """The tutorial Command.

    This command can not parse any arguments.
    """

    name = "tutorial"

    TEMP_DIR = Path(tempfile.gettempdir()).resolve()
    """The temporary directory in which to store the tutorial's database."""

    @unique
    class State(Enum):
        """The enumerated states that the tutorial runs through.

        These states will be iterated in order of definition. Each named state contains the
        instructions that will be printed for the user as its value. These will be rendered as
        `rich.markdown.Markdown` in the shell.

        .. note::
           If you happen to be reading this documentation in its HTML format, you can find a preview
           of all the tutorial's instructions below.
        """

        INIT = """
        # coBib's Tutorial

        **Welcome** to this interactive, guided tutorial on how to get started with _coBib - the
        console bibliography_!

        Before diving right in, please acknowledge the following:

        - This tutorial uses a custom configuration and database which are isolated from your own.
        - Therefore, you can work through this tutorial without overwriting any of your own data.
        - However, it does not check your progress and is not programmed to handle any errors.
        - Thus, please follow the instructions **carefully** to ensure a successful completion.
        - If you do encounter any issues or have feedback of any kind, please reach out by
          [opening an issue](https://gitlab.com/cobib/cobib/-/issues/new).

        ---

        Before doing anything else, you will need to initialize the database.
        By design, coBib uses a centralized database (meaning a single file) and it can optionally
        integrate with `git` to track the changes you make over time.
        This version control integration is **not** enabled by default, but in this tutorial we have
        overwritten the `cobib.config.database.git` setting to enable it.

        > Covering coBib's many configuration options is beyond the scope of this tutorial.
        > Let it just be said that you configure coBib directly using Python.
        >
        > To get started, you can generate an example configuration file with all the default
        > settings and extensive explanatory comments directly from the terminal like so:
        >
        >   ```bash
        >   $ cobib _example_config > ~/.config/cobib/config.py
        >   ```

        ## The Shell

        Returning to this tutorial, it is almost time to initialize the database.
        But before, we have one more explanation to cover: coBib's interactive shell.
        You may have already noticed that the prompt below has changed to look like so (where █
        indicates the position of your cursor):
        ```
        > █
        ```
        This is the prompt of coBib's interactive shell.
        While you are in this shell, you can execute consecutive coBib commands without dropping
        down to the terminal prompt.

        > If you want to make your life a little bit simpler, install the optional dependency
        > `prompt_toolkit`, as it will allow you to recall previous commands in the shell via the
        > up/down arrow keys.

        Using the shell has several benefits, such as keeping your database and configuration in
        memory without having to re-parse them.
        Thus, you may also find it useful outside the scope of this tutorial.
        When that is the case, you can start an interactive shell with your own database and
        configuration like so:
        ```bash
        $ cobib --shell
        ```
        > Whenever we show a command to be executed you can tell if it is meant for a terminal
        > prompt by the `$` prefix. All other commands in this tutorial are meant for coBib's
        > interactive shell and use the `>` prefix.

        # Scroll up to ensure you don't miss any instructions because they can get very long!

        ## Initializing the database

        Finally, it is time to get started and initialize a new database.
        To do so, simply execute the following command:
        ```
        > init --git
        ```
        """
        POST_INIT = """
        Congratulations! The output above should indicate the successful creation of a new git
        repository to track the history of your coBib database!

        > If you encountered an error above, make sure that `git` is set up properly on your device;
        > see the [git docs](https://git-scm.com/book/en/v2/Getting-Started-First-Time-Git-Setup).

        ## Growing your database

        ### Importing entries

        The database is still empty at this point, so to get started you will simply import some
        entries from a BibLaTeX file.
        This is done using the `import` command which provides backends for different sources.
        The BibLaTeX backend is built right into coBib but you can add more backends by installing
        plugins.

        You can check which backends are available in your installation using the following:
        ```
        > import --help
        ```
        """
        IMPORT = f"""
        In general, every command of coBib provides a `--help` summary like the one shown above.
        Note also the references to relevant man-pages at the bottom of the output: these refer to
        coBib's builtin manual which you will learn more about at the end of this tutorial.

        > Throughout this tutorial, please only inspect the help when the tutorial explicitly tells
        > you to do so, because the instructions may otherwise get out of sync with your tasks.

        ---

        For the purposes of this tutorial, coBib includes a BibLaTeX file whose entries you will now
        import. The path to this file will depend on your installation of coBib, so please ensure to
        specify it correctly below (you may copy & paste it for simplicity):
        ```
        > import --bibtex {TUTORIAL_IMPORT_DATABASE}
        ```
        """
        ADD = f"""
        ### Adding entries

        While on the topic of inserting entries into your database, we should address the difference
        between the `import` and `add` commands:
        - The `import` command is meant for addition of many entries at once in bulk.
          Minimal processing is performed on those entries and coBib will _only_ ensure that the
          database does not end up with multiple entries using the same _label_.
        - The `add` command is more for day-to-day operations of inserting entries a few at a time.
          It provides more parsers to add entries from different sources, allows manual insertion of
          entries, and even prompts you how to deal with a conflict when two entries try to use the
          same _label_.

        To provide a quick example of this behavior, you will now add a single entry from another
        BibLaTeX file, but deliberately set its `label` to overlap with an alrerady existing one.

        We will use this opportunity to associate a file with this entry. As one would expect from a
        reference manager such as coBib, it not only helps with managing BibLaTeX entries, but also
        their associated files such as PDFs and other attachments. As mentioned earlier though,
        coBib was designed to have a single, centralized database that can be version controlled.
        Consequently one might ask: how do attachments fit it into this model? Well, it is quite
        simple actually: the database does not track attached files themselves, but only keeps a
        reference to their location in the filesystem. After all, adding PDF files (the most common
        attachment) to version control would hardly make any sense. A benefit of this is that you
        can organize your attachments in any way you like, since coBib does not constrain you to a
        particular directory structure.

        > coBib makes no assumptions about the type or number of files associated with an entry.

        #### Label Disambiguation

        One final note: since an entry with the same label already exists in your database, this
        next step will trigger a *disambiguation* process. This results in an interactive prompt to
        which you must reply with one of the options:
        - `keep`: leaves the existing entry (left) unchanged
        - `replace`: replaces the entire existing entry (left) with the new one (right)
        - `update`: merges the changes of the new entry (right) into the existing one (left)
        - `cancel`: cancels the entire addition process
        - `disambiguate`: adds the new entry under a slightly modified label to disambiguate it from
          the existing one

        In this case, you should answer the prompt with `update`. So let's go ahead and add that
        entry to our database, while also attaching a file to it. Here, we simply add some `.txt`
        file with some key points of that article (since coBib does not ship with its PDF):
        ```
        > add --label Van_Noorden_2014 --bibtex {TUTORIAL_ADD_ENTRY} --file {TUTORIAL_ADD_FILE}
        ```
        """
        LIST = """
        ## Inspecting your database contents

        ### Listing entries

        Phew, that was quite a lot to take in already.
        Let's take a breather and inspect our database, by listing its contents:
        ```
        > list
        ```
        """
        FILTER_POSITIVE = r"""
        This is a good moment to briefly explain what entries we are working with in this tutorial.
        There are 11 entries:
        - `Van_Noorden_2014` is a Nature article from 2014 that explores the 100 most-cited research
          papers of all time.
        - The remaining 10 entries are the top 10 from that list.

        ### Filtering entries

        The `list` command is actually a lot more powerful than this first example leads to suggest,
        because it provides coBib's extensive *filtering* mechanism.

        Basically, you can filter the list of entries to display based on any field that ever occurs
        in your database; common examples include `year`, `author`, `journal`, `label`, etc.

        Let's use an example to explain this in more detail. Say, we want to list all entries that
        were published in the 1970s. We can achieve that very easily like so:
        ```
        > list ++year "197\d"
        ```
        """
        FILTER_NEGATIVE = r"""
        That was easy! Notice how the output automatically includes the `year` column which we
        included in our filter.

        > By default, the `list` command only shows the `label` and `title` columns. But you can
        > configure this to your liking via `cobib.config.commands.list_.default_columns`.

        Let's disect what is going on here:
        - `++year` is filtering the database to only show entries whose `year` field matches the
          value we specify
        - the `++` suffix indicates that we want a **positive** match
        - we match against a value of `"197\d"` which is a simple regex pattern to represent any of
          the numbers `1970` to `1979`

        Notice how we said `++year` is a _positive_ match? That can only mean we can also perform
        **negative** matching! And as one might expect, that is achieved using `--year`, like so:
        ```
        > list --year "197\d"
        ```
        """
        MORE_FILTERTING = r"""
        There are many more features to the filtering mechanism but rather than give an example for
        each and every one, we will list the most important ones below:
        - You can combine as many filters as you like, positive or negative alike.
        - When doing so, they will be combined using logical `AND`s. You can change this to `OR`s by
          adding the `--or` argument.
        - You can limit the number of entries to list using `--limit 10`.
        - You can sort the output by a given field using `--sort year`.
        - You can reverse the output order using `--reverse`.
        - And you can make your life easier by using:
          - `--ignore-case` to treat all characters as lowercase
          - `--decode-latex` to convert simple LaTeX sequences to Unicode characters
          - `--decode-unicode` to approximate Unicode characters with their closest ASCII one
        - And if you install the optional `regex` dependency, you can even perform basic **fuzzy**
          matching to guard against typos or other minor deviations from your filter query.

        To wrap up this introduction on filtering, it is best to explain one more special entry
        field: `tags`. As you learned earlier, coBib does not enforce a certain directory structure
        or other requirements for managing file attachments and it also stores all entries in a
        single database. Consequently, coBib does not order your entries into _directories_ like
        some other reference managers might. But this is by design, since coBib relies on `tags` to
        add structure to your database. This is a lot more powerful because it is more free-form and
        also allows entries (and by extension their attachments) to be tagged multiple times,
        something that is not possible when constrained to placing a file in one specific directory.

        In the database that you imported for this tutorial we already included a tag on each entry
        indicating the number of citations it has received at the time when `Van_Noorden_2014` was
        published.

        > This is obviously a contrived example of a `tag` since this information will become
        > outdated over time, but it serves the purposes of this tutorial very well.
        > More common examples of tags are for example `new` for newly added entries, priority
        > indicators such as `high` or `low`, and whatever else suits your workflow and needs.

        Let's run one last example by listing the top-5 most cited papers:
        ```
        > list ++tags citations --sort tags --reverse --limit 5
        ```
        """
        SEARCH = r"""
        ### Searching through the database

        Sometimes, filtering can only get you so far. That is one reason why coBib also allows you
        to search through your database without being restricted to the structure of the entries.

        Furthermore, the `search` command will also show results for any file attachments provided
        that the configured `cobib.config.commands.search.grep` tool supports their respective file
        types.

        > For plain-text files (like the `.txt` file we added to the `Van_Noorden_2014` entry
        > earlier in this tutorial), the default `grep` tool will work just fine. But if you want to
        > support searching through PDF files, consider installing and configuring a variant like
        > [ripgrep-all](https://github.com/phiresky/ripgrep-all).

        Much like the filtering mechanism, the `search` command provides features such as:
        - ignoring the lower/upper case spelling (`--ignore-case`)
        - converting simple LaTeX sequences to Unicode characters (`--decode-latex`)
        - approximating Unicode characters with their closest ASCII ones (`--decode-unicode`)
        - basic fuzzy matching (when the optional `regex` dependency is installed)
        - and of course, the search terms can be regex patterns themselves

        Finally, just like with `grep`, you can configure the amount of _context_ to provide for
        search results using the `--context` flag. You can see this in action with the following
        search for the term `biological`:
        ```
        > search --ignore-case --context 3 "biological"
        ```
        """
        SHOW = """
        ## Interacting with entries

        ### Showing entries

        Both the `list` and `search` commands have always only presented partial views of matching
        entries in the database. But of course, from time to time it is important to actually view
        one entry in its full.

        This is done quite simply using the `show` command and specifying the `label` of the entry:
        ```
        > show Van_Noorden_2014
        ```
        """
        OPEN = """
        ### Opening attachments

        As already discussed, you can manage attached files of your entries. Of course, coBib also
        provides a command to quickly `open` them. In fact, when opening an entry, several fields
        are checked for objects that can be opened. You will see this in action now, when opening
        the `Van_Noorden_2014` entry. It has both a `file` and `url` field that can be opened and
        you are prompted to select which one(s) to open.

        You can try this out and select any of the given options:
        ```
        > open Van_Noorden_2014
        ```
        """
        NOTE = """
        ### Taking notes

        While file attachments are great due to their flexibility, this also poses some limitations
        for how well entries can be discovered through `search` (because especially binary files
        like PDFs can only be included in the search with specialized tools).
        To overcome this, one could add plain-text comments to the entries directly, but this can
        quickly clutter up the database and displaying of entries using `show` (and it can impact
        the quality of `export` which we will get to later).

        Thus, coBib provides another solution: the `note` command. In essence, every entry is
        associated with exactly one `note` file. This has the following characteristics:
        - its name is derived from the entry's `label`
        - it is included in the version control of the database's history (when enabled)
        - it is a plain-text file whose contents are included natively during `search`

        Being plain-text files, you have full freedom over how to structure your notes, and you can
        even configure the `cobib.config.commands.note.default_filetype` to something other than the
        default `txt` to leverage capabilities of your text editor (for example you can use `md` for
        markdown formatting which many editors render more nicely).

        You can try out taking some notes for an entry of your choice. This will open the note file
        in your configured `$EDITOR` so be sure to save and close the file again before continuing:
        ```
        > note Van_Noorden_2014
        ```
        """
        DELETE = """
        ## Changing your database contents

        Now we will cover commands which change the contents of your database.

        ### Deleting entries

        The most straight forward operation is to `delete` an entry from your database.
        By default, this will also delete any attached files, so use this with care!

        ```
        > delete Thompson_1994
        ```
        """
        EDIT = """
        ### Editing entries

        Of course, one also has to be able to `edit` an entry.
        When doing this, the entry's contents are presented in coBib's YAML format rather than in
        BibLaTeX form, but you can obviously still use common LaTeX typesetting in the entry's data
        whenever necessary.

        In general, the YAML format is a bit nicer to work with. For example, take a look at the
        `author` field in a moment and notice that coBib nicely separates all authors into list
        items, with their first and last names stored separately. Additionally, coBib automatically
        converts author names to proper Unicode representation rather than rely on the "clunky"
        LaTeX sequences to encode special characters. This makes matching against or searching for
        authors by name much easier.

        Let's go ahead and edit some entry of the database. Feel free to perform any changes or
        simply quit the editor without making any changes:
        ```
        > edit Lee_1988
        ```
        """
        MODIFY_1 = """
        ### Modifying entries

        Sometimes, the manual editing process can become cumbersome, especially when performing only
        simple, repetitive edits over many different entries. That is what the `modify` command
        tries to solve, by providing a powerful bulk editing mechanism.

        To really show what this command is capable of, we will address an issue you may have
        already noticed: the typesetting of the author names is not consistent as many names are
        written with all capital letters while others are not. This is a perfect usecase for the
        `modify` command as it allows us to automate the replacement using Python!

        First, let us understand how the `modify` command works. We can get a first impression from
        its `--help` summary:
        ```
        > modify --help
        ```
        """
        MODIFY_2 = """
        As we can see, there are two positional arguments: `modification` and `filter`.

        Let us first consider the latter. You already learned about the filtering mechanism provided
        by the `list` command. Here, you can repurpose that same mechanism to _select_ which entries
        of your database will get modified! For the example at hand, we actually want to apply the
        modification to _all_ entries in our database, so we do not need to specify a filter.

        Okay, let us now design our `modification` argument. As explained in the `--help` summary,
        this argument should be structured like so: `<field>:<value>`. Here, we want to modify the
        `author` field, so the first part is simple: `author:<value>`. Now, what about the `value`
        that we want to insert?

        This is where the `modify` command leverages Python's powerful
        [f-strings](https://docs.python.org/3/reference/lexical_analysis.html#f-strings):
        we can provide a `value` that gets evaluated as a formatted string using all of the current
        entry's fields as local variables!

        Okay, let's actually write out our example:
        ```
        {' and '.join([' '.join(n.title() for n in str(name).split()) for name in author])}
        ```

        Wow! There is a lot going on here... so let's dissect it:
        - `{...}`: These outer most curly parentheses delimit the f-string's replacement field. In
          other words, the entire value will be replaced by what the inner expression evaluates to.
        - `' and '.join([... for name in author])`: As you learned earlier, coBib stores the
          `author` field as a list. So here, we are iterating over each `name` in that list and join
          them together using the string `' and '` (the standard BibLaTeX way of joining multiple
          authors, which coBib understands how to parse again).
        - `' '.join(n.title() for n in str(name).split())`: this is the inner-most part.
          Here, we take the current author's `name` convert it to a string and split it into
          fragments. Over these, we iterate and title-case them (i.e. ensure that only the first
          character is upper-cased), and finally we join the name back together to a single string.

        That was a lot to take in. Let's test whether all this works with a dry-run:
        ```
        > modify --dry "author:{' and '.join([' '.join(n.title() for n in str(name).split()) for name in author])}"
        ```
        """  # noqa: E501
        REVIEW = """
        Cool, that works as expected! However, we can see that there is another problem with the
        `Lowry_1951` entry, where the initial of the secondary name appears to not be separated
        correctly from the first name. Applying this modification would make spotting that error
        more difficult, so it is good that we only ran the command in `--dry` mode!

        We will learn about an alternative solution to our problem in a second, but hopefully this
        gave you a good idea of how powerful the `modify` command can be!
        If you remember to use the `--dry` mode, you can check and adjust your modifications before
        applying the changes to your database.
        And if you make a mistake, even that can be corrected due to the integrated version control!

        ### Reviewing entries

        Okay, now let's learn about that alternative solution: the `review` command.
        As the name suggests you can use this command to review - that is, manually inspect - the
        entries in your database one at a time.

        While simply executing the `review` command without any further arguments will iterate over
        your entire database, that can quite quickly become too much information to process, which
        is why the `review` command provides some clever mechanics to narrow down the scope to be
        more manageable.

        - just like the `modify` command, you can _filter_ the entries to be reviewed
        - additionally, you can select specific _fields_ to focus on

        With that dialed in, the `review` command will iterate over each entry in your database
        matching your specified filters and presents you its current contents (possibly only of any
        selected fields).
        Then, you are prompted for an input on how to proceed, and have the following options:
        - `edit` the entry manually (just like with the `edit` command)
        - `inline <field>` to edit the value of the specific field directly on the prompt
        - `context` to request a preview of the entire entry (and not just the selected fields)
        - `done` to complete the review of _this_ entry
        - `skip` to skip the review of _this_ entry
        - `finish` to close the entire review process

        > When the `git` integration is enabled, you can even pause and resume a `review` process!
        > But here we won't go into the details of that.

        Let's put this to the test and review the `author` field of that `Lowry_1951` entry we
        spotted to be faulty earlier.

        This is a great opportunity to teach you about the `--selection` mode, which all commands
        support that also allow `filter` arguments.
        This mode is mainly a helper interface for coBib's TUI where you can make a visual selection
        of entries to act upon.
        But we can repurpose it here to replace the `filter` mechanics by a manual list of `label`s
        to act upon.

        Let's put this all together and fix the `author` with an `inline` edit. Remember, that you
        must typeset the `author` field as a BibLaTeX string, so for this specific case your input
        should be: `Oliver H. Lowry and Nira J. Rosebrough and A. Lewis Farr and Rose J. Randall`.
        ```
        > review author --selection -- Lowry_1951
        ```
        """
        EXPORT = """
        ## Exporting

        The final topic covering coBib's common commands is exporting.
        Since coBib does not store its database directly in BibLaTeX format, exporting is a key
        requirement for the managed references to be useful.

        In addition to exporting with `--bibtex`, you can also use the `--zip` exporter to gather up
        all your attached files into a single archive.
        And just like with other commands, you can use the _filter_ mechanism to narrow down the
        selection of entries that you want to export.

        Finally, the `export` command also provides some nifty mechanics for ensuring a consistent
        typesetting of `journal` names which you can configure via
        `cobib.config.utils.journal_abbreviations`, but we won't cover that in more detail here.

        Instead, let us simply export the current state of the database:
        ```
        > export --bibtex tutorial.bib --zip tutorial.zip
        ```
        """
        LINT = """
        ## Utility Commands

        With all the common commands covered, we are left with some utility commands.

        ### Linting your database

        Sometimes, new versions of coBib can update the formatting of certain database elements.
        To enable you to keep up with this, you can `lint` your database to check for any
        inconsistencies. This will print out a list of messages highlighting those entries (and
        possibly their specific fields) that require updating. Some of them can even be formatted
        automatically when you add the `--format` argument.

        Check the status of your database like so:
        ```
        > lint
        ```
        """
        UNIFY = """
        ### Unify entry labels

        Another consistency check which is _not_ covered by the linter, is to ensure consistent
        `labels` of your entries. Especially when adding new entries from online sources, their
        naming schemes for entry labels can vastly differ. Thus, coBib has a
        `cobib.config.database.format.label_default` setting which works similar to the `modify`'s
        f-string-like modification argument: it can enforce a certain naming pattern for all the
        entries in your database.

        Normally, the default setting does not change any labels (except for replacing Unicode
        characters with ASCII approximations): `{unidecode(label)}`.
        However, for the purposes of this tutorial we have changed the setting to the following:
        ```python
        config.database.format.label_default = (
            "{unidecode(author[0].last).replace('-', '').replace(' ', '')}{year}"
        )
        ```
        In other words every label should be the surname of the first author and the year of
        publication, without any separating character in between.

        When this is configured, the `add` command automatically applies this `label_default`,
        *unless* you explicitly overwrite it with the `--label` argument (as we did at the beginning
        of this tutorial for `Van_Noorden_2014`).

        To simplify the common `modify` command of enforcing all labels to follow this formatting,
        coBib provides the `unify_labels` command which does exactly that. However, it runs in
        `--dry` mode by default, and you must explicitly `--apply` the changes (aligning with the
        `lint` command being told explicitly to `--format`):
        ```
        > unify_labels --apply
        ```
        """
        GIT = """
        ### Interacting with the version control

        We already mentioned several times that coBib optionally integrates with `git` for automatic
        version control of your database. The `git` command makes inspecting and interacting with
        this version control easier by providing an alias to the actual `git` command configured to
        the correct root.

        For example, you can see the tracked history of changes you made throughout this tutorial
        like so:
        ```
        > git log
        ```
        """
        UNDO = """
        And where there is version control, there is also an `undo` command:
        ```
        > undo
        ```
        """
        REDO = """
        ... and a `redo` command:
        ```
        > redo
        ```
        """
        MAN = """
        ### Learning more

        To conclude this tutorial, you should learn about the `man` command, which gives you access
        to coBib's builtin man-pages. While this tutorial has covered all of coBib's commands,
        almost all of them have more options than we covered here. And that is in addition to their
        various configuration settings that we only mentioned very scarcely.

        And if that were not enough, coBib also boasts subscribable _event_ hooks, an extension
        mechanisms for plugins, as well as an interactive terminal user interface (TUI) which we
        cannot cover in such a style of tutorial as this one.

        The manual provides more information on all of coBib's features and settings. Thus, we
        highly suggest you refer not only to the command's `--help` summaries, but also their
        man-pages. As you may recall, you already saw mentions of them in earlier outputs.

        So as the final example, how about you take a look at the man-page of the `man` command:
        ```
        > man man
        ```
        """
        END = """
        # Congratulations! You have reached the end of this guided tutorial on coBib!

        The interactive shell still remains operational from here onwards, so feel free to explore
        and play with what you have learned. Whenever you are done, simply type `exit` or `quit` to
        close the shell.

        If you want even more reading material, you can get a list of all available man-pages using:
        ```
        > man
        ```
        """

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = argparse.ArgumentParser(
            prog="tutorial",
            description="A guided tutorial.",
            epilog="Read cobib-tutorial.1 for more help.",
        )
        cls.argparser = parser

    @override
    async def execute(self) -> None:  # type: ignore[override]
        database_file = self.TEMP_DIR / "cobib_tutorial" / "literature.yaml"
        history_file = self.TEMP_DIR / "cobib_tutorial_history"

        config.defaults()
        config.database.cache = None
        config.database.file = str(database_file)
        config.database.format.label_default = (
            "{unidecode(author[0].last).replace('-', '').replace(' ', '')}{year}"
        )
        config.database.git = True
        config.logging.version = None
        config.shell.history = str(history_file)
        # NOTE: we must clear the PromptConsole instance to ensure the config.shell.history setting
        # can be overwritten at runtime
        PromptConsole.clear_instance()

        state = iter(TutorialCommand.State)

        @Event.PreShellInput.subscribe
        def hr(shell: Shell) -> None:
            shell.live.console.print(Markdown("---"))

        @Event.PreShellInput.subscribe
        def print_instructions(shell: Shell) -> None:
            try:
                next_state = next(state)
            except StopIteration:  # pragma: no cover
                # NOTE: the unittests do not actually run through the entire tutorial, which is why
                # these lines are not covered
                return  # pragma: no cover

            shell.live.console.print(Markdown(dedent(next_state.value)))

        # NOTE: we must delay this import to avoid a circular dependency
        from cobib.ui import Shell  # noqa: PLC0415

        shell = Shell()
        await shell.run_async()

        rmtree(database_file.parent, ignore_errors=True)
        history_file.unlink(missing_ok=True)
