# Contributing
If you want to contribute to CoBib feel free to open a [PR on Gitlab](https://gitlab.com/mrossinek/cobib/-/merge_requests).
Bug fixes and feature additions are always welcome!
If you need some inspiration you also take a look at the [list of open issues](https://gitlab.com/mrossinek/cobib/-/issues) to see whether there is something you can help with.

## Testing
We use `pytest` and `pyte` for our test suite so be sure to install these additional packages:
```
pip install pytest pyte
```
You can run the tests locally with
```
make test
```
or if you want to run only some specific tests:
```
python -m pytest test/TEST.py -k FUNCTION_NAME
```
Please also check your code style with the following checks:
```
pip install pylint pyenchant pydocstyle
make lint
make spell
make doc
```

## Releasing [Repository admins only]
To create a new release you should do the following steps:
0. Update the version number in `cobib/__init__.py` and the man page
1. Ensure you have the following packages installed: `pip install wheel twine`
2. Create the release wheel and archive files: `python setup.py sdist bdist_wheel`
3. Publish the new release on pypi: `python -m twine upload dist/cobib-VERSION*`
4. Update the [changelog](CHANGELOG.md) including the link to pypi
5. Commit, tag and push to Gitlab
6. Create a release on Gitlab by adding the changelog section to the tag release notes
