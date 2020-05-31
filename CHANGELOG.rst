====================================
Changelog for Ansible Changelog Tool
====================================


v0.2.0
======

Minor Changes
-------------

- Title generation improved (remove superfluous space).
- ``lint`` subcommand no longer requires specification whether it is run inside a collection or not (if usual indicators are absent).
- Improve reStructuredText creation when new modules with and without namespace exist at the same time.
- Improve error handling.
- Fix internal API for ACD changelog generation (pruning and concatenation of changelogs).
- Use PyYAML C loader/dumper if available.
- Added more testing.

v0.1.0
======

Initial release as antsibull-changelog. The Ansible Changelog Tool has originally been developed by @mattclay in [the ansible/ansible](https://github.com/ansible/ansible/blob/stable-2.9/packaging/release/changelogs/changelog.py) repository for Ansible itself. It has been extended in https://github.com/felixfontein/ansible-changelog/ and https://github.com/ansible-community/antsibull/ to work with collections, until it was moved to its current location https://github.com/ansible-community/antsibull-changelog/.
