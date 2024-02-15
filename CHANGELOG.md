# Ansible Changelog Tool Release Notes

**Topics**
- <a href="#v0-25-0">v0\.25\.0</a>
  - <a href="#release-summary">Release Summary</a>
  - <a href="#minor-changes">Minor Changes</a>
  - <a href="#bugfixes">Bugfixes</a>
- <a href="#v0-24-0">v0\.24\.0</a>
  - <a href="#release-summary-1">Release Summary</a>
  - <a href="#minor-changes-1">Minor Changes</a>
  - <a href="#deprecated-features">Deprecated Features</a>
- <a href="#v0-23-0">v0\.23\.0</a>
  - <a href="#release-summary-2">Release Summary</a>
  - <a href="#minor-changes-2">Minor Changes</a>
- <a href="#v0-22-0">v0\.22\.0</a>
  - <a href="#release-summary-3">Release Summary</a>
  - <a href="#minor-changes-3">Minor Changes</a>
- <a href="#v0-21-0">v0\.21\.0</a>
  - <a href="#release-summary-4">Release Summary</a>
  - <a href="#deprecated-features-1">Deprecated Features</a>
- <a href="#v0-20-0">v0\.20\.0</a>
  - <a href="#release-summary-5">Release Summary</a>
  - <a href="#major-changes">Major Changes</a>
  - <a href="#bugfixes-1">Bugfixes</a>
- <a href="#v0-19-0">v0\.19\.0</a>
  - <a href="#release-summary-6">Release Summary</a>
  - <a href="#minor-changes-4">Minor Changes</a>
- <a href="#v0-18-0">v0\.18\.0</a>
  - <a href="#release-summary-7">Release Summary</a>
  - <a href="#breaking-changes--porting-guide">Breaking Changes / Porting Guide</a>
- <a href="#v0-17-0">v0\.17\.0</a>
  - <a href="#release-summary-8">Release Summary</a>
  - <a href="#minor-changes-5">Minor Changes</a>
- <a href="#v0-16-0">v0\.16\.0</a>
  - <a href="#release-summary-9">Release Summary</a>
  - <a href="#minor-changes-6">Minor Changes</a>
  - <a href="#bugfixes-2">Bugfixes</a>
- <a href="#v0-15-0">v0\.15\.0</a>
  - <a href="#release-summary-10">Release Summary</a>
  - <a href="#minor-changes-7">Minor Changes</a>
- <a href="#v0-14-0">v0\.14\.0</a>
  - <a href="#release-summary-11">Release Summary</a>
  - <a href="#minor-changes-8">Minor Changes</a>
- <a href="#v0-13-0">v0\.13\.0</a>
  - <a href="#release-summary-12">Release Summary</a>
  - <a href="#minor-changes-9">Minor Changes</a>
  - <a href="#bugfixes-3">Bugfixes</a>
- <a href="#v0-12-0">v0\.12\.0</a>
  - <a href="#release-summary-13">Release Summary</a>
  - <a href="#minor-changes-10">Minor Changes</a>
  - <a href="#bugfixes-4">Bugfixes</a>
- <a href="#v0-11-0">v0\.11\.0</a>
  - <a href="#minor-changes-11">Minor Changes</a>
  - <a href="#bugfixes-5">Bugfixes</a>
- <a href="#v0-10-0">v0\.10\.0</a>
  - <a href="#minor-changes-12">Minor Changes</a>
  - <a href="#bugfixes-6">Bugfixes</a>
- <a href="#v0-9-0">v0\.9\.0</a>
  - <a href="#major-changes-1">Major Changes</a>
  - <a href="#minor-changes-13">Minor Changes</a>
  - <a href="#breaking-changes--porting-guide-1">Breaking Changes / Porting Guide</a>
- <a href="#v0-8-1">v0\.8\.1</a>
  - <a href="#bugfixes-7">Bugfixes</a>
- <a href="#v0-8-0">v0\.8\.0</a>
  - <a href="#minor-changes-14">Minor Changes</a>
