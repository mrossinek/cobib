"""coBib's Zotero importer.

This importer handles migrating from [Zotero][1] to coBib.
Normally, you would only need to trigger this migration once, but for convenience, coBib will store
the OAuth authentication tokens provided by the Zotero API in its cache (whose location is
configurable via `cobib.config.config.LoggingConfig.cache`).

The importer is registered under the `--zotero` command-line argument of the
`cobib.commands.import_.ImportCommand`. Thus, you can trigger it like so:
```
cobib import --zotero
```

### Additional Options

You can provide some additional arguments for the Zotero importer.

First of all, you can disable the cache. This is useful if you want to avoid caching any
authentication tokens or if you want to re-trigger the OAuth authentication procedure.
```
cobib import --zotero -- --no-cache
```

You can also provide a custom Zotero user ID via the command line. If you do so, OAuth
authentication will not be triggered. The import will work normally, if the library associated with
the provided user ID is publicly accessible. Otherwise, you will also need to provide your own
Zotero API key (see next paragraph).
```
cobib import --zotero -- --user-id <user ID>
```

As mentioned above, you can provide your own Zotero API key if you do not want coBib to initiate an
OAuth authentication process for you. This argument only takes affect if you also provide your own
Zotero user ID.
```
cobib import --zotero -- --user-id <user ID> --api-key <API key>
```

[1]: https://www.zotero.org/
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys

import requests
from requests_oauthlib import OAuth1Session
from typing_extensions import override

from cobib.config import Event, config
from cobib.database import Entry
from cobib.parsers import BibtexParser
from cobib.utils.file_downloader import FileDownloader
from cobib.utils.rel_path import RelPath

from .base_importer import ArgumentParser, Importer

LOGGER = logging.getLogger(__name__)
"""@private module logger."""


class ZoteroImporter(Importer):
    """The Zotero Importer.

    This importer can parse the following arguments:

        * `--no-cache`: disables the use of any cached OAuth tokens.
        * `--user-id`: the Zotero user ID used for API calls. You can find your user ID at
          <https://www.zotero.org/settings/keys>. Unless you also specify `--no-cache`, this value
          will be stored in coBib's internal cache. If you do not also provide an `--api-key`, you
          can only read publicly available Zotero databases.
        * `--api-key`: overwrites the user-specific Zotero API key for the coBib application. Unless
          you also specify `--no-cache`, this value will be stored in coBib's internal cache. This
          argument only takes effect if `--user-id` is also provided.
    """

    name = "zotero"

    _CLIENT_KEY = "94a2f739acd6be46df50"
    """The key given to the coBib application by the Zotero API."""
    _CLIENT_SECRET = "8d2659a20871036a462f"
    """The secret given to the coBib application by the Zotero API."""

    OAUTH_REQUEST_URL = "https://www.zotero.org/oauth/request"
    """The URL from which to initiate OAuth authentication token requests."""
    OAUTH_ACCESS_URL = "https://www.zotero.org/oauth/access"
    """The URL from which to fetch generated OAuth authentication token."""
    OAUTH_AUTHORIZE_URL = "https://www.zotero.org/oauth/authorize"
    """The URL where the user must be redirected in order to authenticate the coBib application."""

    @override
    def __init__(self, *args: str, skip_download: bool = False) -> None:
        super().__init__(*args, skip_download=skip_download)

        self.authentication: dict[str, str] = {}
        """The authentication dictionary used as a header during the `GET` request of the Zotero
        API."""

        self.protected_url: str = ""
        """The protected URL via which the Zotero API gets accessed."""

        self.imported_entries: list[Entry] = []
        """A list of `cobib.database.Entry` objects which were imported by this importer."""

    @override
    @classmethod
    def init_argparser(cls) -> None:
        parser = ArgumentParser(prog="zotero", description="Zotero migration parser.")
        parser.add_argument(
            "--no-cache", action="store_true", help="disable use of cached OAuth tokens"
        )
        parser.add_argument(
            "--api-key", type=str, help="the user-specific Zotero API key for the coBib application"
        )
        parser.add_argument("--user-id", type=str, help="the Zotero user ID used for API calls")

        cls.argparser = parser

    @override
    async def fetch(self) -> list[Entry]:
        LOGGER.debug("Starting Zotero fetching.")

        if self.largs.user_id is not None:
            self.authentication["UserID"] = self.largs.user_id
            if self.largs.api_key is not None:
                self.authentication["Zotero-API-Key"] = self.largs.api_key

            if not self.largs.no_cache:
                self._store_oauth_tokens(self.authentication)
        else:
            self.authentication = self._get_authentication_tokens(self.largs.no_cache)

        user_id = self.authentication.pop("UserID")

        LOGGER.info("Requesting items from Zotero user via API v3.")
        self.protected_url = f"https://api.zotero.org/users/{user_id}/items?include=biblatex&v=3"

        Event.PreZoteroImport.fire(self)

        raw_result = requests.get(self.protected_url, headers=self.authentication, timeout=30)
        if raw_result.encoding is None:
            raw_result.encoding = "utf-8"

        bibtex_parser = BibtexParser()

        results = json.loads(raw_result.content)

        encountered_attachments: dict[str, dict[str, str]] = {}

        for res in results:
            biblatex = res.get("biblatex", "").strip()
            if not bool(biblatex):
                # check if this is an attachment
                try:
                    attachment_enclosure = res.get("links", {}).get("enclosure", {})
                    LOGGER.info("Storing encountered attachment: %s", res["key"])
                    encountered_attachments[res["key"]] = {
                        "href": attachment_enclosure["href"],
                        "title": attachment_enclosure["title"],
                    }
                except KeyError:
                    pass
                continue

            LOGGER.info("Parsing encountered BibLaTeX entry: %s", res["key"])
            # biblatex contains exactly one entry so we can pop it from the OrderedDict
            _, new_entry = bibtex_parser.parse(biblatex).popitem()

            # Zotero-specific `journal` keyword handling
            new_entry.data.pop("shortjournal")
            new_entry.data["journal"] = new_entry.data.pop("journaltitle")

            # check attachment
            try:
                attachment = res.get("links", {}).get("attachment", {})
            except KeyError:
                pass

            if attachment.get("attachmentType", None) == "application/pdf":
                LOGGER.info("Queuing associated attachment for download.")
                new_entry.data["_download"] = attachment["href"].split("/")[-1]

            self.imported_entries.append(new_entry)

        for entry in self.imported_entries:  # pragma: no cover
            if "_download" not in entry.data.keys():
                continue

            key = entry.data.pop("_download")
            if self.skip_download:
                LOGGER.info("Skipping attachment download.")
                continue
            if key not in encountered_attachments:
                LOGGER.warning("Skipping unknown attachment: %s", key)
                continue

            url = encountered_attachments[key]["href"]
            filename = encountered_attachments[key]["title"]

            path = await FileDownloader().download(url, filename, headers=self.authentication)
            if path is not None:
                entry.file = str(path)  # type: ignore[assignment]

        Event.PostZoteroImport.fire(self)

        return self.imported_entries

    @staticmethod
    def _get_fresh_oauth_tokens() -> dict[str, str]:  # pragma: no cover
        """Obtain new OAuth authentication tokens from the Zotero API.

        Returns:
            A dictionary containing the authentication information. More specifically, two values
            will be stored:
                - `Zotero-API-Key`: the API key generated by the Zotero user specifically for coBib
                - `UserID`: the Zotero user ID used during user-specific API access.
        """
        LOGGER.info("Obtaining new OAuth tokens from Zotero.")
        oauth = OAuth1Session(ZoteroImporter._CLIENT_KEY, ZoteroImporter._CLIENT_SECRET)
        LOGGER.debug("Fetching temporary request token")
        oauth.fetch_request_token(ZoteroImporter.OAUTH_REQUEST_URL)

        authorization_url = oauth.authorization_url(ZoteroImporter.OAUTH_AUTHORIZE_URL)
        LOGGER.debug("Opening user authorization URL")
        opener = "xdg-open" if sys.platform.lower() == "linux" else "open"
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            subprocess.Popen(
                [opener, authorization_url],
                stdout=devnull,
                stderr=devnull,
                stdin=devnull,
                close_fds=True,
            )
        redirect_response = input("Please insert the redirected URL here: ")
        LOGGER.debug("Parsing authorization redirect URL")
        oauth.parse_authorization_response(redirect_response)

        LOGGER.debug("Fetching permanent access token")
        oauth_tokens = oauth.fetch_access_token(ZoteroImporter.OAUTH_ACCESS_URL)

        authentication = {
            "Zotero-API-Key": oauth_tokens.get("oauth_token"),
            "UserID": oauth_tokens.get("userID"),
        }

        return authentication

    @staticmethod
    def _get_cached_oauth_tokens() -> dict[str, str]:
        """Obtain the OAuth authentication tokens for the Zotero API from coBib's cache.

        Returns:
            A dictionary containing the authentication information. Refer to
            `_get_fresh_oauth_tokens` for more specific details on the dictionary contents.
        """
        LOGGER.info("Attempting to load cached OAuth tokens for Zotero.")
        cache_path = RelPath(config.logging.cache).path
        try:
            with open(cache_path, "r", encoding="utf-8") as cache:
                cached_data = json.load(cache)
        except FileNotFoundError:
            cached_data = {}
        return cached_data.get("Zotero", {})  # type: ignore[no-any-return]

    @staticmethod
    def _store_oauth_tokens(tokens: dict[str, str]) -> None:
        """Stores the OAuth authentication tokens for the Zotero API in coBib's cache.

        Args:
            tokens: the dictionary containing the authentication information. Refer to
                `_get_fresh_oauth_tokens` for more specific details on the dictionary contents.
        """
        LOGGER.info("Storing OAuth tokens for Zotero in cache.")
        cache_path = RelPath(config.logging.cache).path
        try:
            with open(cache_path, "r", encoding="utf-8") as cache:
                cached_data = json.load(cache)
        except FileNotFoundError:
            cached_data = {}

        if "Zotero" not in cached_data.keys():
            cached_data["Zotero"] = {}
        cached_data["Zotero"].update(tokens)

        if not cache_path.parent.exists():
            cache_path.parent.mkdir(parents=True)

        with open(cache_path, "w", encoding="utf-8") as cache:
            json.dump(cached_data, cache)

    @staticmethod
    def _get_authentication_tokens(no_cache: bool = False) -> dict[str, str]:
        """Obtain the OAuth authentication tokens for the Zotero API.

        This method will first attempt to load the tokens from the cache. If that fails, it will
        generate new tokens via the Zotero API.

        Args:
            no_cache: whether or not to use cached OAuth tokens.

        Returns:
            A dictionary containing the authentication information. Refer to
            `_get_fresh_oauth_tokens` for more specific details on the dictionary contents.
        """
        authentication: dict[str, str] = {}

        if not no_cache:
            authentication = ZoteroImporter._get_cached_oauth_tokens()

        if authentication:
            LOGGER.info("Successfully obtained OAuth tokens for Zotero from cache.")
        else:  # pragma: no cover
            authentication = ZoteroImporter._get_fresh_oauth_tokens()
            if not no_cache:
                ZoteroImporter._store_oauth_tokens(authentication)

        return authentication
