"""
@author: Vojtech Burian
@summary: Fixtures for handling custom pytest parameters
"""
import pytest

from shishito.reporting.junithtml import LogHTML


# CURRENT TEST INFO OBJECT #

class CurrentTestInfo():
    """ Gathers test execution information about currently running test """

    def __init__(self):
        self.test_status = None
        self.test_name = None

    def set_test_info(self, new_status=None, new_name=None):
        self.test_status = new_status
        self.test_name = new_name


test_info = CurrentTestInfo()


def get_test_info():
    return test_info


# FIXTURES #

def pytest_addoption(parser):
    parser.addoption("--url", action="store", default="https://salsitasoft.com", help="specify URL for test site")

    # MODULES
    parser.addoption('--test_platform', action="store",
                     help="Test Platform")
    parser.addoption('--test_environment', action="store",
                     help="Test Environment")
    parser.addoption('--environment_configuration', action="store",
                     help="Environment Configuration")

    # BROWSERSTACK
    parser.addoption("--browser", action="store",
                     help="BrowserStack browser: Chrome, Firefox, IE, PhantomJS, Opera, Safari")
    parser.addoption("--browser_version", action="store",
                     help="BrowserStack browser version. Value depends on selected browser.")
    parser.addoption("--os", action="store",
                     help="BrowserStack operating system: Windows, OS X")
    parser.addoption("--os_version", action="store",
                     help="BrowserStack operating system version. Depends on selected OS.")
    parser.addoption("--resolution", action="store",
                     help="Screen resolution: 1024x768, 1280x960, 1280x1024, 1600x1200, 1920x1080")

    parser.addoption("--xbuildname", action="store", default="Unnamed",
                     help="Test build name")
    parser.addoption("--xbrowserName", action="store", default="iPad",
                     help="BrowserStack mobile browser: iPad, iPhone, android")
    parser.addoption("--xplatform", action="store", default="MAC",
                     help="BrowserStack mobile platform: MAC, ANDROID")
    parser.addoption("--xdevice", action="store", default="iPad Air",
                     help="BrowserStack mobile device: iPad Air, Samsung Galaxy S5 and others")
    parser.addoption("--deviceOrientation", action="store", default="portrait",
                     help="BrowserStack mobile device screen orientation: portrait or landscape")
    parser.addoption("--jira_support", action="store", default=None,
                     help="Jira username and password")
    parser.addoption('--jira_cycle_id', action="store", default=None,
                     help="Set JIRA cycle id")
    parser.addoption("--browserstack", action="store", default=None,
                     help="Browserstack username and password")
    parser.addoption('--test_mobile', action="store", default=None,
                     help="Execute tests on mobile devices")



    # APPIUM

    parser.addoption('--platformName', action="store", default=None,
                     help="Appium platform: ios, android")
    parser.addoption('--platformVersion', action="store", default=None,
                     help="Appium platform version. For iOS e.g. '7.1', for Android e.g. '4.4'")
    parser.addoption('--deviceName', action="store", default=None,
                     help="Device name (simulator or real device)")
    parser.addoption('--appiumVersion', action="store", default=None,
                     help="Appium verison, e.g. '1.3.5'")
    parser.addoption('--appPackage', action="store", default=None,
                     help="Android app package, e.g. 'com.example.android.notepad'")
    parser.addoption('--appActivity', action="store", default=None,
                     help="Android default activity, e.g. '.NotesList'")
    parser.addoption('--app', action="store", default=None,
                     help="File path or link to iOS app.zip file / Android apk file")
    parser.addoption("--autoAcceptAlerts", action="store", default=True,
                     help="Auto accepts alerts on iOS devices")
    parser.addoption("--saucelabs", action="store", default=None,
                     help="Saucelabs username and password")

    # BROWSERSTACK MOBILE

    parser.addoption('--platform', action="store", default=None,
                     help="Appium platform: ios, android")
    parser.addoption('--device', action="store", default=None,
                     help="Device name (simulator or real device)")
    parser.addoption('--browserstack.appium_version', action="store", default=None,
                     help="Appium default version")

    # REPORTS
    group = parser.getgroup("terminal reporting")
    group.addoption('--html', '--junit-html', action="store",
                    dest="htmlpath", metavar="path", default=None,
                    help="create html style report file at given path.")
    group.addoption('--htmlprefix', '--html-prefix', action="store",
                    dest="prefix", metavar="str", default=None,
                    help="prepend prefix to classnames in html output")

    # TESTRAIL
    parser.addoption("--test_rail", action="store", default=None,
                     help="TestRail Test Management tool credentials")

    # QAStats
    parser.addoption("--qastats", action="store", default=None,
                     help="QAStats Test Management tool credentials")


def pytest_configure(config):
    htmlpath = config.option.htmlpath
    prefix = config.option.prefix
    # prevent opening xmllog on slave nodes (xdist)
    if htmlpath and not hasattr(config, 'slaveinput'):
        config._html = LogHTML(htmlpath, prefix)
        config.pluginmanager.register(config._html)


def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


def pytest_collection_finish(session):
    test_names = {}
    for i in session.items:
        name, module = i.name, i.cls.__module__
        if name in test_names:
            raise Exception("You should rename duplicate test method: '%s'. It was found in modules: '%s' and '%s'"%(name, module, test_names[name]))
        test_names[name] = module


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()
    # set an report attribute for each phase of a call, which can
    # be "setup", "call", "teardown"
    setattr(item, "rep_" + rep.when, rep)
    return rep


@pytest.fixture()
def test_status(request):
    test_name = request.node.nodeid.split('::')[-1]

    def fin():
        # request.node is an "item" because we use the default
        # "function" scope
        if request.node.rep_setup.failed:
            print("setting up a test failed!", request.node.nodeid)
            test_info.set_test_info('failed_setup', test_name)
        elif request.node.rep_setup.passed:
            if request.node.rep_call.failed:
                test_info.set_test_info('failed_execution', test_name)
                print("executing test failed", request.node.nodeid)
            elif "xfail" in request.node.keywords:
                test_info.set_test_info('expected_fail', test_name)
                print("executing test failed as eXpected", request.node.nodeid)

    request.addfinalizer(fin)
    test_info.set_test_info('passed', test_name)


@pytest.fixture(scope='class')
def browser(request):
    return request.config.getoption("--browser")


@pytest.fixture
def browser_version(request):
    return request.config.getoption("--browser_version")


@pytest.fixture
def os(request):
    return request.config.getoption("--os")


@pytest.fixture
def os_version(request):
    return request.config.getoption("--os_version")


@pytest.fixture
def resolution(request):
    return request.config.getoption("--resolution")


@pytest.fixture
def xbuildname(request):
    return request.config.getoption("--xbuildname")


@pytest.fixture
def xdevice(request):
    return request.config.getoption("--xdevice")


@pytest.fixture
def xdeviceOrientation(request):
    return request.config.getoption("--xdeviceOrientation")


@pytest.fixture
def xbrowserName(request):
    return request.config.getoption("--xbrowserName")


def xplatform(request):
    return request.config.getoption("--xplatform")


@pytest.fixture
def jira_support(request):
    return request.config.getoption("--jira_support")


@pytest.fixture
def browserstack(request):
    return request.config.getoption("--browserstack")


@pytest.fixture
def jira_cycle_id(request):
    return request.config.getoption("--jira_cycle_id")


@pytest.fixture
def test_mobile(request):
    return request.config.getoption("--test_mobile")


@pytest.fixture(scope='class')
def url(request):
    return request.config.getoption("--url")
