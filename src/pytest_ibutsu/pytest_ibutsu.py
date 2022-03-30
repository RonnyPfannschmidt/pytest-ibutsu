from __future__ import annotations

import json
import os
import shutil
import tarfile
import time
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TypedDict

import pytest

from ._data_processing import DATA_OPTIONS
from ._data_processing import get_name
from ._data_processing import get_test_idents
from ._data_processing import merge_dicts
from ._data_processing import parse_data_option
from ._data_processing import safe_string
from ._servers import get_server
from ._servers import IbutsuApiServer
from ._servers import NoServer

# A list of markers that can be filtered out
FILTERED_MARKERS = ["parametrize"]

# Convert the blocker category into an Ibutsu Classification
BLOCKER_CATEGORY_TO_CLASSIFICATION = {
    "needs-triage": "needs_triage",
    "automation-issue": "test_failure",
    "environment-issue": "environment_failure",
    "product-issue": "product_failure",
    "product-rfe": "product_rfe",
}

# Place a limit on the file-size we can upload for artifacts
UPLOAD_LIMIT = 5 * 1024 * 1024  # 5 MiB


def overall_test_status(statuses: dict[str, tuple[str, bool]]) -> str:
    """ """
    # todo: let the pytest teststatus hook return the cases for whens
    # Handle some logic for when to count certain tests as which state
    for when, (outcome, wasxfail) in statuses.items():
        if when in ("call", "setup") and wasxfail and outcome == "skipped":
            return "xfailed"
        elif when == "call" and wasxfail and outcome == "passed":
            return "xpassed"
        elif when in ("setup", "teardown") and outcome == "failed":
            return "error"
        elif outcome == "skipped":
            return "skipped"
        elif when == "call" and outcome == "failed":
            return "failed"
        elif outcome == "manual":
            return "manual"
        elif outcome == "blocked":
            return "blocked"
    return "passed"


class ResultsDict(TypedDict):
    duration: float | None
    component: str | None


def update_extra_data_from_env(extra_data: dict[str, str | dict | None]):
    extra_data = {"component": None, "env": None, **extra_data}

    # Set an env var ID
    env_id: str = os.environ.get("IBUTSU_ENV_ID", "")
    if env_id:
        extra_data.update(env_id=env_id)
    # Auto-detect running in Jenkins and add to the metadata
    if os.environ.get("JOB_NAME") and os.environ.get("BUILD_NUMBER"):
        extra_data.update(
            jenkins={
                "job_name": os.environ.get("JOB_NAME"),
                "build_number": os.environ.get("BUILD_NUMBER"),
                "build_url": os.environ.get("BUILD_URL"),
            }
        )
    # If the project is set via environment variables
    if os.environ.get("IBUTSU_PROJECT"):
        extra_data.update(project=os.environ.get("IBUTSU_PROJECT"))
    return extra_data


@dataclass(order=False, eq=False, unsafe_hash=True)
class TimeTimer:
    started_at: float | None = None
    stopped_at: float | None = None

    def start(self):
        assert self.started_at is None
        self.started_at = time.time()

    def stop(self):
        assert self.started_at is not None
        assert self.stopped_at is None
        self.stopped_at = time.time()

    @property
    def duration(self) -> float:

        if self.started_at is not None:
            if self.stopped_at is not None:
                return self.stopped_at - self.started_at
            else:
                return time.time() - self.started_at
        else:
            return 0


