RUNS = {
    "run_twice": {
        "component": None,
        "env": None,
        "metadata": {"project": "test_project", "accessibility": True},
        "source": "local",
        "summary": {
            "failures": 2,
            "errors": 0,
            "xfailures": 0,
            "xpasses": 0,
            "skips": 3,
            "tests": 7,
            "collected": 7,
            "not_run": 0,
        },
    },
    "run_once": {
        "component": None,
        "env": None,
        "metadata": {"project": "test_project", "accessibility": True},
        "source": "local",
        "summary": {
            "failures": 1,
            "errors": 0,
            "xfailures": 0,
            "xpasses": 0,
            "skips": 1,
            "tests": 3,
            "collected": 3,
            "not_run": 0,
        },
    },
}

RESULTS = {
    "test_help_message": {
        "test_id": "test_help_message",
        "component": None,
        "env": None,
        "result": "passed",
        "metadata": {
            "statuses": {
                "setup": ["passed", False],
                "call": ["passed", False],
                "teardown": ["passed", False],
            },
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [],
            "project": "test_project",
            "node_id": "example_test_to_report_to_ibutsu.py::test_help_message",
            "user_properties": {},
            "extra_data": "runtest_setup",
            "test_type": "TestType",
        },
        "params": {},
        "source": "local",
    },
    "test_mark_skip": {
        "test_id": "test_mark_skip",
        "component": None,
        "env": None,
        "result": "skipped",
        "metadata": {
            "statuses": {"setup": ["skipped", False], "teardown": ["passed", False]},
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [
                {
                    "name": "skip",
                    "args": ["Skipped because I'm not a fan of this test."],
                    "kwargs": {},
                }
            ],
            "project": "test_project",
            "node_id": "example_test_to_report_to_ibutsu.py::test_mark_skip",
            "user_properties": {},
        },
        "params": {},
        "source": "local",
    },
    "test_mark_skipif": {
        "test_id": "test_mark_skipif",
        "component": None,
        "env": None,
        "result": "skipped",
        "metadata": {
            "statuses": {"setup": ["skipped", False], "teardown": ["passed", False]},
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [
                {
                    "name": "skipif",
                    "args": [True],
                    "kwargs": {"reason": "Skipping due to True equaling True"},
                }
            ],
            "project": "test_project",
            "node_id": "example_test_to_report_to_ibutsu.py::test_mark_skipif",
            "user_properties": {},
        },
        "params": {},
        "source": "local",
    },
    "test_skip": {
        "test_id": "test_skip",
        "component": None,
        "env": None,
        "result": "skipped",
        "metadata": {
            "statuses": {
                "setup": ["passed", False],
                "call": ["skipped", False],
                "teardown": ["passed", False],
            },
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [{"name": "some_marker", "args": [], "kwargs": {}}],
            "project": "test_project",
            "extra_data": "runtest_setup",
            "node_id": "example_test_to_report_to_ibutsu.py::test_skip",
            "user_properties": {},
            "test_type": "TestType",
        },
        "params": {},
        "source": "local",
    },
    "test_pass": {
        "test_id": "test_pass",
        "component": None,
        "env": None,
        "result": "passed",
        "metadata": {
            "statuses": {
                "setup": ["passed", False],
                "call": ["passed", False],
                "teardown": ["passed", False],
            },
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [{"name": "some_marker", "args": [], "kwargs": {}}],
            "project": "test_project",
            "node_id": "example_test_to_report_to_ibutsu.py::test_pass",
            "user_properties": {},
            "extra_data": "runtest_setup",
            "test_type": "TestType",
        },
        "params": {},
        "source": "local",
    },
    "test_fail": {
        "test_id": "test_fail",
        "component": None,
        "env": None,
        "result": "failed",
        "metadata": {
            "statuses": {
                "setup": ["passed", False],
                "call": ["failed", False],
                "teardown": ["passed", False],
            },
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [],
            "project": "test_project",
            "node_id": "example_test_to_report_to_ibutsu.py::test_fail",
            "user_properties": {},
            "short_tb": '>       pytest.fail("I don\'t like tests that pass")\nE       Failed: I don\'t like tests that pass\n\nexample_test_to_report_to_ibutsu.py:33: Failed\nFailed\nb"I don\'t like tests that pass"',
            "exception_name": "Failed",
            "extra_data": "runtest_setup",
            "test_type": "TestType",
        },
        "params": {},
        "source": "local",
    },
    "test_exception": {
        "test_id": "test_exception",
        "component": None,
        "env": None,
        "result": "failed",
        "metadata": {
            "statuses": {
                "setup": ["passed", False],
                "call": ["failed", False],
                "teardown": ["passed", False],
            },
            "fspath": "example_test_to_report_to_ibutsu.py",
            "markers": [{"name": "some_marker", "args": [], "kwargs": {}}],
            "project": "test_project",
            "extra_data": "runtest_setup",
            "node_id": "example_test_to_report_to_ibutsu.py::test_exception",
            "user_properties": {},
            "short_tb": ">       raise Exception(\"Boom!\")\nE       Exception: Boom!\n\nexample_test_to_report_to_ibutsu.py:38: Exception\nException\nb'Boom!'",
            "exception_name": "Exception",
            "test_type": "TestType",
        },
        "params": {},
        "source": "local",
    },
}
