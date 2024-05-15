<!--
Copyright (c) Ansible Project
GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Configuration Settings for antsibull-changelog

This document describes all settings that are supported in
`changelogs/config.yaml`.

## General options

### `add_plugin_period` (boolean)

The default value is `false`.

If set to `false`, the plugin short description is used. If set to `true`, a period is added to the end of the plugin short description if no other end punctuation is present. Setting to ``true`` complies with the [Ansible changelog format](https://docs.ansible.com/ansible/latest/community/development_process.html#changelogs-how-to-format).


### `always_refresh` (string)

Allowed values are `none`, `full`, or a comma-separated combination of
one or more of `plugins`, `plugins-without-removal`, `fragments` and
`fragments-without-archives`.

If `true` is passed, it will be converted to `full`. If `false` is
passed, it will be converted to `none`.

For details, see ["Updating/Refreshing changelog.yaml" in the main
documentation](changelogs.md#updatingrefreshing-changelogyaml).

### `archive_path_template` (optional string)

The default value is `null`.

When `keep_fragments` is set to `false`, and this setting is defined,
fragments will be copied to the path specified by this setting after a
release is made. This setting is assumed to point to a directory, and
the placeholder `{version}` can be used to make the destination
dependent on the version number of the new release. If the directory
does not yet exist, it will be created.

### `changelog_filename_template` (string)

The default value is `CHANGELOG-v%s.rst` for existing configurations,
and `../CHANGELOG.rst` for new configurations.

This is the path relative to the `changelogs/` directory where the
reStructuredText version of the changelog is written to. The placeholder
`%s` will be replaced by the first `changelog_filename_version_depth`
parts of the version of the release.

> [!NOTE]
> The file extension (default `.rst`) will always be replaced by the
> extension matching the output format (see [`output_formats`](#output_formats-list-of-strings)).
> Therefore the extension provided here will always be ignored.

### `changelog_filename_version_depth` (integer)

The default value is 2 for existing configurations, and 0 for new
configurations.

Determines the number of parts of the current release version to be used
when replacing `%s` in `changelog_filename_template` (see above). For
the value 2, version 1.2.3 will result in the string `1.2`. The value 0
results in the empty string.

### `changes_file` (string)

The default value is `.changes.yaml` for existing configurations, and
`changelog.yaml` for new configurations.

The YAML file where the changelog is stored in a machine-readable form.
This is relative to the `changelogs/` directory and should not be
changed, since `changelogs/changelog.yaml` is the standard place for the
machine-readable file which is expected to be there by the Ansible
Community Distribution changelog generator.

### `changes_format` (string)

The default value is `classic` for existing configurations, and
`combined` for new configurations.

Determines whether `changes_file` contains only references to changelog
fragments or plugins (was used internally by Ansible until version 2.9),
or whether all fragments and plugin data is stored inside the file (used
by Ansible 2.10 and in collections). Should never be set to `classic`,
except when using the changelog generator for Ansible 2.9 or earlier.

Note that support for `classic` is **DEPRECATED** and will be removed in
a future release. The field will from then on be required.

### `flatmap` (optional boolean)

The default value is `null`.

Can be set to `true` or `false` explicitly to enable respectively
disable flatmapping. Since flatmapping is disabled by default (except
for ansible-core), this is effectively only needed for the big community
collections `community.general` and `community.network`.

When enabled, a plugin `foo.bar.subdir.dir.plugin_name` will be
mentioned as `plugin_name` or `foo.bar.plugin_name` (if `use_fqcn` is
`true`), instead of as `subdir.dir.plugin_name` respectively
`foo.bar.subdir.dir.plugin_name`.

### `is_other_project` (boolean)

The default value is `false`.

If set to `true`, does not look for `galaxy.yml` and does not look for
new Ansible objects (plugins, modules and roles). This allows the
changelog generator to be used for projects which are not
ansible-core/-base or an Ansible collection.

### `ignore_other_fragment_extensions` (boolean)

The default value is `false` for existing configurations, and `true` for
new configurations.

If set to `true`, only `.yml` and `.yaml` fragment filenames are
considered which do not start with a dot. This is compatible with what
`ansible-test sanity --test changelog` enforces. If set to `false`
(default if not specified), all filenames that do not start with a dot
are considered.

### `keep_fragments` (boolean)

The default value is `false` (except if `changes_format` is `classic`).

If set to `false`, the fragment files will be removed after a release is
done. If set to `true`, fragment files for old releases are kept.

If fragment files should be moved to another directory after release,
set this setting to `false` and set `archive_path_template`.

See also `prevent_known_fragments`.

### `mention_ancestor` (boolean)

The default value is `true`.

If an ancestor is defined in `changelogs/changelog.yaml`, determines
whether it should be mentioned at the beginning of the changelog or not.
If set to `true`,
`This changelog describes changes after version {ancestor}` will be
inserted at the top of the changelog.

### `notes_dir` (string)

The default value is `fragments`.

The name of the subdirectory of `changelogs/` that contains the
changelog fragments.

### `prelude_name` (string)

The default value is `release_summary`.

Name of the prelude section to be used in changelog fragments. This
section is special, in that it does not accept a list, but a string.

### `prelude_title` (string)

The default value is `Release Summary`.

The title for the section whose name is set in `prelude_name`.

### `prevent_known_fragments` (optional boolean)

The default value is the same value as the `keep_fragments` option.

If set to `true`, will not add changelog fragments to a release whose
filename was already used in the past. This was the default behavior
before antsibull-changelog 0.9.0. From 0.9.0 on, it is set to `false` by
default if `keep_fragments` is `false`.

If `keep_fragments` is set to `false` later-on when some fragments from
older releases are still there, and you want to keep them, make sure to
set `prevent_known_fragments` explicitly to `true`. Otherwise they will
be added again to the next release.

### `sanitize_changelog` (boolean)

The default value is `false` for existing configurations, and `true` for
new configurations.

Remove all invalid and superfluous information when loading a
`changelogs/changelog.yaml` file.

### `sections` (list of two-element lists of strings)

The default value is:

    - - major_changes
      - Major Changes
    - - minor_changes
      - Minor Changes
    - - breaking_changes
      - Breaking Changes / Porting Guide
    - - deprecated_features
      - Deprecated Features
    - - removed_features
      - Removed Features (previously deprecated)
    - - security_fixes
      - Security Fixes
    - - bugfixes
      - Bugfixes
    - - known_issues
      - Known Issues

Lists all section names (first element) and their titles (second
element). The only two sections not listed here are the prelude section
(`release_summary` / "Release Summary") and the trivial section
(`trivial`, no title).

It is not recommended to change this list, except possibly adjust
section titles. Collections using other section names will cause
problems with the Ansible Community Distribution changelog generation.

### `title` (string)

The default value is the titlecase of the collection's namespace and
name.

The title is shown at the top of the changelog.

### `trivial_section_name` (optional string)

The default value is `trivial` for collections and other projects, and
`null` for ansible-core/ansible-base.

This defines a section that is not included in the generated
reStructuredText version of the changelog. It can be used to add
changelog fragments to changes that are so minor (trivial) that they
should not appear in the changelog, or that are irrelevant to the user
(for example changes in the CI system used). When set to `null`, no
trivial section is allowed.

### `use_fqcn` (boolean)

The default value is `false` for existing configurations, and `true` for
new configurations.

When set to `true`, uses FQCN (Fully Qualified Collection Names) when
mentioning new plugins and modules. This means that `namespace.name.`
is prepended to the plugin respectively module names.

### `output_formats` (list of strings)

The default is `["rst"]`.

A list of output formats to write the changelog as. Supported formats
are `rst` for ReStructuredText and `md` for MarkDown.

## Deprecated options

### `new_plugins_after_name` (string)

The default value is `''` (empty string).

This setting is not used.

## Ansible-core/-base specific options

These options are only used for the changelog for ansible-core, i.e. in
the ansible/ansible GitHub repository.

### `use_semantic_versioning` (boolean)

The default value is `false`.

If set to `true`, assumes that ansible-core use semantic versioning
instead of the classic Ansible version numbers. This is mainly relevant
for pre-releases. If set to `true`, `release_tag_re` and
`pre_release_tag_re` are ignored.

### `release_tag_re` (string)

The default value is `((?:[\d.ab]|rc)+)`.

This value is used to detect versions that are proper release versions,
and not prereleases. This is a regular expression matching the version
string preprended with `v`.

This setting is ignored if `use_semantic_versioning` is set to `true`.

### `pre_release_tag_re` (string)

The default value is `(?P<pre_release>\.\d+(?:[ab]|rc)+\d*)$`.

This value is used to detect versions that are prereleases. This is a
regular expression matching the version string preprended with `v`.

This setting is ignored if `use_semantic_versioning` is set to `true`.