@dataclass(repr=False, order=False, eq=False)
class IbutsuArchiver:
    """
    Save all Ibutsu results to archive
    """

    server: IbutsuApiServer | NoServer
    temp_path: Path
    source: str
    _results: ResultsDict = field(
        default_factory=lambda: ResultsDict(duration=None, component=None)
    )
    extra_data: DATA_OPTIONS = field(default_factory=DATA_OPTIONS.new)
    archive_name: str | None = None
    _timer: TimeTimer = field(default_factory=TimeTimer)
    frontend: str | None = None
    _session = None

    run: dict | None = None
    results: dict = field(default_factory=dict)

    def _status_to_summary(self, status):
        return {
            "failed": "failures",
            "error": "errors",
            "skipped": "skips",
            "xfailed": "xfailures",
            "xpassed": "xpasses",
            "tests": "tests",
        }.get(status, status)

    def _save_run(self, run):
        if not run.get("metadata"):
            run["metadata"] = {}
        run["metadata"].update(self.extra_data)

        with self.temp_path.joinpath("run.json").open("w") as f:
            json.dump(run, f)

    @property
    def duration(self) -> float:
        return self._timer.duration

    def start_timer(self):
        self._timer.start()

    def stop_timer(self):
        self.timer.stop()

    def shutdown(self):
        # Gather the summary before building the archive
        summary = {
            "failures": 0,
            "skips": 0,
            "errors": 0,
            "xfailures": 0,
            "xpasses": 0,
            "tests": 0,
            "collected": 0,
        }
        for result in self._results.values():
            if result is None:
                continue
            key = self._status_to_summary(result["result"])
            summary[key] = summary.get(key, 0) + 1
            # update the number of tests that actually ran
            summary["tests"] += 1
        # store the number of tests that were collected
        summary["collected"] = getattr(self._session, "testscollected", summary["tests"])
        # store the summary on the run
        self.run["summary"] = summary
        self.update_run()
        # Build the tarball
        if self.archive_name is not None:
            self.tar_file = os.path.join(
                os.path.abspath("."), self.archive_name.format(run_id=self.run_id)
            )
            print(f"Creating archive {os.path.basename(self.archive_name)}...")
            with tarfile.open(self.tar_file, "w:gz") as tar:
                tar.add(self.temp_path, self.run_id)
        self.server.shutdown()

    def output_msg(self):
        with open(".last-ibutsu-run-id", "w") as f:
            if self.run_id is not None:
                f.write(self.run_id)
        url = f"{self.server.frontend}/runs/{self.run_id}"
        with open(".last-ibutsu-run-url", "w") as f:
            f.write(url)
        if not self.server._has_server_error:
            print(f"Results can be viewed on: {url}")
        else:
            print(
                "There was an error while uploading results,"
                " and not all results were uploaded to the server."
            )
            print(f"All results were written to archive, partial results can be viewed on: {url}")

    def get_run_id(self):
        if not self.run:
            run = {
                "duration": 0.0,
                "component": "",
                "summary": {
                    "failures": 0,
                    "skips": 0,
                    "errors": 0,
                    "xfailures": 0,
                    "xpasses": 0,
                    "tests": 0,
                },
                "metadata": self.extra_data,
                "source": self.source,
                "start_time": datetime.utcnow().isoformat(),
            }
            self.run = self.add_run(run=run)
        return self.run["id"]

    def set_run_id(self, run_id: str):
        self._run_id = run_id
        self.refresh_run()

    def add_run(self, run):
        if not run.get("source"):
            run["source"] = self.source
        run = self.server.add_run(run)
        assert run.get("id") is not None
        self._save_run(run)

        return run

    def refresh_run(self):
        """This does nothing, there's nothing to do here"""
        if self.run_id:
            server_run = self.server.refresh_run(self.run_id)
            if server_run:
                self.run = server_run

    def update_run(self, duration: float | None = None):
        assert self.run is not None
        if duration is not None:
            self.run["duration"] = duration
        self._save_run(self.run)
        self.server.update_run(self.run)

    def add_result(self, result):
        if not result.get("metadata"):
            result["metadata"] = {}
        result["metadata"].update(self.extra_data)
        server_result = self.server.add_result(result)
        result.update(server_result)

        self._write_result(result["id"], result)
        assert result["id"]
        return result

    def update_result(self, id, result):
        self.server.update_result(id, result)
        self._write_result(id, result)

    def _write_result(self, id, result):
        assert result["id"] == id
        art_path = os.path.join(self.temp_path, id)
        os.makedirs(art_path, exist_ok=True)
        if not result.get("metadata"):
            result["metadata"] = {}
        result["metadata"].update(self.extra_data)
        with open(os.path.join(art_path, "result.json"), "w") as f:
            json.dump(result, f)
        self.results[id] = result

    def upload_artifact(self, id_, filename, data, is_run=False):
        """
        Save an artifact to the archive.

        'id_' can be either a run or result ID.
        'is_run' should be True if it is a run ID.
        """
        file_size = os.stat(data).st_size
        if file_size < UPLOAD_LIMIT:
            art_path = os.path.join(self.temp_path, id_)
            os.makedirs(art_path, exist_ok=True)
            shutil.copyfile(data, os.path.join(art_path, filename))
        else:
            print(
                f"File '{filename}' of size '{file_size}' bytes"
                f" exceeds global Ibutsu upload limit of '{UPLOAD_LIMIT}' bytes."
                f" File will not be uploaded to Ibutsu."
            )
        if file_size < UPLOAD_LIMIT:
            self.server.upload_artifact(id_, filename, data, is_run=is_run)

    def upload_artifact_raw(self, id_, filename, data, is_run=False):
        file_object = NamedTemporaryFile(delete=False)
        os_file_name = file_object.name
        file_object.write(data)
        file_object.close()
        self.upload_artifact(id_, filename, os_file_name, is_run=is_run)

    def upload_artifact_from_file(self, id_, logged_filename, filename, is_run=False):
        self.upload_artifact(id_, logged_filename, filename, is_run=is_run)

    def get_xfail_reason(self, data, report):
        xfail_reason = None
        if data["metadata"].get("markers"):
            for marker in data["metadata"]["markers"]:
                if marker.get("name") == "xfail":
                    xfail_reason = marker["kwargs"].get("reason")
        else:
            xfail_reason = report.wasxfail.split("reason: ")[1]
        return xfail_reason

    def get_skip_reason(self, data, report):
        skip_reason = None
        # first see if the reason is in the marker skip
        if data["metadata"].get("markers"):
            for marker in data["metadata"]["markers"]:
                if marker.get("name") == "skipif":
                    skip_reason = marker["kwargs"].get("reason")
                elif marker.get("name") == "skip":
                    try:
                        skip_reason = marker["args"][0]
                    except IndexError:
                        pass
        # otherwise we must use the report to get the skip information
        else:
            try:
                if report.longrepr:
                    skip_reason = report.longrepr[2].split("Skipped: ")[1]
            except IndexError:
                pass
        return skip_reason

    def get_classification(self, reason):
        """Get the skip/xfail classification and category from the reason"""
        category = None
        try:
            category = reason.split("category:")[1].strip()
        except IndexError:
            pass
        return BLOCKER_CATEGORY_TO_CLASSIFICATION.get(category)

    @pytest.mark.tryfirst
    def pytest_collection_modifyitems(self, session, items):
        # save the pytest session object for later use
        self._session = session

        # loop over all items and add ibutsu data
        for item in items:
            data = getattr(item, "_ibutsu", {})
            new_data = {"id": None, "data": {"metadata": {}}, "artifacts": {}}
            merge_dicts(data, new_data)
            item._ibutsu = new_data

    @pytest.mark.hookwrapper
    def pytest_runtest_protocol(self, item):
        if hasattr(item, "callspec"):
            try:
                params = {p: get_name(v) for p, v in item.callspec.params.items()}
            except Exception:
                params = {}
        else:
            params = {}
        start_time = datetime.utcnow().isoformat()
        fspath: str = item.location[0] or item.fspath.strpath
        site_free_path = fspath.split("site-packages/", 1)[-1]
        data = {
            "result": "failed",
            "source": getattr(self, "source", "local"),
            "params": params,
            "start_time": start_time,
            "test_id": get_test_idents(item)[0],
            "duration": 0.0,
            "metadata": {
                "statuses": {},
                "report_teststatuses": {},
                "run": self.run_id,
                "durations": {},
                "fspath": site_free_path,
                "markers": [
                    {"name": m.name, "args": m.args, "kwargs": m.kwargs}
                    for m in item.iter_markers()
                    if m.name not in FILTERED_MARKERS
                ],
            },
        }

        def _default(obj):
            if callable(obj) and hasattr(obj, "__code__"):
                return f"function: '{obj.__name__}', args: {str(obj.__code__.co_varnames)}"
            else:
                return str(obj)

        # serialize the metadata just in case of any functions present
        data["metadata"] = json.loads(json.dumps(data["metadata"], default=_default))
        result = self.add_result(result=data)
        item._ibutsu["id"] = result["id"]
        # Update result data
        old_data = item._ibutsu["data"]
        merge_dicts(old_data, data)
        item._ibutsu["data"] = data
        yield
        # Finish up with the result and update it
        self.update_result(item._ibutsu["id"], result=item._ibutsu["data"])

    def pytest_exception_interact(self, node, call, report):
        if not hasattr(report, "_ibutsu"):
            return
        val = safe_string(call.excinfo.value)
        last_lines = "\n".join(report.longreprtext.split("\n")[-4:])
        short_tb = "{}\n{}\n{}".format(
            last_lines, call.excinfo.type.__name__, val.encode("ascii", "xmlcharrefreplace")
        )
        id = report._ibutsu["id"]
        data = report._ibutsu["data"]
        self.upload_artifact_raw(id, "traceback.log", bytes(report.longreprtext, "utf8"))
        data["metadata"]["short_tb"] = short_tb
        data["metadata"]["exception_name"] = call.excinfo.type.__name__
        report._ibutsu["data"] = data

    def pytest_runtest_logreport(self, report):
        if not hasattr(report, "_ibutsu"):
            return

        xfail = hasattr(report, "wasxfail")

        data = report._ibutsu["data"]
        data["metadata"]["user_properties"] = {key: value for key, value in report.user_properties}
        data["metadata"]["statuses"][report.when] = report.outcome, xfail
        data["metadata"]["report_teststatuses"][report.when] = None
        data["metadata"]["durations"][report.when] = report.duration
        data["result"] = overall_test_status(data["metadata"]["statuses"])
        if data["result"] == "skipped" and not data["metadata"].get("skip_reason"):
            reason = self.get_skip_reason(data, report)
            if reason:
                data["metadata"]["skip_reason"] = reason
        elif data["result"] == "xfailed":
            reason = self.get_xfail_reason(data, report)
            if reason:
                data["metadata"]["xfail_reason"] = reason
        else:
            reason = None
        if reason:
            classification = self.get_classification(reason)
            if classification:
                data["metadata"]["classification"] = classification
        data["duration"] = sum(v for v in data["metadata"]["durations"].values())
        report._ibutsu["data"] = data

    def pytest_sessionfinish(self):
        self.stop_timer()
        self.update_run(duration=self.duration)

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Item, call: pytest.CallInfo):
        outcome = yield
        res = outcome.get_result()  # will raise if outcome was exception
        res._ibutsu = item._ibutsu  # type: ignore
        categories = res._ibutsu["data"]["metadata"].setdefault("pytest-category", {})

        categories[call.when] = item.config.hook.pytest_report_teststatus(
            report=res, config=item.config
        )[0]

    @property
    def run_id(self) -> str | None:
        if self.run:
            return self.run.get("id")
        else:
            return None


