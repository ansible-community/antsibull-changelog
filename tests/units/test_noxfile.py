# SPDX-FileCopyrightText: 2026 Ansible Project
# SPDX-License-Identifier: GPL-3.0-or-later

"""Exercise release orchestration without creating releases or publishing packages."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock, call

import pytest

if sys.version_info < (3, 10):
    pytest.skip("Current nox requires Python 3.10 or later", allow_module_level=True)

spec = importlib.util.spec_from_file_location(
    "project_noxfile", Path(__file__).resolve().parents[2] / "noxfile.py"
)
noxfile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(noxfile)

COMMIT = "a" * 40
PUBLISHED_AT = "2026-11-20T12:00:00Z"
TAG_ENDPOINT = "repos/ansible-community/antsibull-changelog/git/ref/tags/1.2.3"
SIGNED_TAG_ENDPOINT = (
    "repos/ansible-community/antsibull-changelog/git/tags/signed-tag-object"
)
WORKFLOW_RUNS_ENDPOINT = "repos/ansible-community/antsibull-changelog/actions/workflows/pypi-publish.yaml/runs"


@pytest.fixture
def session(monkeypatch):
    """Fake every external command, including all signing and publishing."""
    result = Mock(posargs=[])

    def error(message):
        raise RuntimeError(message)

    result.error.side_effect = error
    monkeypatch.setattr(noxfile, "install", Mock())
    monkeypatch.setattr(noxfile.time, "sleep", Mock())

    def run(*args, **kwargs):
        if args[:2] == ("git", "status"):
            return ""
        if args[:2] == ("hatch", "version"):
            return "1.2.3"
        if args[:2] == ("git", "rev-parse"):
            return COMMIT
        if args[:3] == ("gh", "release", "view"):
            return json.dumps({"isDraft": False, "publishedAt": PUBLISHED_AT})
        if args[:3] == ("gh", "run", "watch"):
            return ""
        if args[:3] == ("gh", "run", "view"):
            return json.dumps(
                {
                    "jobs": [
                        {
                            "name": "Publish Python 🐍 distribution 📦 to PyPI",
                            "conclusion": "success",
                        }
                    ]
                }
            )
        if args[:3] in (
            ("gh", "api", TAG_ENDPOINT),
            ("gh", "api", SIGNED_TAG_ENDPOINT),
        ):
            return json.dumps({"object": {"type": "commit", "sha": COMMIT}})
        if args[:3] == ("gh", "api", WORKFLOW_RUNS_ENDPOINT):
            return json.dumps(
                {
                    "workflow_runs": [
                        {"id": 42, "head_branch": "1.2.3", "created_at": PUBLISHED_AT}
                    ]
                }
            )
        if args[:2] in (("git", "add"), ("git", "commit")):
            return ""
        pytest.fail(f"Unexpected external command: {args}")

    result.run.side_effect = run
    return result


def assert_no_bump(session):
    assert call("hatch", "version", "post") not in session.run.call_args_list
    assert not any(
        args[:2] == ("git", "commit") for args, _ in session.run.call_args_list
    )


@pytest.mark.parametrize("version", ["1.2.3", "1.2.3rc1"])
def test_publish_creates_release_before_waiting_and_bumping(session, version):
    original = session.run.side_effect
    release_created = False

    def run(*args, **kwargs):
        nonlocal release_created
        if args == ("hatch", "version"):
            return version
        if args[:3] == ("gh", "api", WORKFLOW_RUNS_ENDPOINT):
            return json.dumps(
                {
                    "workflow_runs": [
                        {"id": 42, "head_branch": version, "created_at": PUBLISHED_AT}
                    ]
                }
            )
        if args[:3] == (
            "gh",
            "api",
            f"repos/ansible-community/antsibull-changelog/git/ref/tags/{version}",
        ):
            return json.dumps({"object": {"type": "commit", "sha": COMMIT}})
        if args[:3] == ("gh", "release", "view") and not release_created:
            return ""
        if args[:3] == ("gh", "release", "create"):
            release_created = True
            assert "--verify-tag" in args
            assert "--notes-from-tag" in args
            assert ("--prerelease" in args) == (version == "1.2.3rc1")
            return "https://github.com/example/release"
        return original(*args, **kwargs)

    session.run.side_effect = run
    noxfile.publish(session)
    assert release_created
    calls = [args for args, _ in session.run.call_args_list]
    watch_index = next(
        i for i, args in enumerate(calls) if args[:3] == ("gh", "run", "watch")
    )
    bump_index = calls.index(("hatch", "version", "post"))
    assert watch_index < bump_index
    assert not any(args[:2] == ("hatch", "publish") for args in calls)


def test_publish_resumes_existing_release(session):
    noxfile.publish(session)
    calls = [args for args, _ in session.run.call_args_list]
    assert not any(args[:3] == ("gh", "release", "create") for args in calls)
    assert ("hatch", "version", "post") in calls


def test_publish_dereferences_signed_tag(session):
    original = session.run.side_effect

    def run(*args, **kwargs):
        if args[:3] == ("gh", "api", TAG_ENDPOINT):
            return json.dumps({"object": {"type": "tag", "sha": "signed-tag-object"}})
        return original(*args, **kwargs)

    session.run.side_effect = run
    noxfile.publish(session)
    assert ("hatch", "version", "post") in [
        args for args, _ in session.run.call_args_list
    ]


@pytest.mark.parametrize("version", ["1.2.3.post0", "1.2.3.dev0"])
def test_publish_rejects_unreleasable_version(session, version):
    original = session.run.side_effect
    session.run.side_effect = lambda *args, **kwargs: (
        version if args == ("hatch", "version") else original(*args, **kwargs)
    )
    with pytest.raises(RuntimeError, match="development or post-release"):
        noxfile.publish(session)
    assert_no_bump(session)


@pytest.mark.parametrize(
    "failure", ["local-tag", "upstream-tag", "draft", "watch", "job"]
)
def test_publish_failure_never_bumps(session, failure):
    original = session.run.side_effect

    def run(*args, **kwargs):
        if failure == "local-tag" and args[:3] == ("git", "rev-parse", "--verify"):
            return "b" * 40
        if failure == "upstream-tag" and args[:3] == ("gh", "api", TAG_ENDPOINT):
            return json.dumps({"object": {"type": "commit", "sha": "b" * 40}})
        if failure == "draft" and args[:3] == ("gh", "release", "view"):
            return json.dumps({"isDraft": True, "publishedAt": None})
        if failure == "watch" and args[:3] == ("gh", "run", "watch"):
            raise RuntimeError("Workflow failed")
        if failure == "job" and args[:3] == ("gh", "run", "view"):
            return json.dumps(
                {
                    "jobs": [
                        {
                            "name": "Publish Python 🐍 distribution 📦 to PyPI",
                            "conclusion": "skipped",
                        }
                    ]
                }
            )
        return original(*args, **kwargs)

    session.run.side_effect = run
    with pytest.raises(RuntimeError):
        noxfile.publish(session)
    assert_no_bump(session)


def test_wait_ignores_other_tags_and_older_releases(session):
    runs = [
        {"id": 99, "head_branch": "1.2.4", "created_at": PUBLISHED_AT},
        {"id": 98, "head_branch": "1.2.3", "created_at": "2026-11-19T12:00:00Z"},
        {"id": 42, "head_branch": "1.2.3", "created_at": PUBLISHED_AT},
    ]
    session.run.side_effect = [
        json.dumps({"workflow_runs": []}),
        json.dumps({"workflow_runs": runs}),
    ]
    assert noxfile.wait_for_publish_run(session, "1.2.3", COMMIT, PUBLISHED_AT) == 42
    noxfile.time.sleep.assert_called_once_with(5)


def test_wait_times_out_without_bumping(session):
    session.run.side_effect = lambda *args, **kwargs: json.dumps({"workflow_runs": []})
    with pytest.raises(RuntimeError, match="five minutes"):
        noxfile.wait_for_publish_run(session, "1.2.3", COMMIT, PUBLISHED_AT)
    assert_no_bump(session)
