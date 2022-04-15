RUN = {
    "component": None,
    "env": None,
    "metadata": {"project": "test_project"},
    "source": "local",
    "summary": {
        "failures": 1,
        "errors": 0,
        "xfailures": 0,
        "xpasses": 0,
        "skips": 3,
        "tests": 6,
        "collected": 6,
        "not_run": 0,
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
            "user_properties": {},
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
            "markers": [],
            "project": "test_project",
            "user_properties": {},
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
            "markers": [],
            "project": "test_project",
            "user_properties": {},
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
            "user_properties": {},
            "short_tb": '>       pytest.fail("I don\'t like tests that pass")\nE       Failed: I don\'t like tests that pass\n\nexample_test_to_report_to_ibutsu.py:31: Failed\nFailed\nb"I don\'t like tests that pass"',
            "exception_name": "Failed",
        },
        "params": {},
        "source": "local",
    },
}