def pytest_addoption(parser):
    parser.addini("ibutsu_server", help="The Ibutsu server to connect to")
    parser.addini("ibutsu_token", help="The JWT token to authenticate with the server")
    parser.addini("ibutsu_source", help="The source of the test run")
    parser.addini("ibutsu_metadata", help="Extra metadata to include with the test results")
    parser.addini("ibutsu_project", help="Project ID or name")
    parser.addini("ibutsu_archive", help="archive name for artifact archive")

    group = parser.getgroup("ibutsu")
    group.addoption(
        "--ibutsu",
        dest="ibutsu_server",
        action="store",
        metavar="URL",
        default=None,
        help="URL for the Ibutsu server",
    )
    group.addoption(
        "--ibutsu-archive",
        dest="ibutsu_archive",
        action="store",
        default=None,
        help="filename for the archivel, use {run_id} for the run_id",
    )
    group.addoption(
        "--ibutsu-token",
        dest="ibutsu_token",
        action="store",
        metavar="TOKEN",
        default=None,
        help="The JWT token to authenticate with the server",
    )
    group.addoption(
        "--ibutsu-source",
        dest="ibutsu_source",
        action="store",
        metavar="SOURCE",
        default=None,
        help="set the source for the tests",
    )
    group.addoption(
        "--ibutsu-data",
        dest="ibutsu_data",
        action="append",
        metavar="KEY=VALUE",
        default=[],
        help="extra metadata for the test result, key=value",
    )
    group.addoption(
        "--ibutsu-project",
        dest="ibutsu_project",
        action="store",
        metavar="PROJECT",
        default=None,
        help="project id or name",
    )


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node):
    if not hasattr(node.config, "_ibutsu"):
        # If this plugin is not active
        return
    node.workerinput["ibutsu:run_id"] = node.config._ibutsu.run_id
    node.workerinput["ibutsu:run_dir"] = node.config._ibutsu.tmp_path