- <a href="#v0-7-0">v0\.7\.0</a>
  - <a href="#minor-changes-15">Minor Changes</a>
- <a href="#v0-6-0">v0\.6\.0</a>
  - <a href="#minor-changes-16">Minor Changes</a>
- <a href="#v0-5-0">v0\.5\.0</a>
  - <a href="#minor-changes-17">Minor Changes</a>
- <a href="#v0-4-0">v0\.4\.0</a>
  - <a href="#minor-changes-18">Minor Changes</a>
  - <a href="#bugfixes-8">Bugfixes</a>
- <a href="#v0-3-1">v0\.3\.1</a>
  - <a href="#bugfixes-9">Bugfixes</a>
- <a href="#v0-3-0">v0\.3\.0</a>
  - <a href="#minor-changes-19">Minor Changes</a>
- <a href="#v0-2-1">v0\.2\.1</a>
  - <a href="#bugfixes-10">Bugfixes</a>
- <a href="#v0-2-0">v0\.2\.0</a>
  - <a href="#minor-changes-20">Minor Changes</a>
- <a href="#v0-1-0">v0\.1\.0</a>
  - <a href="#release-summary-14">Release Summary</a>

<a id="v0-25-0"></a>
## v0\.25\.0

<a id="release-summary"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes"></a>
### Minor Changes

