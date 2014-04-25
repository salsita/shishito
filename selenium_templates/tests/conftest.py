# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Fixtures for handling custom BrowserStack parameters
"""
import pytest
from library.junithtml import LogHTML

# CURRENT TEST INFO OBJECT #

class TestInfo():
    """ Gathers test execution information about currently running test """
    def __init__(self):
        self.test_status = None
        self.test_name = None

    def set_test_info(self, new_status=None, new_name=None):
        self.test_status = new_status
        self.test_name = new_name

test_info = TestInfo()


def get_test_info():
    return test_info


# FIXTURES #

def pytest_addoption(parser):
    parser.addoption("--xbrowser", action="store", default="Chrome",
                     help="BrowserStack browser: Chrome, Firefox, IE, PhantomJS, Opera, Safari")
    parser.addoption("--xbrowserversion", action="store", default="32.0",
                     help="BrowserStack browser version. Value depends on selected browser.")
    parser.addoption("--xos", action="store", default="Windows",
                     help="BrowserStack operating system: Windows, OS X")
    parser.addoption("--xosversion", action="store", default="7",
                     help="BrowserStack operating system version. Depends on selected OS.")
    parser.addoption("--xresolution", action="store", default="1024x768",
                     help="Screen resolution: 1024x768, 1280x960, 1280x1024, 1600x1200, 1920x1080")
    parser.addoption("--xbuildname", action="store", default="Unnamed",
                     help="Test build name")
    group = parser.getgroup("terminal reporting")
    group.addoption('--html', '--junit-html', action="store",
           dest="htmlpath", metavar="path", default=None,
           help="create html style report file at given path.")
    group.addoption('--htmlprefix', '--html-prefix', action="store",
           dest="prefix", metavar="str", default=None,
           help="prepend prefix to classnames in html output")



def pytest_configure(config):
    htmlpath = config.option.htmlpath
    #print(htmlpath)
    prefix = config.option.prefix
    #print(prefix)
    # prevent opening xmllog on slave nodes (xdist)
    if htmlpath and not hasattr(config, 'slaveinput'):
        config._html = LogHTML(htmlpath, prefix)
        config.pluginmanager.register(config._html)

def pytest_unconfigure(config):
    html = getattr(config, '_html', None)
    if html:
        del config._html
        config.pluginmanager.unregister(html)


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    # execute all other hooks to obtain the report object
    rep = __multicall__.execute()
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
            print "setting up a test failed!", request.node.nodeid
            test_info.set_test_info('failed_setup', test_name)
        elif request.node.rep_setup.passed:
            if request.node.rep_call.failed:
                test_info.set_test_info('failed_execution', test_name)
                print "executing test failed", request.node.nodeid
    request.addfinalizer(fin)
    test_info.set_test_info('passed', test_name)


@pytest.fixture(scope='class')
def xbrowser(request):
    return request.config.getoption("--xbrowser")


@pytest.fixture
def xbrowserversion(request):
    return request.config.getoption("--xbrowserversion")


@pytest.fixture
def xos(request):
    return request.config.getoption("--xos")


@pytest.fixture
def xosversion(request):
    return request.config.getoption("--xosversion")


@pytest.fixture
def xresolution(request):
    return request.config.getoption("--xresolution")


@pytest.fixture
def xbuildname(request):
    return request.config.getoption("--xbuildname")