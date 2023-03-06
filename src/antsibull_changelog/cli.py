# Author: Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or
# https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2020, Ansible Project

"""
Entrypoint to the antsibull-changelog script.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
import traceback
from collections.abc import Callable
from typing import Any, cast

try:
    import argcomplete
    HAS_ARGCOMPLETE = True
except ImportError:
    HAS_ARGCOMPLETE = False

try:
    import toml
    HAS_TOML = True
except ImportError:
    HAS_TOML = False

try:
    import tomli
    HAS_TOMLI = True
except ImportError:
    HAS_TOMLI = False

from .ansible import get_ansible_release
from .changelog_generator import generate_changelog
from .changes import ChangesBase, add_release, load_changes
from .config import ChangelogConfig, CollectionDetails, PathsConfig
from .errors import ChangelogError
from .fragment import ChangelogFragment, ChangelogFragmentLinter, load_fragments
from .lint import lint_changelog_yaml
from .logger import LOGGER, setup_logger
from .plugins import PluginDescription, load_plugins


def set_paths(force: str | None = None,
              is_collection: bool | None = None,
              ansible_doc_bin: str | None = None,
              is_other_project: bool | None = None,
              fallback_to_other_project: bool = False) -> PathsConfig:
    """
    Create ``PathsConfig``.

    :arg force: If provided, create a collection path config for the given path.
                Otherwise, detect configuration.
    :arg is_collection: Override detection of whether the tool is run in a collection
                        or in ansible-core.
    :arg ansible_doc_bin: Override path to ansible-doc.
    :arg is_other_project: Override detection of whether the tool is an other project
    :arg fallback_to_other_project: Fall back to other project
    """
    if force is not None:
        if is_other_project is True:
            return PathsConfig.force_other(force, ansible_doc_bin=ansible_doc_bin)
        if is_collection is False:
            return PathsConfig.force_ansible(force, ansible_doc_bin=ansible_doc_bin)
        return PathsConfig.force_collection(force, ansible_doc_bin=ansible_doc_bin)

    try:
        return PathsConfig.detect(is_collection=is_collection,
                                  is_other_project=is_other_project,
                                  ansible_doc_bin=ansible_doc_bin,
                                  fallback_to_other_project=fallback_to_other_project)
    except ChangelogError:
        if is_collection is True:
            raise ChangelogError(  # pylint: disable=raise-missing-from
                "Only the 'init' command can be used outside a collection repository, "
                "or inside one without changelogs/config.yaml.")
        if is_collection is False:
            raise ChangelogError(  # pylint: disable=raise-missing-from
                "Only the 'init' command can be used outside an Ansible checkout, "
                "or inside one without changelogs/config.yaml.")
        raise ChangelogError(  # pylint: disable=raise-missing-from
            "Only the 'init' command can be used outside an Ansible checkout and outside a "
            "collection repository, or inside one without changelogs/config.yaml.\n"
            "If you are in a collection without galaxy.yml, specify `--is-collection no` "
            "on the command line.")


def parse_boolean_arg(value: Any) -> bool:
    """
    Parse a string as a boolean
    """
    if isinstance(value, bool):
        return value
    value = str(value)
    if value.lower() in ('yes', 'true'):
        return True
    if value.lower() in ('no', 'false'):
        return False
    raise argparse.ArgumentTypeError('Cannot interpret as boolean')


def create_argparser(program_name: str) -> argparse.ArgumentParser:
    """
    Create CLI argument parser.
    """
    parser = argparse.ArgumentParser(
        prog=program_name,
        description='Changelog generator and linter.')

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='increase verbosity of output')

    is_collection = argparse.ArgumentParser(add_help=False)
    is_collection.add_argument('--is-collection',
                               type=parse_boolean_arg,
                               help='override whether this is a collection or not '
                                    '(needed when galaxy.yml does not exist)')

    collection_details = argparse.ArgumentParser(add_help=False)
    collection_details.add_argument('--collection-namespace',
                                    help='set collection namespace '
                                         '(needed when galaxy.yml does not exist)')
    collection_details.add_argument('--collection-name',
                                    help='set collection name '
                                         '(needed when galaxy.yml does not exist)')
    collection_details.add_argument('--collection-flatmap',
                                    type=parse_boolean_arg,
                                    help='override collection flatmapping flag '
                                         '(needed when galaxy.yml does not exist)')

    subparsers = parser.add_subparsers(metavar='COMMAND')

    init_parser = subparsers.add_parser('init',
                                        parents=[common],
                                        help='set up changelog infrastructure for '
                                             'collection, or an other project')
    init_parser.set_defaults(func=command_init)
    init_parser.add_argument('root',
                             metavar='PROJECT_ROOT',
                             help='path to collection or project root')
    init_parser.add_argument('--is-other-project',
                             action='store_true',
                             help='project root belongs to an other project, and '
                                  'not to an Ansible collection')

    lint_parser = subparsers.add_parser('lint',
                                        parents=[common],
                                        help='check changelog fragments for syntax errors')
    lint_parser.set_defaults(func=command_lint)
    lint_parser.add_argument('fragments',
                             metavar='FRAGMENT',
                             nargs='*',
                             help='path to fragment to test')

    lint_changelog_yaml_parser = subparsers.add_parser('lint-changelog-yaml',
                                                       parents=[common],
                                                       help='check syntax of'
                                                            ' changelogs/changelog.yaml file')
    lint_changelog_yaml_parser.set_defaults(func=command_lint_changelog_yaml)
    lint_changelog_yaml_parser.add_argument('changelog_yaml_path',
                                            metavar='/path/to/changelog.yaml',
                                            help='path to changelogs/changelog.yaml')

    lint_changelog_yaml_parser.add_argument('--no-semantic-versioning', action='store_true',
                                            help='assume that use_semantic_versioning=false in the'
                                                 ' changelog config. Do not use this for Ansible'
                                                 ' collections!')

    common_build = argparse.ArgumentParser(add_help=False)
    common_build.add_argument('--reload-plugins',
                              action='store_true',
                              help='force reload of plugin cache')
    common_build.add_argument('--ansible-doc-bin',
                              help='path to ansible-doc (overrides autodetect)')
    common_build.add_argument('--use-ansible-doc',
                              action='store_true',
                              help='always use ansible-doc to find plugins')
    common_build.add_argument('--refresh',
                              action='store_true',
                              help='update existing entries from fragment files (if '
                                   'keep_fragments is true), and update plugin descriptions '
                                   '(should be combined with --reload-plugins)')
    common_build.add_argument('--refresh-plugins',
                              choices=['allow-removal', 'prevent-removal'],
                              nargs='?',
                              default=None,
                              const='allow-removal',
                              help='update plugin descriptions '
                                   '(should be combined with --reload-plugins); '
                                   'default is allow-removal')
    common_build.add_argument('--refresh-fragments',
                              choices=['without-archives', 'with-archives'],
                              nargs='?',
                              default=None,
                              const='with-archives',
                              help='update existing entries from fragment files (if '
                                   'keep_fragments is true, or for with-archives if '
                                   'archives are used); default is with-archives')

    release_parser = subparsers.add_parser('release',
                                           parents=[common, common_build,
                                                    is_collection, collection_details],
                                           help='add a new release to the change metadata')
    release_parser.set_defaults(func=command_release)
    release_parser.add_argument('--version',
                                help='override release version')
    release_parser.add_argument('--codename',
                                help='override/set release codename')
    release_parser.add_argument('--date',
                                default=str(datetime.date.today()),
                                help='override release date')
    release_parser.add_argument('--update-existing',
                                action='store_true',
                                help='if the release already exists, updates the release '
                                     'date and (if relevant) the codename')
    release_parser.add_argument('--cummulative-release',
                                action='store_true',
                                help='include all plugins/modules/... that have been added '
                                     'since the previous release / ancestor')

    generate_parser = subparsers.add_parser('generate',
                                            parents=[common, common_build,
                                                     is_collection, collection_details],
                                            help='generate the changelog')
    generate_parser.set_defaults(func=command_generate)

    if HAS_ARGCOMPLETE:
        argcomplete.autocomplete(parser)

    return parser


def load_collection_details(collection_details: CollectionDetails, args: Any):
    """
    Override collection details data with CLI args.
    """
    if args.collection_namespace is not None:
        collection_details.namespace = args.collection_namespace
    if args.collection_name is not None:
        collection_details.name = args.collection_name
    if args.collection_flatmap is not None:
        collection_details.flatmap = args.collection_flatmap


def run(args: list[str]) -> int:
    """
    Main program entry point.
    """
    verbosity = 0
    try:
        program_name = os.path.basename(args[0])
        parser = create_argparser(program_name)

        arguments = parser.parse_args(args[1:])

        if getattr(arguments, 'func', None) is None:
            parser.print_help()
            return 2

        verbosity = arguments.verbose
        setup_logger(verbosity)

        return arguments.func(arguments)
    except ChangelogError as e:
        LOGGER.error(str(e))
        if verbosity > 2:
            traceback.print_exc()
        return 5
    except SystemExit as e:
        # All cases that sys.exit is called directly or indirectly in the above
        # code (that we are aware of) always return an int.
        return cast(int, e.code)  # pyre-ignore[22]
    except Exception:  # pylint: disable=broad-except
        if verbosity > 0:
            traceback.print_exc()
        else:
            print('ERROR: Uncaught exception. Run with -v to see traceback.')
        return 1


def command_init(args: Any) -> int:
    """
    Initialize a changelog config.

    :arg args: Parsed arguments
    """
    root: str = args.root
    is_other_project: bool = args.is_other_project

    paths = set_paths(force=root, is_other_project=is_other_project)

    if not is_other_project and paths.galaxy_path is None:
        LOGGER.error('The file galaxy.yml does not exists in the collection root!')
        return 5
    LOGGER.debug('Checking for existance of "{}"', paths.config_path)
    if os.path.exists(paths.config_path):
        LOGGER.error('A configuration file already exists at "{}"!', paths.config_path)
        return 5

    collection_details = CollectionDetails(paths)

    title = 'Project'
    if not is_other_project:
        title = '{0}.{1}'.format(
            collection_details.get_namespace().title(), collection_details.get_name().title())

    config = ChangelogConfig.default(paths, collection_details, title=title)

    fragments_dir = os.path.join(paths.changelog_dir, config.notes_dir)
    try:
        os.makedirs(fragments_dir, exist_ok=True)
        print('Created fragments directory "{0}"'.format(fragments_dir))
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error('Cannot create fragments directory "{}"', fragments_dir)
        LOGGER.info('Exception: {}', str(exc))
        return 5

    try:
        config.store()
        print('Created config file "{0}"'.format(paths.config_path))
    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.error('Cannot create config file "{}"', paths.config_path)
        LOGGER.info('Exception: {}', str(exc))
        return 5

    return 0


def _determine_flatmap(collection_details: CollectionDetails,
                       config: ChangelogConfig) -> bool:
    """
    Determine whether flatmapping is used or not for the collection.
    """
    flatmap = not config.is_collection
    flatmap_ = config.flatmap
    if flatmap_ is not None:
        flatmap = flatmap_
    if config.is_collection:
        flatmap_ = collection_details.get_flatmap()
        if flatmap_ is not None:
            flatmap = flatmap_
    return flatmap


def _get_refresh_config(args: Any,
                        config: ChangelogConfig) -> tuple[str | None, str | None]:
    refresh_plugins: str | None = args.refresh_plugins
    refresh_fragments: str | None = args.refresh_fragments
    always_refresh = config.always_refresh
    if args.refresh or always_refresh == 'full':
        if refresh_plugins is None:
            refresh_plugins = 'allow-removal'
        if refresh_fragments is None:
            refresh_fragments = 'with-archives'
    if always_refresh not in ('full', 'none'):
        for part in always_refresh.split(','):
            part = part.strip()
            if part == 'plugins':
                refresh_plugins = 'allow-removal'
            elif part == 'plugins-without-removal':
                refresh_plugins = 'prevent-removal'
            elif part == 'fragments':
                refresh_fragments = 'with-archives'
            elif part == 'fragments-without-archives':
                refresh_fragments = 'without-archives'
            else:
                # pylint:disable-next=broad-exception-raised
                raise Exception(
                    'The config value always_refresh contains an invalid value "{0}"'.format(
                        part))
    return refresh_plugins, refresh_fragments


def _get_archive_loader(archive_path_template: str,
                        paths: PathsConfig,
                        config: ChangelogConfig) -> Callable[[str], list[ChangelogFragment]]:
    def load_extra_fragments(version: str) -> list[ChangelogFragment]:
        archive_path = os.path.join(
            paths.base_dir, archive_path_template.format(version=version))
        return load_fragments(paths, config, fragments_dir=archive_path)

    return load_extra_fragments


def _do_refresh(args: Any,  # pylint: disable=too-many-arguments
                paths: PathsConfig,
                collection_details: CollectionDetails,
                config: ChangelogConfig,
                changes: ChangesBase,
                plugins: list[PluginDescription] | None = None,
                fragments: list[ChangelogFragment] | None = None
                ) -> tuple[list[PluginDescription] | None, list[ChangelogFragment] | None]:

    refresh_plugins, refresh_fragments = _get_refresh_config(args, config)

    if refresh_plugins:
        if plugins is None:
            plugins = load_plugins(paths=paths,
                                   collection_details=collection_details,
                                   version=changes.latest_version,
                                   force_reload=args.reload_plugins,
                                   use_ansible_doc=args.use_ansible_doc)
        allow_removals = refresh_plugins == 'allow-removal'

        changes.update_plugins(plugins, allow_removals=allow_removals)
        changes.update_objects(plugins, allow_removals=allow_removals)

    if refresh_fragments:
        if fragments is None:
            fragments = load_fragments(paths, config)
        archive_path_template = config.archive_path_template
        has_archives = archive_path_template is not None
        with_archives = refresh_fragments == 'with-archives'

        if config.keep_fragments or (has_archives and with_archives):
            all_fragments = list(fragments)
            load_extra_fragments = None
            if with_archives and archive_path_template is not None:
                load_extra_fragments = _get_archive_loader(archive_path_template, paths, config)

            changes.update_fragments(all_fragments, load_extra_fragments=load_extra_fragments)
        else:
            LOGGER.warning('Cannot refresh changelog fragments, as keep_fragments '
                           'is false and archives are not enabled')

    if refresh_plugins or refresh_fragments:
        changes.save()

    return plugins, fragments


def _get_pyproject_toml_version(project_toml_path: str) -> str | None:
    '''
    Try to extract version from pyproject.toml.
    '''
    if not HAS_TOML and not HAS_TOMLI:
        raise ChangelogError('Need toml/tomli library to read pyproject.toml')

    with open(project_toml_path, 'r', encoding='utf-8') as f:
        data = (toml if HAS_TOML else tomli).loads(f.read())

    # PEP 621 project metadata (https://peps.python.org/pep-0621/#version)
    project_data = data.get('project')
    if isinstance(project_data, dict) and project_data.get('version'):
        return project_data.get('version')

    tool_config = data.get('tool') or {}

    # Python Poetry (https://python-poetry.org/docs/pyproject/#version)
    if 'poetry' in tool_config:
        poetry_config = tool_config['poetry']
        return poetry_config.get('version')

    return None


def _get_package_json_version(package_json_path: str) -> str | None:
    '''
    Try to extract version from package.json.
    '''
    with open(package_json_path, 'rb') as f:
        data = json.load(f)

    return data.get('version')


def _get_project_version(paths: PathsConfig) -> str | None:
    '''
    Try to extract version for other projects.
    '''
    project_toml_path = os.path.join(paths.base_dir, 'pyproject.toml')
    if os.path.isfile(project_toml_path):
        return _get_pyproject_toml_version(project_toml_path)

    package_json_path = os.path.join(paths.base_dir, 'package.json')
    if os.path.isfile(package_json_path):
        return _get_package_json_version(package_json_path)

    return None


def _get_version_and_codename(paths: PathsConfig, config: ChangelogConfig,
                              collection_details: CollectionDetails,
                              args: Any) -> tuple[str, str | None]:
    '''
    Extract version and codename for a release from arguments, autodetect them, or fail.
    '''
    version: str | None = args.version
    codename: str | None = args.codename

    if not config.is_collection and not config.is_other_project and not (version and codename):
        # Both version and codename are required for ansible-core
        try:
            return get_ansible_release()
        except ValueError:
            raise ChangelogError(  # pylint: disable=raise-missing-from
                'Cannot import ansible.release to determine version and codename')

    # Codename is not required for collections or other projects
    if version:
        return version, codename

    if config.is_collection:
        return collection_details.get_version(), codename

    # Other projects
    version = _get_project_version(paths)
    if not version:
        raise ChangelogError(
            'You need to explicitly specify the version for other projects with --version')
    return version, codename


def command_release(args: Any) -> int:
    """
    Add a new release to a changelog.

    :arg args: Parsed arguments
    """
    ansible_doc_bin: str | None = args.ansible_doc_bin
    paths = set_paths(is_collection=args.is_collection, ansible_doc_bin=ansible_doc_bin)

    date = datetime.datetime.strptime(args.date, "%Y-%m-%d").date()

    collection_details = CollectionDetails(paths)
    config = ChangelogConfig.load(paths, collection_details)

    load_collection_details(collection_details, args)

    flatmap = _determine_flatmap(collection_details, config)

    version, codename = _get_version_and_codename(paths, config, collection_details, args)

    changes = load_changes(config)

    prev_version: str | None = None
    if args.cummulative_release:
        prev_version = changes.latest_version if changes.has_release else changes.ancestor

    plugins: list[PluginDescription] | None
    fragments: list[ChangelogFragment] | None

    plugins = load_plugins(paths=paths, collection_details=collection_details,
                           version=version, force_reload=args.reload_plugins,
                           use_ansible_doc=args.use_ansible_doc)
    fragments = load_fragments(paths, config)
    lint_rc = lint_fragments(config, fragments, [])
    if lint_rc != 0:
        LOGGER.error(
            'Please fix all linting errors before releasing a new version! '
            'Use `antsibull-changelog lint` to manually lint before releasing.')
        return lint_rc

    plugins, fragments = _do_refresh(
        args, paths, collection_details, config, changes, plugins, fragments)
    add_release(
        config, changes,
        # Need cast() here because there is currently no way to mark _do_refresh so that
        # it does not convert a non-None value to None for plugins or fragments
        cast(list[PluginDescription], plugins),
        cast(list[ChangelogFragment], fragments),
        version, codename, date,
        update_existing=args.update_existing,
        prev_version=prev_version,
        objects=cast(list[PluginDescription], plugins),
    )
    generate_changelog(paths, config, changes, plugins, fragments, flatmap=flatmap)

    return 0


def command_generate(args: Any) -> int:
    """
    (Re-)generate the reStructuredText version of the changelog.

    :arg args: Parsed arguments
    """
    ansible_doc_bin: str | None = args.ansible_doc_bin
    paths = set_paths(is_collection=args.is_collection, ansible_doc_bin=ansible_doc_bin)

    collection_details = CollectionDetails(paths)
    config = ChangelogConfig.load(paths, collection_details)

    load_collection_details(collection_details, args)

    flatmap = _determine_flatmap(collection_details, config)

    changes = load_changes(config)
    if not changes.has_release:
        print('Cannot create changelog when not at least one release has been added.')
        return 5
    plugins, fragments = _do_refresh(args, paths, collection_details, config, changes, None, None)
    if args.reload_plugins and plugins is None:
        plugins = load_plugins(paths=paths, collection_details=collection_details,
                               version=changes.latest_version, force_reload=args.reload_plugins)
    generate_changelog(paths, config, changes, plugins, fragments, flatmap=flatmap)

    return 0


def command_lint(args: Any) -> int:
    """
    Lint changelog fragments.

    :arg args: Parsed arguments
    """
    # Passing fallback_to_other_project=True ensures that we don't expect galaxy.yml
    # or lib/ansible to be present.
    paths = set_paths(fallback_to_other_project=True)

    fragment_paths: list[str] = args.fragments

    collection_details = CollectionDetails(paths)
    config = ChangelogConfig.load(paths, collection_details, ignore_is_other_project=True)

    exceptions: list[tuple[str, Exception]] = []
    fragments = load_fragments(paths, config, fragment_paths, exceptions)
    return lint_fragments(config, fragments, exceptions)


def lint_fragments(config: ChangelogConfig, fragments: list[ChangelogFragment],
                   exceptions: list[tuple[str, Exception]]) -> int:
    """
    Lint a given set of changelog fragment objects.

    :arg config: The configuration
    :arg fragments: The loaded fragments
    :arg exceptions: Exceptions from loading the fragments
    """
    linter = ChangelogFragmentLinter(config)

    errors = [(ex[0], 0, 0, 'yaml parsing error') for ex in exceptions]

    for fragment in fragments:
        errors += linter.lint(fragment)

    messages = sorted(set(
        '%s:%d:%d: %s' % (os.path.relpath(error[0]), error[1], error[2], error[3])
        for error in errors))

    for message in messages:
        print(message)

    return 3 if messages else 0


def command_lint_changelog_yaml(args: Any) -> int:
    """
    Lint changelogs/changelog.yaml file.

    :arg args: Parsed arguments
    """
    errors = lint_changelog_yaml(
        args.changelog_yaml_path, no_semantic_versioning=args.no_semantic_versioning)

    messages = sorted(set(f'{error[0]}:{error[1]}:{error[2]}: {error[3]}' for error in errors))

    for message in messages:
        print(message)

    return 3 if messages else 0


def main() -> int:
    """
    Entrypoint called from the script.

    console_scripts call functions which take no parameters.  However, it's hard to test a function
    which takes no parameters so this function lightly wraps :func:`run`, which actually does the
    heavy lifting.

    :returns: A program return code.

    Return codes:
        :0: Success
        :1: Unhandled error.  See the Traceback for more information.
        :2: There was a problem with the command line arguments
        :3: Found invalid changelog fragments
        :4: Needs to be run on a newer version of Python
        :5: Problem occured which prevented the execution of the command
    """
    if sys.version_info < (3, 6):
        print('Needs Python 3.6 or later')
        return 4

    return run(sys.argv)