* Add <code>\-\-version</code> flag to print package version and exit \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/147](https\://github\.com/ansible\-community/antsibull\-changelog/pull/147)\)\.

<a id="bugfixes"></a>
### Bugfixes

* When multiple output formats are defined and <code>antsibull\-changelog generate</code> is used with both <code>\-\-output</code> and <code>\-\-output\-format</code>\, an error was displayed that <code>\-\-output\-format</code> must be specified \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/149](https\://github\.com/ansible\-community/antsibull\-changelog/issues/149)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/151](https\://github\.com/ansible\-community/antsibull\-changelog/pull/151)\)\.

<a id="v0-24-0"></a>
## v0\.24\.0

<a id="release-summary-1"></a>
### Release Summary

Feature release which now allows to output MarkDown\.

<a id="minor-changes-1"></a>
### Minor Changes

* Allow automatically retrieving package version for hatch projects with the <code>hatch version</code> command \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/141](https\://github\.com/ansible\-community/antsibull\-changelog/pull/141)\)\.
* Allow to render changelogs as MarkDown\. The output formats written can be controlled with the <code>output\_formats</code> option in the config file \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/139](https\://github\.com/ansible\-community/antsibull\-changelog/pull/139)\)\.
* Officially support Python 3\.12 \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/134](https\://github\.com/ansible\-community/antsibull\-changelog/pull/134)\)\.

<a id="deprecated-features"></a>
### Deprecated Features

* Some code in <code>antsibull\_changelog\.changelog\_entry</code> has been deprecated\, and the <code>antsibull\_changelog\.rst</code> module has been deprecated completely\. If you use them in your own code\, please take a look at the [PR deprecating them](https\://github\.com/ansible\-community/antsibull\-changelog/pull/139) for information on how to stop using them \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/139](https\://github\.com/ansible\-community/antsibull\-changelog/pull/139)\)\.

<a id="v0-23-0"></a>
## v0\.23\.0

<a id="release-summary-2"></a>
### Release Summary

Feature release\.

<a id="minor-changes-2"></a>
### Minor Changes

* Allow to generate changelog for a specific version \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/130](https\://github\.com/ansible\-community/antsibull\-changelog/pull/130)\)\.
* Allow to generate only the last entry without preamble with the <code>generate</code> command \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/131](https\://github\.com/ansible\-community/antsibull\-changelog/pull/131)\)\.
* Allow to write <code>generate</code> output to a user\-provided file \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/131](https\://github\.com/ansible\-community/antsibull\-changelog/pull/131)\)\.

<a id="v0-22-0"></a>
## v0\.22\.0

<a id="release-summary-3"></a>
### Release Summary

New feature release

<a id="minor-changes-3"></a>
### Minor Changes

* Add <code>antsibull\-changelog\-lint</code> and <code>antsibull\-changelog\-lint\-changelog\-yaml</code> pre\-commit\.com hooks \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/125](https\://github\.com/ansible\-community/antsibull\-changelog/pull/125)\)\.
* Add <code>toml</code> extra to pull in a toml parser to use to guess the version based on <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/126](https\://github\.com/ansible\-community/antsibull\-changelog/pull/126)\)\.

<a id="v0-21-0"></a>
## v0\.21\.0

<a id="release-summary-4"></a>
### Release Summary

Maintenance release with a deprecation\.

<a id="deprecated-features-1"></a>
### Deprecated Features

* Support for <code>classic</code> changelogs is deprecated and will be removed soon\. If you need to build changelogs for Ansible 2\.9 or before\, please use an older version \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/123](https\://github\.com/ansible\-community/antsibull\-changelog/pull/123)\)\.

<a id="v0-20-0"></a>
## v0\.20\.0

<a id="release-summary-5"></a>
### Release Summary

Bugfix and maintenance release using a new build system\.

<a id="major-changes"></a>
### Major Changes

* Change pyproject build backend from <code>poetry\-core</code> to <code>hatchling</code>\. <code>pip install antsibull</code> works exactly the same as before\, but some users may be affected depending on how they build/install the project \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/109](https\://github\.com/ansible\-community/antsibull\-changelog/pull/109)\)\.

<a id="bugfixes-1"></a>
### Bugfixes

* When releasing ansible\-core and only one of <code>\-\-version</code> and <code>\-\-codename</code> is supplied\, error out instead of ignoring the supplied value \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/104](https\://github\.com/ansible\-community/antsibull\-changelog/issues/104)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/105](https\://github\.com/ansible\-community/antsibull\-changelog/pull/105)\)\.

<a id="v0-19-0"></a>
## v0\.19\.0

<a id="release-summary-6"></a>
### Release Summary

Feature release\.

<a id="minor-changes-4"></a>
### Minor Changes

* Allow to extract other project versions for JavaScript / TypeScript projects from <code>package\.json</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/100](https\://github\.com/ansible\-community/antsibull\-changelog/pull/100)\)\.
* Allow to extract other project versions for Python projects from PEP 621 conformant <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/100](https\://github\.com/ansible\-community/antsibull\-changelog/pull/100)\)\.
* Support Python 3\.11\'s <code>tomllib</code> to load <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/101](https\://github\.com/ansible\-community/antsibull\-changelog/issues/101)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/102](https\://github\.com/ansible\-community/antsibull\-changelog/pull/102)\)\.
* Use more specific exceptions than <code>Exception</code> for some cases in internal code \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/103](https\://github\.com/ansible\-community/antsibull\-changelog/pull/103)\)\.

<a id="v0-18-0"></a>
## v0\.18\.0

<a id="release-summary-7"></a>
### Release Summary

Maintenance release that drops support for older Python versions\.

<a id="breaking-changes--porting-guide"></a>
### Breaking Changes / Porting Guide

* Drop support for Python 3\.6\, 3\.7\, and 3\.8 \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/93](https\://github\.com/ansible\-community/antsibull\-changelog/pull/93)\)\.

<a id="v0-17-0"></a>
## v0\.17\.0

<a id="release-summary-8"></a>
### Release Summary

Feature release for ansible\-core\.

<a id="minor-changes-5"></a>
### Minor Changes

* Only allow a <code>trival</code> section in the ansible\-core/ansible\-base changelog when explicitly configured \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/90](https\://github\.com/ansible\-community/antsibull\-changelog/pull/90)\)\.

<a id="v0-16-0"></a>
## v0\.16\.0

<a id="release-summary-9"></a>
### Release Summary

Feature and bugfix release\.

<a id="minor-changes-6"></a>
### Minor Changes

* Allow to extract other project versions for Python poetry projects from <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/80](https\://github\.com/ansible\-community/antsibull\-changelog/pull/80)\)\.
* The files in the source repository now follow the [REUSE Specification](https\://reuse\.software/spec/)\. The only exceptions are changelog fragments in <code>changelogs/fragments/</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/82](https\://github\.com/ansible\-community/antsibull\-changelog/pull/82)\)\.

<a id="bugfixes-2"></a>
### Bugfixes

* Mark rstcheck 4\.x and 5\.x as compatible\. Support rstcheck 6\.x as well \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/81](https\://github\.com/ansible\-community/antsibull\-changelog/pull/81)\)\.

<a id="v0-15-0"></a>
## v0\.15\.0

<a id="release-summary-10"></a>
### Release Summary

Feature release\.

<a id="minor-changes-7"></a>
### Minor Changes

* Add <code>changelogs/changelog\.yaml</code> file format linting subcommand that was previously part of antsibull\-lint \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/76](https\://github\.com/ansible\-community/antsibull\-changelog/pull/76)\, [https\://github\.com/ansible\-community/antsibull/issues/410](https\://github\.com/ansible\-community/antsibull/issues/410)\)\.

<a id="v0-14-0"></a>
## v0\.14\.0

<a id="release-summary-11"></a>
### Release Summary

Feature release that will speed up the release process with ansible\-core 2\.13\.

<a id="minor-changes-8"></a>
### Minor Changes

* The internal <code>changelog\.yaml</code> linting API allows to use <code>packaging\.version\.Version</code> for version numbers instead of semantic versioning \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/73](https\://github\.com/ansible\-community/antsibull\-changelog/pull/73)\)\.
* Use the new <code>\-\-metadata\-dump</code> option for ansible\-core 2\.13\+ to quickly dump and extract all module/plugin <code>version\_added</code> values for the collection \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/72](https\://github\.com/ansible\-community/antsibull\-changelog/pull/72)\)\.

<a id="v0-13-0"></a>
## v0\.13\.0

<a id="release-summary-12"></a>
### Release Summary

This release makes changelog building more reliable\.

<a id="minor-changes-9"></a>
### Minor Changes

* Always lint fragments before releasing \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/65](https\://github\.com/ansible\-community/antsibull\-changelog/issues/65)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/67](https\://github\.com/ansible\-community/antsibull\-changelog/pull/67)\)\.

<a id="bugfixes-3"></a>
### Bugfixes

* Fix issues with module namespaces when symlinks appear in the path to the temp directory \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/68](https\://github\.com/ansible\-community/antsibull\-changelog/issues/68)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/69](https\://github\.com/ansible\-community/antsibull\-changelog/pull/69)\)\.
* Stop mentioning <code>galaxy\.yaml</code> instead of <code>galaxy\.yml</code> in some error messages \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/66](https\://github\.com/ansible\-community/antsibull\-changelog/pull/66)\)\.

<a id="v0-12-0"></a>
## v0\.12\.0

<a id="release-summary-13"></a>
### Release Summary

New feature release which supports other projects than ansible\-core and Ansible collections\.

<a id="minor-changes-10"></a>
### Minor Changes

* Support changelogs for other projects than ansible\-core/\-base and Ansible collections \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/60](https\://github\.com/ansible\-community/antsibull\-changelog/pull/60)\)\.

<a id="bugfixes-4"></a>
### Bugfixes

* Fix prerelease collapsing when <code>use\_semantic\_versioning</code> is set to <code>true</code> for ansible\-core\.

<a id="v0-11-0"></a>
## v0\.11\.0

<a id="minor-changes-11"></a>
### Minor Changes

* When using ansible\-core 2\.11 or newer\, will now detect new roles with argument spec\. We only consider the <code>main</code> entrypoint of roles\.

<a id="bugfixes-5"></a>
### Bugfixes

* When subdirectories of <code>modules</code> are used in ansible\-base/ansible\-core\, the wrong module name was passed to <code>ansible\-doc</code> when <code>\-\-use\-ansible\-doc</code> was not used\.

<a id="v0-10-0"></a>
## v0\.10\.0

<a id="minor-changes-12"></a>
### Minor Changes

* The new <code>\-\-cummulative\-release</code> option for <code>antsibull\-changelog release</code> allows to add all plugins and objects to a release since whose <code>version\_added</code> is later than the previous release version \(or ancestor if there was no previous release\)\, and at latest the current release version\. This is needed for major releases of <code>community\.general</code> and similarly organized collections\.
* Will now print a warning when a release is made where the no <code>prelude\_section\_name</code> section \(default\: <code>release\_summary</code>\) appears\.

<a id="bugfixes-6"></a>
### Bugfixes

* Make sure that the plugin caching inside ansible\-base/\-core works without <code>\-\-use\-ansible\-doc</code>\.

<a id="v0-9-0"></a>
## v0\.9\.0

<a id="major-changes-1"></a>
### Major Changes

* Add support for reporting new playbooks and roles in collections\.
* Add support for special changelog fragment sections which add new plugins and/or objects to the changelog for this version\. This is mainly useful for <code>test</code> and <code>filter</code> plugins\, and for <code>playbook</code> and <code>role</code> objects\, which are not yet automatically detected and mentioned in <code>changelogs/changelog\.yaml</code> or the generated RST changelog\.

  The format of these sections and their content is as follows\:

  ```
  ---
  add plugin.filter:
    - name: to_time_unit
      description: Converts a time expression to a given unit
    - name: to_seconds
      description: Converts a time expression to seconds
  add object.role:
    - name: nginx
      description: The most awesome nginx installation role ever
  add object.playbook:
    - name: wipe_server
      description: Totally wipes a server
  ```

  For every entry\, a list of plugins \(section <code>add plugin\.xxx</code>\) or objects \(section <code>add object\.xxx</code>\) of the given type \(<code>filter</code>\, <code>test</code> for plugins\, <code>playbook</code>\, <code>role</code> for objects\) will be added\. Every plugin or object has a short name as well as a short description\. These fields correspond to the module/plugin name and the <code>short\_description</code> field of the <code>DOCUMENTATION</code> block of modules and documentable plugins\.

<a id="minor-changes-13"></a>
### Minor Changes

* Add <code>\-\-update\-existing</code> option for <code>antsibull\-changelog release</code>\, which allows to update the current release\'s release date and \(if relevant\) codename instead of simply reporting that the release already exists\.

<a id="breaking-changes--porting-guide-1"></a>
### Breaking Changes / Porting Guide

* The new option <code>prevent\_known\_fragments</code> with default value being the value of <code>keep\_fragments</code> allows to control whether fragments with names that already appeared in the past are ignored or not\. The new behavior happens if <code>keep\_fragments\=false</code>\, and is less surprising to users \(see [https\://github\.com/ansible\-community/antsibull\-changelog/issues/46](https\://github\.com/ansible\-community/antsibull\-changelog/issues/46)\)\. Changelogs with <code>keep\_fragments\=true</code>\, like the ansible\-base/ansible\-core changelog\, are not affected\.

<a id="v0-8-1"></a>
## v0\.8\.1

<a id="bugfixes-7"></a>
### Bugfixes

* Fixed error on generating changelogs when using the trivial section\.

<a id="v0-8-0"></a>
## v0\.8\.0

<a id="minor-changes-14"></a>
### Minor Changes

* Allow to not save a changelog on release when using API\.
* Allow to sanitize changelog data on load/save\. This means that unknown information will be removed\, and bad information will be stripped\. This will be enabled in newly created changelog configs\, but is disabled for backwards compatibility\.

<a id="v0-7-0"></a>
## v0\.7\.0

<a id="minor-changes-15"></a>
### Minor Changes

* A new config option\, <code>ignore\_other\_fragment\_extensions</code> allows for configuring whether only <code>\.yaml</code> and <code>\.yml</code> files are used \(as mandated by the <code>ansible\-test sanity \-\-test changelog</code> test\)\. The default value for existing configurations is <code>false</code>\, and for new configurations <code>true</code>\.
* Allow to use semantic versioning also for Ansible\-base with the <code>use\_semantic\_versioning</code> configuration setting\.
* Refactoring changelog generation code to provide all preludes \(release summaries\) in changelog entries\, and provide generic functionality to extract a grouped list of versions\. These changes are mainly for the antsibull project\.

<a id="v0-6-0"></a>
## v0\.6\.0

<a id="minor-changes-16"></a>
### Minor Changes

* New changelog configurations place the <code>CHANGELOG\.rst</code> file by default in the top\-level directory\, and not in <code>changelogs/</code>\.
* The config option <code>archive\_path\_template</code> allows to move fragments into an archive directory when <code>keep\_fragments</code> is set to <code>false</code>\.
* The option <code>use\_fqcn</code> \(set to <code>true</code> in new configurations\) allows to use FQCN for new plugins and modules\.

<a id="v0-5-0"></a>
## v0\.5\.0

<a id="minor-changes-17"></a>
### Minor Changes

* The internal changelog generator code got more flexible to help antsibull generate Ansible porting guides\.

<a id="v0-4-0"></a>
## v0\.4\.0

<a id="minor-changes-18"></a>
### Minor Changes

* Allow to enable or disable flatmapping via <code>config\.yaml</code>\.

<a id="bugfixes-8"></a>
### Bugfixes

* Fix bad module namespace detection when collection was symlinked into Ansible\'s collection search path\. This also allows to add releases to collections which are not installed in a way that Ansible finds them\.

<a id="v0-3-1"></a>
## v0\.3\.1

<a id="bugfixes-9"></a>
### Bugfixes

* Do not fail when <code>changelogs/fragments</code> does not exist\. Simply assume there are no fragments in that case\.
* Improve behavior when <code>changelogs/config\.yaml</code> is not a dictionary\, or does not contain <code>sections</code>\.
* Improve error message when <code>\-\-is\-collection</code> is specified and <code>changelogs/config\.yaml</code> cannot be found\, or when the <code>lint</code> subcommand is used\.

<a id="v0-3-0"></a>
## v0\.3\.0

<a id="minor-changes-19"></a>
### Minor Changes

* Allow to pass path to ansible\-doc binary via <code>\-\-ansible\-doc\-bin</code>\.
* Changelog generator can be ran via <code>python \-m antsibull\_changelog</code>\.
* Use <code>ansible\-doc</code> instead of <code>/path/to/checkout/bin/ansible\-doc</code> when being run in ansible\-base checkouts\.

<a id="v0-2-1"></a>
## v0\.2\.1

<a id="bugfixes-10"></a>
### Bugfixes

* Allow to enumerate plugins/modules with ansible\-doc by specifying <code>\-\-use\-ansible\-doc</code>\.

<a id="v0-2-0"></a>
## v0\.2\.0

<a id="minor-changes-20"></a>
### Minor Changes

* Added more testing\.
* Fix internal API for ACD changelog generation \(pruning and concatenation of changelogs\)\.
* Improve error handling\.
* Improve reStructuredText creation when new modules with and without namespace exist at the same time\.
* Title generation improved \(remove superfluous space\)\.
* Use PyYAML C loader/dumper if available\.
* <code>lint</code> subcommand no longer requires specification whether it is run inside a collection or not \(if usual indicators are absent\)\.

<a id="v0-1-0"></a>
## v0\.1\.0

<a id="release-summary-14"></a>
### Release Summary

Initial release as antsibull\-changelog\. The Ansible Changelog Tool has originally been developed by \@mattclay in [the ansible/ansible](https\://github\.com/ansible/ansible/blob/stable\-2\.9/packaging/release/changelogs/changelog\.py) repository for Ansible itself\. It has been extended in [felixfontein/ansible\-changelog](https\://github\.com/felixfontein/ansible\-changelog/) and [ansible\-community/antsibull](https\://github\.com/ansible\-community/antsibull/) to work with collections\, until it was moved to its current location [ansible\-community/antsibull\-changelog](https\://github\.com/ansible\-community/antsibull\-changelog/)\.
