# All man-page template files should contain these two variables:
PACKAGE_DATE := 2025-10-11
PACKAGE_VERSION := v6.0.0

# The man page template files can be found in:
MAN_SRC_DIR := src/cobib/man
# And we will generate the installable files in:
MAN_BUILD_DIR := build/man
# For the HTML documentation, we generate the man-page fragments in:
MAN_HTML_DIR := src/cobib/man

include docs/theme/Makefile
