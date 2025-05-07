# Ansible Changelog Tool Release Notes

<a id="v0-34-0"></a>
## v0\.34\.0

<a id="release-summary"></a>
### Release Summary

Feature release for antsibull\-build\.

<a id="minor-changes"></a>
### Minor Changes

* The <code>RSTDocumentRenderer</code> API now allows to configure section underlines\. This is needed to fix the Ansible 12 porting guide \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/203](https\://github\.com/ansible\-community/antsibull\-changelog/pull/203)\)\.

<a id="v0-33-0"></a>
## v0\.33\.0

<a id="release-summary-1"></a>
### Release Summary

Maintenance release for fixing / deprecating certain boolean options\.

<a id="breaking-changes--porting-guide"></a>
### Breaking Changes / Porting Guide

* The <code>\-\-strict</code> option of the <code>lint\-changelog\-yaml</code> subcommand no longer expects a parameter\. It now matches what was documented \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/195](https\://github\.com/ansible\-community/antsibull\-changelog/issues/195)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/196](https\://github\.com/ansible\-community/antsibull\-changelog/pull/196)\)\.

<a id="deprecated-features"></a>
### Deprecated Features

* The boolean valued options <code>\-\-is\-collection</code> and <code>\-\-collection\-flatmap</code> will likely change to proper flags \(<code>\-\-flag</code> and <em class="title-reference">\-\-no\-flag\`</em> instead of <code>\-\-flag true</code>/<code>\-\-flag false</code>\) in the near future\. If you are using these options and want them to not change\, or have other suggestions\, please [create an issue in the antsibull\-changelog repository](https\://github\.com/ansible\-community/antsibull\-changelog/issues/new) \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/199](https\://github\.com/ansible\-community/antsibull\-changelog/pull/199)\)\.

<a id="v0-32-0"></a>
## v0\.32\.0

<a id="release-summary-2"></a>
### Release Summary

Feature release\.

<a id="major-changes"></a>
### Major Changes

* The new configuration setting <code>output</code> allows to configure more precisely which changelog files are generated and how they are formatted \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/190](https\://github\.com/ansible\-community/antsibull\-changelog/issues/190)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/194](https\://github\.com/ansible\-community/antsibull\-changelog/pull/194)\)\.

<a id="minor-changes-1"></a>
### Minor Changes

* Antsibull\-changelog now depends on Pydantic 2 \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/193](https\://github\.com/ansible\-community/antsibull\-changelog/pull/193)\)\.
* Antsibull\-changelog now uses Pydantic to parse and validate the config\. This means that validation is more strict than before and might reject configs that were incorrect\, but still got accepted somehow \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/193](https\://github\.com/ansible\-community/antsibull\-changelog/pull/193)\)\.

<a id="breaking-changes--porting-guide-1"></a>
### Breaking Changes / Porting Guide

* When using antsibull\-changelog as a library\, <code>ChangelogConfig</code>\'s constructor should no longer be called directly\. Instead\, use the class method <code>ChangelogConfig\.parse\(\)</code>\, which has the same signature than the previous constructor\, except that <code>ignore\_is\_other\_project</code> now must be a keyword parameter \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/193](https\://github\.com/ansible\-community/antsibull\-changelog/pull/193)\)\.
* When using antsibull\-changelog as a library\, <code>rendering\.changelog\.generate\_changelog\(\)</code> now needs a <code>ChangelogOutput</code> object instead of the <code>document\_format\: TextFormat</code> parameter\, and the <code>config</code> and <code>changelog\_path</code> parameters have been removed \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/194](https\://github\.com/ansible\-community/antsibull\-changelog/pull/194)\)\.
* When using the <code>\-\-output</code> argument for <code>antsibull\-changelog generate</code>\, the generated changelog\'s title will not contain any parts of the version number\. If you need this\, [please create an issue](https\://github\.com/ansible\-community/antsibull\-changelog/issues/new) \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/194](https\://github\.com/ansible\-community/antsibull\-changelog/pull/194)\)\.

<a id="deprecated-features-1"></a>
### Deprecated Features

* The configuration settings <code>changelog\_filename\_template</code>\, <code>changelog\_filename\_version\_depth</code>\, and <code>output\_formats</code> are deprecated and will eventually be removed\. Use the new setting <code>output</code> instead\. Note that there are no runtime warnings right now\. If the time to remove them comes nearer\, there will be runtime warnings for a longer time first before they are actually removed \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/194](https\://github\.com/ansible\-community/antsibull\-changelog/pull/194)\)\.

<a id="removed-features-previously-deprecated"></a>
### Removed Features \(previously deprecated\)

* Python API\: remove <code>antsibull\_changelog\.rst</code> module \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/183](https\://github\.com/ansible\-community/antsibull\-changelog/pull/183)\)\.
* Python API\: remove constructor arguments <code>plugins</code> and <code>fragments</code> from class <code>ChangelogGenerator</code> in <code>antsibull\_changelog\.rendering\.changelog</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/183](https\://github\.com/ansible\-community/antsibull\-changelog/pull/183)\)\.
* Python API\: remove method <code>ChangelogEntry\.add\_section\_content</code>\, class <code>ChangelogGenerator</code>\, and function <code>generate\_changelog</code> from <code>antsibull\_changelog\.changelog\_generator</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/183](https\://github\.com/ansible\-community/antsibull\-changelog/pull/183)\)\.
* When using antsibull\-changelog as a library\, the fields <code>changelog\_filename\_template</code>\, <code>changelog\_filename\_version\_depth</code>\, and <code>output\_formats</code> are no longer available in <code>ChangelogConfig</code>\. Use <code>output</code> instead \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/194](https\://github\.com/ansible\-community/antsibull\-changelog/pull/194)\)\.

<a id="v0-31-2"></a>
## v0\.31\.2

<a id="release-summary-3"></a>
### Release Summary

Bugfix release\.

<a id="bugfixes"></a>
### Bugfixes

* When linting found RST problems with rstcheck\, the error messages were reduced to a single letter \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/188](https\://github\.com/ansible\-community/antsibull\-changelog/pull/188)\)\.

<a id="v0-31-1"></a>
## v0\.31\.1

<a id="release-summary-4"></a>
### Release Summary

Bugfix release for ansible\-core\.

<a id="bugfixes-1"></a>
### Bugfixes

* Fix <code>namespace</code> extraction for ansible\-core modules \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/184](https\://github\.com/ansible\-community/antsibull\-changelog/issues/184)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/185](https\://github\.com/ansible\-community/antsibull\-changelog/pull/185)\)\.

<a id="v0-31-0"></a>
## v0\.31\.0

<a id="release-summary-5"></a>
### Release Summary

Feature release\.

<a id="minor-changes-2"></a>
### Minor Changes

* Add <code>\-\-strict</code> parameter to the <code>lint\-changelog\-yaml</code> subcommand to also check for extra fields that should not be there \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/182](https\://github\.com/ansible\-community/antsibull\-changelog/pull/182)\)\.
* Declare support for Python 3\.13 \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/180](https\://github\.com/ansible\-community/antsibull\-changelog/pull/180)\)\.
* Python API\: allow to extract extra data when loading changelog files\, and allow to insert extra data when saving \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/181](https\://github\.com/ansible\-community/antsibull\-changelog/pull/181)\)\.
* Python API\: allow to preprocess changelog\.yaml before linting \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/181](https\://github\.com/ansible\-community/antsibull\-changelog/pull/181)\)\.

<a id="breaking-changes--porting-guide-2"></a>
### Breaking Changes / Porting Guide

* More internal code related to the old changelog format has been removed\. This only potentially affects other projects which consume antsibull\-changelog as a library\. The sister antsibull projects antsibull\-build and antsibull\-docs might only be affected in older versions\. <strong>Users of the antsibull\-changelog CLI tool are not affected by this change</strong> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/179](https\://github\.com/ansible\-community/antsibull\-changelog/pull/179)\)\.

<a id="v0-30-0"></a>
## v0\.30\.0

<a id="release-summary-6"></a>
### Release Summary

Feature release\.

<a id="minor-changes-3"></a>
### Minor Changes

* Allow to configure the used VCS in <code>changelogs/config\.yml</code>\. Valid choices are <code>none</code> \(default\)\, <code>git</code>\, or <code>auto</code>\. If set to <code>git</code>\, or <code>auto</code> detects that the project is part of a Git repository\, only non\-ignored files will be copied to a temporary directory when trying to load information on Ansible modules\, plugins and roles \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/172](https\://github\.com/ansible\-community/antsibull\-changelog/issues/172)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/175](https\://github\.com/ansible\-community/antsibull\-changelog/pull/175)\)\.
* Antsibull\-changelog now depends on the new package antsibull\-docutils\. This should not have any visible impact\, expect potentially improved MarkDown output \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/174](https\://github\.com/ansible\-community/antsibull\-changelog/pull/174)\)\.
* Antsibull\-changelog now depends on the new project antsibull\-fileutils \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/176](https\://github\.com/ansible\-community/antsibull\-changelog/pull/176)\)\.
* If you are using [argcomplete](https\://pypi\.org/project/argcomplete/) global completion\, you can now tab\-complete <code>antsibull\-changelog</code> command lines\. See [Activating global completion](https\://pypi\.org/project/argcomplete/\#activating\-global\-completion) in the argcomplete README for how to enable tab completion globally\. This will also tab\-complete Ansible commands such as <code>ansible\-playbook</code> and <code>ansible\-test</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/173](https\://github\.com/ansible\-community/antsibull\-changelog/pull/173)\)\.

<a id="v0-29-0"></a>
## v0\.29\.0

<a id="release-summary-7"></a>
### Release Summary

Feature release\.

<a id="minor-changes-4"></a>
### Minor Changes

* Add a <code>reformat</code> command that reformats <code>changelogs/changelog\.yaml</code> to the current settings of <code>changelogs/config\.yaml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/169](https\://github\.com/ansible\-community/antsibull\-changelog/pull/169)\)\.
* Adds a new configuration option <code>changelog\_sort</code>\. This option allows sorting of changelog entries in <code>changelogs/changelog\.yaml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/165](https\://github\.com/ansible\-community/antsibull\-changelog/pull/165)\)\.
* Replaces numbers with constants for return codes \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/77](https\://github\.com/ansible\-community/antsibull\-changelog/issues/77)\)\.

<a id="removed-features-previously-deprecated-1"></a>
### Removed Features \(previously deprecated\)

* Removes support for the deprecated classic changelog format\. <code>changes\_format</code> must now be present and set to <code>combined</code> for ansible\-core usage\, and the value <code>classic</code> is no longer allowed \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/137](https\://github\.com/ansible\-community/antsibull\-changelog/issues/137)\)\.

<a id="bugfixes-2"></a>
### Bugfixes

* Remove Python version check that was checking for Python \>\= 3\.6 \(instead of \>\= 3\.9\)\. This check is not really necessary since <code>pyproject\.toml</code> declares <code>requires\-python</code>\, and old enough Python versions where pip does not know about <code>requires\-python</code> will not load antsibull\-changelog due to syntax errors anyway \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/167](https\://github\.com/ansible\-community/antsibull\-changelog/pull/167)\)\.

<a id="v0-28-0"></a>
## v0\.28\.0

<a id="release-summary-8"></a>
### Release Summary

Feature release\.

<a id="minor-changes-5"></a>
### Minor Changes

* There is now an option <code>changelog\_nice\_yaml</code> to prepend the YAML document start
  marker <code>\-\-\-</code> to the header of the <code>changelogs/changelog\.yaml</code> file\, and to increases
  indentation level on list items\. This makes the file pass ansible\-lint
  \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/91](https\://github\.com/ansible\-community/antsibull\-changelog/issues/91)\,
  [https\://github\.com/ansible\-community/antsibull\-changelog/issues/152](https\://github\.com/ansible\-community/antsibull\-changelog/issues/152)\,
  [https\://github\.com/ansible\-community/antsibull\-changelog/pull/160](https\://github\.com/ansible\-community/antsibull\-changelog/pull/160)\)\.

<a id="v0-27-0"></a>
## v0\.27\.0

<a id="release-summary-9"></a>
### Release Summary

Feature release\.

<a id="minor-changes-6"></a>
### Minor Changes

* Adds period where needed at end of new plugin short descriptions\. Controlled by the <code>add\_plugin\_period</code> option in the config file \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/87](https\://github\.com/ansible\-community/antsibull\-changelog/issues/87)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/162](https\://github\.com/ansible\-community/antsibull\-changelog/pull/162)\)\.

<a id="v0-26-0"></a>
## v0\.26\.0

<a id="release-summary-10"></a>
### Release Summary

Feature release\.

<a id="minor-changes-7"></a>
### Minor Changes

* The Markdown output format is now compatible with [python\-markdown](https\://python\-markdown\.github\.io/) and [mkdocs](https\://www\.mkdocs\.org/)\, as long as the [pymdownx\.escapeall](https\://facelessuser\.github\.io/pymdown\-extensions/extensions/escapeall/) extension is enabled \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/153](https\://github\.com/ansible\-community/antsibull\-changelog/pull/153)\)\.

<a id="v0-25-0"></a>
## v0\.25\.0

<a id="release-summary-11"></a>
### Release Summary

Bugfix and feature release\.

<a id="minor-changes-8"></a>
### Minor Changes

* Add <code>\-\-version</code> flag to print package version and exit \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/147](https\://github\.com/ansible\-community/antsibull\-changelog/pull/147)\)\.

<a id="bugfixes-3"></a>
### Bugfixes

* When multiple output formats are defined and <code>antsibull\-changelog generate</code> is used with both <code>\-\-output</code> and <code>\-\-output\-format</code>\, an error was displayed that <code>\-\-output\-format</code> must be specified \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/149](https\://github\.com/ansible\-community/antsibull\-changelog/issues/149)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/151](https\://github\.com/ansible\-community/antsibull\-changelog/pull/151)\)\.

<a id="v0-24-0"></a>
## v0\.24\.0

<a id="release-summary-12"></a>
### Release Summary

Feature release which now allows to output MarkDown\.

<a id="minor-changes-9"></a>
### Minor Changes

* Allow automatically retrieving package version for hatch projects with the <code>hatch version</code> command \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/141](https\://github\.com/ansible\-community/antsibull\-changelog/pull/141)\)\.
* Allow to render changelogs as MarkDown\. The output formats written can be controlled with the <code>output\_formats</code> option in the config file \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/139](https\://github\.com/ansible\-community/antsibull\-changelog/pull/139)\)\.
* Officially support Python 3\.12 \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/134](https\://github\.com/ansible\-community/antsibull\-changelog/pull/134)\)\.

<a id="deprecated-features-2"></a>
### Deprecated Features

* Some code in <code>antsibull\_changelog\.changelog\_entry</code> has been deprecated\, and the <code>antsibull\_changelog\.rst</code> module has been deprecated completely\. If you use them in your own code\, please take a look at the [PR deprecating them](https\://github\.com/ansible\-community/antsibull\-changelog/pull/139) for information on how to stop using them \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/139](https\://github\.com/ansible\-community/antsibull\-changelog/pull/139)\)\.

<a id="v0-23-0"></a>
## v0\.23\.0

<a id="release-summary-13"></a>
### Release Summary

Feature release\.

<a id="minor-changes-10"></a>
### Minor Changes

* Allow to generate changelog for a specific version \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/130](https\://github\.com/ansible\-community/antsibull\-changelog/pull/130)\)\.
* Allow to generate only the last entry without preamble with the <code>generate</code> command \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/131](https\://github\.com/ansible\-community/antsibull\-changelog/pull/131)\)\.
* Allow to write <code>generate</code> output to a user\-provided file \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/131](https\://github\.com/ansible\-community/antsibull\-changelog/pull/131)\)\.

<a id="v0-22-0"></a>
## v0\.22\.0

<a id="release-summary-14"></a>
### Release Summary

New feature release

<a id="minor-changes-11"></a>
### Minor Changes

* Add <code>antsibull\-changelog\-lint</code> and <code>antsibull\-changelog\-lint\-changelog\-yaml</code> pre\-commit\.com hooks \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/125](https\://github\.com/ansible\-community/antsibull\-changelog/pull/125)\)\.
* Add <code>toml</code> extra to pull in a toml parser to use to guess the version based on <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/126](https\://github\.com/ansible\-community/antsibull\-changelog/pull/126)\)\.

<a id="v0-21-0"></a>
## v0\.21\.0

<a id="release-summary-15"></a>
### Release Summary

Maintenance release with a deprecation\.

<a id="deprecated-features-3"></a>
### Deprecated Features

* Support for <code>classic</code> changelogs is deprecated and will be removed soon\. If you need to build changelogs for Ansible 2\.9 or before\, please use an older version \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/123](https\://github\.com/ansible\-community/antsibull\-changelog/pull/123)\)\.

<a id="v0-20-0"></a>
## v0\.20\.0

<a id="release-summary-16"></a>
### Release Summary

Bugfix and maintenance release using a new build system\.

<a id="major-changes-1"></a>
### Major Changes

* Change pyproject build backend from <code>poetry\-core</code> to <code>hatchling</code>\. <code>pip install antsibull</code> works exactly the same as before\, but some users may be affected depending on how they build/install the project \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/109](https\://github\.com/ansible\-community/antsibull\-changelog/pull/109)\)\.

<a id="bugfixes-4"></a>
### Bugfixes

* When releasing ansible\-core and only one of <code>\-\-version</code> and <code>\-\-codename</code> is supplied\, error out instead of ignoring the supplied value \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/104](https\://github\.com/ansible\-community/antsibull\-changelog/issues/104)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/105](https\://github\.com/ansible\-community/antsibull\-changelog/pull/105)\)\.

<a id="v0-19-0"></a>
## v0\.19\.0

<a id="release-summary-17"></a>
### Release Summary

Feature release\.

<a id="minor-changes-12"></a>
### Minor Changes

* Allow to extract other project versions for JavaScript / TypeScript projects from <code>package\.json</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/100](https\://github\.com/ansible\-community/antsibull\-changelog/pull/100)\)\.
* Allow to extract other project versions for Python projects from PEP 621 conformant <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/100](https\://github\.com/ansible\-community/antsibull\-changelog/pull/100)\)\.
* Support Python 3\.11\'s <code>tomllib</code> to load <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/101](https\://github\.com/ansible\-community/antsibull\-changelog/issues/101)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/102](https\://github\.com/ansible\-community/antsibull\-changelog/pull/102)\)\.
* Use more specific exceptions than <code>Exception</code> for some cases in internal code \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/103](https\://github\.com/ansible\-community/antsibull\-changelog/pull/103)\)\.

<a id="v0-18-0"></a>
## v0\.18\.0

<a id="release-summary-18"></a>
### Release Summary

Maintenance release that drops support for older Python versions\.

<a id="breaking-changes--porting-guide-3"></a>
### Breaking Changes / Porting Guide

* Drop support for Python 3\.6\, 3\.7\, and 3\.8 \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/93](https\://github\.com/ansible\-community/antsibull\-changelog/pull/93)\)\.

<a id="v0-17-0"></a>
## v0\.17\.0

<a id="release-summary-19"></a>
### Release Summary

Feature release for ansible\-core\.

<a id="minor-changes-13"></a>
### Minor Changes

* Only allow a <code>trival</code> section in the ansible\-core/ansible\-base changelog when explicitly configured \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/90](https\://github\.com/ansible\-community/antsibull\-changelog/pull/90)\)\.

<a id="v0-16-0"></a>
## v0\.16\.0

<a id="release-summary-20"></a>
### Release Summary

Feature and bugfix release\.

<a id="minor-changes-14"></a>
### Minor Changes

* Allow to extract other project versions for Python poetry projects from <code>pyproject\.toml</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/80](https\://github\.com/ansible\-community/antsibull\-changelog/pull/80)\)\.
* The files in the source repository now follow the [REUSE Specification](https\://reuse\.software/spec/)\. The only exceptions are changelog fragments in <code>changelogs/fragments/</code> \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/82](https\://github\.com/ansible\-community/antsibull\-changelog/pull/82)\)\.

<a id="bugfixes-5"></a>
### Bugfixes

* Mark rstcheck 4\.x and 5\.x as compatible\. Support rstcheck 6\.x as well \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/81](https\://github\.com/ansible\-community/antsibull\-changelog/pull/81)\)\.

<a id="v0-15-0"></a>
## v0\.15\.0

<a id="release-summary-21"></a>
### Release Summary

Feature release\.

<a id="minor-changes-15"></a>
### Minor Changes

* Add <code>changelogs/changelog\.yaml</code> file format linting subcommand that was previously part of antsibull\-lint \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/76](https\://github\.com/ansible\-community/antsibull\-changelog/pull/76)\, [https\://github\.com/ansible\-community/antsibull/issues/410](https\://github\.com/ansible\-community/antsibull/issues/410)\)\.

<a id="v0-14-0"></a>
## v0\.14\.0

<a id="release-summary-22"></a>
### Release Summary

Feature release that will speed up the release process with ansible\-core 2\.13\.

<a id="minor-changes-16"></a>
### Minor Changes

* The internal <code>changelog\.yaml</code> linting API allows to use <code>packaging\.version\.Version</code> for version numbers instead of semantic versioning \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/73](https\://github\.com/ansible\-community/antsibull\-changelog/pull/73)\)\.
* Use the new <code>\-\-metadata\-dump</code> option for ansible\-core 2\.13\+ to quickly dump and extract all module/plugin <code>version\_added</code> values for the collection \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/72](https\://github\.com/ansible\-community/antsibull\-changelog/pull/72)\)\.

<a id="v0-13-0"></a>
## v0\.13\.0

<a id="release-summary-23"></a>
### Release Summary

This release makes changelog building more reliable\.

<a id="minor-changes-17"></a>
### Minor Changes

* Always lint fragments before releasing \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/65](https\://github\.com/ansible\-community/antsibull\-changelog/issues/65)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/67](https\://github\.com/ansible\-community/antsibull\-changelog/pull/67)\)\.

<a id="bugfixes-6"></a>
### Bugfixes

* Fix issues with module namespaces when symlinks appear in the path to the temp directory \([https\://github\.com/ansible\-community/antsibull\-changelog/issues/68](https\://github\.com/ansible\-community/antsibull\-changelog/issues/68)\, [https\://github\.com/ansible\-community/antsibull\-changelog/pull/69](https\://github\.com/ansible\-community/antsibull\-changelog/pull/69)\)\.
* Stop mentioning <code>galaxy\.yaml</code> instead of <code>galaxy\.yml</code> in some error messages \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/66](https\://github\.com/ansible\-community/antsibull\-changelog/pull/66)\)\.

<a id="v0-12-0"></a>
## v0\.12\.0

<a id="release-summary-24"></a>
### Release Summary

New feature release which supports other projects than ansible\-core and Ansible collections\.

<a id="minor-changes-18"></a>
### Minor Changes

* Support changelogs for other projects than ansible\-core/\-base and Ansible collections \([https\://github\.com/ansible\-community/antsibull\-changelog/pull/60](https\://github\.com/ansible\-community/antsibull\-changelog/pull/60)\)\.

<a id="bugfixes-7"></a>
### Bugfixes

* Fix prerelease collapsing when <code>use\_semantic\_versioning</code> is set to <code>true</code> for ansible\-core\.

<a id="v0-11-0"></a>
## v0\.11\.0

<a id="minor-changes-19"></a>
### Minor Changes

* When using ansible\-core 2\.11 or newer\, will now detect new roles with argument spec\. We only consider the <code>main</code> entrypoint of roles\.

<a id="bugfixes-8"></a>
### Bugfixes

* When subdirectories of <code>modules</code> are used in ansible\-base/ansible\-core\, the wrong module name was passed to <code>ansible\-doc</code> when <code>\-\-use\-ansible\-doc</code> was not used\.

<a id="v0-10-0"></a>
## v0\.10\.0

<a id="minor-changes-20"></a>
### Minor Changes

* The new <code>\-\-cummulative\-release</code> option for <code>antsibull\-changelog release</code> allows to add all plugins and objects to a release since whose <code>version\_added</code> is later than the previous release version \(or ancestor if there was no previous release\)\, and at latest the current release version\. This is needed for major releases of <code>community\.general</code> and similarly organized collections\.
* Will now print a warning when a release is made where the no <code>prelude\_section\_name</code> section \(default\: <code>release\_summary</code>\) appears\.

<a id="bugfixes-9"></a>
### Bugfixes

* Make sure that the plugin caching inside ansible\-base/\-core works without <code>\-\-use\-ansible\-doc</code>\.

<a id="v0-9-0"></a>
## v0\.9\.0

<a id="major-changes-2"></a>
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

<a id="minor-changes-21"></a>
### Minor Changes

* Add <code>\-\-update\-existing</code> option for <code>antsibull\-changelog release</code>\, which allows to update the current release\'s release date and \(if relevant\) codename instead of simply reporting that the release already exists\.

<a id="breaking-changes--porting-guide-4"></a>
### Breaking Changes / Porting Guide

* The new option <code>prevent\_known\_fragments</code> with default value being the value of <code>keep\_fragments</code> allows to control whether fragments with names that already appeared in the past are ignored or not\. The new behavior happens if <code>keep\_fragments\=false</code>\, and is less surprising to users \(see [https\://github\.com/ansible\-community/antsibull\-changelog/issues/46](https\://github\.com/ansible\-community/antsibull\-changelog/issues/46)\)\. Changelogs with <code>keep\_fragments\=true</code>\, like the ansible\-base/ansible\-core changelog\, are not affected\.

<a id="v0-8-1"></a>
## v0\.8\.1

<a id="bugfixes-10"></a>
### Bugfixes

* Fixed error on generating changelogs when using the trivial section\.

<a id="v0-8-0"></a>
## v0\.8\.0

<a id="minor-changes-22"></a>
### Minor Changes

* Allow to not save a changelog on release when using API\.
* Allow to sanitize changelog data on load/save\. This means that unknown information will be removed\, and bad information will be stripped\. This will be enabled in newly created changelog configs\, but is disabled for backwards compatibility\.

<a id="v0-7-0"></a>
## v0\.7\.0

<a id="minor-changes-23"></a>
### Minor Changes

* A new config option\, <code>ignore\_other\_fragment\_extensions</code> allows for configuring whether only <code>\.yaml</code> and <code>\.yml</code> files are used \(as mandated by the <code>ansible\-test sanity \-\-test changelog</code> test\)\. The default value for existing configurations is <code>false</code>\, and for new configurations <code>true</code>\.
* Allow to use semantic versioning also for Ansible\-base with the <code>use\_semantic\_versioning</code> configuration setting\.
* Refactoring changelog generation code to provide all preludes \(release summaries\) in changelog entries\, and provide generic functionality to extract a grouped list of versions\. These changes are mainly for the antsibull project\.

<a id="v0-6-0"></a>
## v0\.6\.0

<a id="minor-changes-24"></a>
### Minor Changes

* New changelog configurations place the <code>CHANGELOG\.rst</code> file by default in the top\-level directory\, and not in <code>changelogs/</code>\.
* The config option <code>archive\_path\_template</code> allows to move fragments into an archive directory when <code>keep\_fragments</code> is set to <code>false</code>\.
* The option <code>use\_fqcn</code> \(set to <code>true</code> in new configurations\) allows to use FQCN for new plugins and modules\.

<a id="v0-5-0"></a>
## v0\.5\.0

<a id="minor-changes-25"></a>
### Minor Changes

* The internal changelog generator code got more flexible to help antsibull generate Ansible porting guides\.

<a id="v0-4-0"></a>
## v0\.4\.0

<a id="minor-changes-26"></a>
### Minor Changes

* Allow to enable or disable flatmapping via <code>config\.yaml</code>\.

<a id="bugfixes-11"></a>
### Bugfixes

* Fix bad module namespace detection when collection was symlinked into Ansible\'s collection search path\. This also allows to add releases to collections which are not installed in a way that Ansible finds them\.

<a id="v0-3-1"></a>
## v0\.3\.1

<a id="bugfixes-12"></a>
### Bugfixes

* Do not fail when <code>changelogs/fragments</code> does not exist\. Simply assume there are no fragments in that case\.
* Improve behavior when <code>changelogs/config\.yaml</code> is not a dictionary\, or does not contain <code>sections</code>\.
* Improve error message when <code>\-\-is\-collection</code> is specified and <code>changelogs/config\.yaml</code> cannot be found\, or when the <code>lint</code> subcommand is used\.

<a id="v0-3-0"></a>
## v0\.3\.0

<a id="minor-changes-27"></a>
### Minor Changes

* Allow to pass path to ansible\-doc binary via <code>\-\-ansible\-doc\-bin</code>\.
* Changelog generator can be ran via <code>python \-m antsibull\_changelog</code>\.
* Use <code>ansible\-doc</code> instead of <code>/path/to/checkout/bin/ansible\-doc</code> when being run in ansible\-base checkouts\.

<a id="v0-2-1"></a>
## v0\.2\.1

<a id="bugfixes-13"></a>
### Bugfixes

* Allow to enumerate plugins/modules with ansible\-doc by specifying <code>\-\-use\-ansible\-doc</code>\.

<a id="v0-2-0"></a>
## v0\.2\.0

<a id="minor-changes-28"></a>
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

<a id="release-summary-25"></a>
### Release Summary

Initial release as antsibull\-changelog\. The Ansible Changelog Tool has originally been developed by \@mattclay in [the ansible/ansible](https\://github\.com/ansible/ansible/blob/stable\-2\.9/packaging/release/changelogs/changelog\.py) repository for Ansible itself\. It has been extended in [felixfontein/ansible\-changelog](https\://github\.com/felixfontein/ansible\-changelog/) and [ansible\-community/antsibull](https\://github\.com/ansible\-community/antsibull/) to work with collections\, until it was moved to its current location [ansible\-community/antsibull\-changelog](https\://github\.com/ansible\-community/antsibull\-changelog/)\.
