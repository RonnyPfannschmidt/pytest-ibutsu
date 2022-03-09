pytest_plugins = "pytester"


def pytest_addoption(parser):
    group = parser.getgroup("ibutsu")
    group.addoption("--test-ibutsu", help="ibutsu url to use for test")
    group.addoption("--test-ibutsu-token", help="ibutsu url to use for test")
    group.addoption("--test-ibutsu-project", help="ibutsu url to use for test")