def _ini_or_option(config: pytest.Config, key: str) -> str | None:
    option = config.getoption(key, None)
    ini = config.getini(key)
    return ini or option


def _mk_ibutsu_tmpdir(config: pytest.Config) -> Path:
    factory: pytest.TempPathFactory = getattr(config, "_tmp_path_factory")

    return factory.mktemp("ibutsu", numbered=False)


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:

    ibutsu_server: str | None = _ini_or_option(config, "ibutsu_server")
    ibutsu_archive = _ini_or_option(config, "ibutsu_archive")

    tmp_path = _mk_ibutsu_tmpdir(config)

    ibutsu_token = _ini_or_option(config, "ibutsu_token")
    ibutsu_source = _ini_or_option(config, "ibutsu_source") or "local"
    ibutsu_data = parse_data_option(config.getoption("ibutsu_data", []))
    ibutsu_project = _ini_or_option(config, "ibutsu_project")
    if ibutsu_project:
        ibutsu_data.update({"project": ibutsu_project})
    server: IbutsuApiServer | NoServer
    if not ibutsu_server:
        server = NoServer()
    elif not ibutsu_project:
        print("project missing, swittching to no server")
        server = NoServer()
        if ibutsu_archive is None:
            ibutsu_archive = "ibutsu-{run_id}.tar.gz"
    else:
        assert ibutsu_server is not None
        maybe_server = get_server(ibutsu_server, ibutsu_token)
        if maybe_server is None:
            print("switching to archiver")
            server = NoServer()
            if ibutsu_archive is None:
                ibutsu_archive = "ibutsu-{run_id}.tar.gz"
        else:
            server = maybe_server

    ibutsu = IbutsuArchiver(
        server=server,
        source=ibutsu_source,
        temp_path=tmp_path,
        extra_data=ibutsu_data,
        archive_name=ibutsu_archive,
    )

    # HACK
    ibutsu.get_run_id()

    if config.pluginmanager.has_plugin("xdist"):
        if hasattr(config, "workerinput") and config.workerinput.get("run_id"):
            ibutsu.set_run_id(config.workerinput["run_id"])
            run = {
                "id": ibutsu.run_id,
                "duration": 0.0,
                "component": "",
                "summary": {
                    "failures": 0,
                    "skips": 0,
                    "errors": 0,
                    "xfailures": 0,
                    "xpasses": 0,
                    "tests": 0,
                },
                "metadata": ibutsu.extra_data,
                "source": getattr(ibutsu, "source", "local"),
                "start_time": datetime.utcnow().isoformat(),
            }
            ibutsu.run = ibutsu.add_run(run=run)
        else:
            ibutsu.set_run_id(ibutsu.get_run_id())
    config._ibutsu = ibutsu

    config.pluginmanager.register(ibutsu, name="ibutsu:sender")


def pytest_collection_finish(session: pytest.Session):
    if not hasattr(session.config, "_ibutsu"):
        # If this plugin is not active
        return
    ibutsu = session.config._ibutsu
    if not session.config.pluginmanager.has_plugin("xdist"):
        ibutsu.set_run_id(ibutsu.get_run_id())
    ibutsu.start_timer()
    ibutsu.output_msg()


def pytest_unconfigure(config):
    ibutsu_instance = getattr(config, "_ibutsu", None)
    if ibutsu_instance:
        del config._ibutsu
        config.pluginmanager.unregister(ibutsu_instance)
        config.hook.pytest_ibutsu_before_shutdown(config=config, ibutsu=ibutsu_instance)
        ibutsu_instance.shutdown()


def pytest_addhooks(pluginmanager):
    from . import newhooks

    pluginmanager.add_hookspecs(newhooks)
