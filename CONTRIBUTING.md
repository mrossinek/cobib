# Contributing
If you want to contribute to coBib feel free to open a [PR on Gitlab](https://gitlab.com/cobib/cobib/-/merge_requests).
Bug fixes and feature additions are always welcome!
If you need some inspiration you also take a look at the [list of open issues](https://gitlab.com/cobib/cobib/-/issues) to see whether there is something you can help with.

## Setup
We are using [`tox`](https://tox.readthedocs.io/en/latest/index.html) for a unified testing experience between local installations and the CI.
Thus, after installing tox (`pip install tox`) you can inspect the available environments with `tox -l`.
You can also inspect `tox.ini` and install the required development tools manually.
I choose not to duplicate the information in another file, because this is likely to become outdated when it is not being used regularly.

## Testing
You can run the tests locally with
```
tox -e py39
```
or if you want to run only some specific tests:
```
pytest tests/PATH_TO_TEST.py -k FUNCTION_NAME
```
Please also check your code style with the following checks:
```
tox -e lint
```

## Coverage
You can check the coverage with:
```
tox -e coverage
```

## Documentation
When working on coBib you may find the online documentation at https://cobib.gitlab.io/cobib/cobib.html or a locally generated version, useful.
For the latter, please refer to the README.

Once you have opened a merge request on GitLab, you can also view an automatically generated version of the documentation for your branch through the `View App` button below the `Pipeline` results.

## Releasing [Repository admins only]
To create a new release you should do the following steps:
1. Update the version number in `src/cobib/__init__.py`
2. Update the version number and publication date in the `Makefile`
3. Update the [changelog](CHANGELOG.md) including the link to pypi
4. Commit, tag and push to Gitlab
5. Verify that the PyPI package and Gitlab release were created successfully
6. Update the Gitlab release notes by adding the changelog section
7. Create a matching release on Github
