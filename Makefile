prefix ?= /usr

# All man-page template files should contain these two variables:
PACKAGE_DATE := 2025-08-02
PACKAGE_VERSION := v5.4.0

# The man page template files can be found in:
MAN_SRC_DIR := src/cobib/man
# And we will generate the installable files in:
MAN_BUILD_DIR := build/man
# For the HTML documentation, we generate the man-page fragments in:
MAN_HTML_DIR := src/cobib/man

# Find all man pages in MAN_SRC_DIR:
MAN_SRC_FILES := $(shell find $(MAN_SRC_DIR) -name '*.md' -printf '%P ')
# Strip the `.md` suffix to obtain the final filenames:
MAN_BUILD_FILES := $(MAN_SRC_FILES:.md=)
MAN1_BUILD_FILES := $(filter %.1,$(MAN_BUILD_FILES))
MAN5_BUILD_FILES := $(filter %.5,$(MAN_BUILD_FILES))
MAN7_BUILD_FILES := $(filter %.7,$(MAN_BUILD_FILES))
# Replace the `.md` suffix with `.html_fragment` for the man-page HTML targets:
MAN_HTML_FILES := $(MAN_SRC_FILES:.md=.html_fragment)

# The default target generates the HTML fragments of the man pages for the online docs
generate_man_html_fragments: $(MAN_HTML_FILES)

# The following function defines the common man-page compilation arguments:
common_ronn_args = \
	    --date=$(PACKAGE_DATE) \
	    --organization=$(PACKAGE_VERSION) \
	    --output-dir=$(1) \
	    $(2)

# Target to generate the HTML man-page fragments for inclusion in the online docs
$(MAN_HTML_FILES) : %.html_fragment : $(MAN_SRC_DIR)/%.md
	@ronn --html --fragment \
		$(call common_ronn_args,$(MAN_HTML_DIR),$<)
	@# We also perform the following replacements:
	@#   - div -> main: this ensures that markdown2 can correctly detect the headings for the ToC
	@#   - h2 -> h1 and h3 -> h2: to ensure that we respect pdoc's maximum ToC depth level of 2
	@#   - apply a base URL shift to man-page references based on base.txt
	@#   - set the --section CSS variable to the section index on the first line of the file
	@sed -i \
		-e 's/<div/<main/g' -e 's/div>/main>/g' \
		-e 's/h2/h1/g' -e 's/h3/h2/g' \
		-e 's;class="man-ref" href=";class="man-ref" href="$(shell grep $(basename $@) $(MAN_HTML_DIR)/base.txt | awk '{ print $$ 2 }');g' \
		-e '1s,^,<head><style>.mp p.man-name code {--section: $(shell echo $@ | awk '{split($$0,a,"."); print a[2]}');}</style></head>,' \
		$(MAN_HTML_DIR)/$@

# The target to generate the actual UNIX man-pages
generate_man_pages: $(MAN_BUILD_FILES)

$(MAN_BUILD_DIR)%:
	mkdir -p $@

# We must sort the man-pages into the correct subdirectories
$(MAN1_BUILD_FILES): %.1 : $(MAN_SRC_DIR)/%.1.md $(MAN_BUILD_DIR)/man1
	@ronn --roff \
		$(call common_ronn_args,$(MAN_BUILD_DIR)/man1,$<)

$(MAN5_BUILD_FILES): %.5 : $(MAN_SRC_DIR)/%.5.md $(MAN_BUILD_DIR)/man5
	@ronn --roff \
		$(call common_ronn_args,$(MAN_BUILD_DIR)/man5,$<)

$(MAN7_BUILD_FILES): %.7 : $(MAN_SRC_DIR)/%.7.md $(MAN_BUILD_DIR)/man7
	@ronn --roff \
		$(call common_ronn_args,$(MAN_BUILD_DIR)/man7,$<)

install_man_pages: $(foreach obj,$(MAN_BUILD_FILES),install_$(obj))

# The following function defines the install command arguments:
install_args = -Dm644 $(MAN_BUILD_DIR)/$(1)/$(2) $(DESTDIR)$(prefix)/share/man/$(1)/$(2)

# Again, we must sort the man-pages into the correct subdirectories
$(foreach obj,$(MAN1_BUILD_FILES),install_$(obj)): install_%.1 : %.1
	install $(call install_args,man1,$^)

$(foreach obj,$(MAN5_BUILD_FILES),install_$(obj)): install_%.5 : %.5
	install $(call install_args,man5,$^)

$(foreach obj,$(MAN7_BUILD_FILES),install_$(obj)): install_%.7 : %.7
	install $(call install_args,man7,$^)

# This phony target installs the license file:
install_license:
	install -Dm644 LICENSE.txt $(DESTDIR)$(prefix)/share/licenses/cobib/LICENSE

# This phony target installs all extra files:
install_extras: install_man_pages install_license

.PHONY: generate_man_pages install_man_pages install_license install_extras
