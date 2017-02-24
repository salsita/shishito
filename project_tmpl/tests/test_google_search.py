# /usr/bin/env python
import pytest
from unittestzero import Assert
from shishito.runtime.shishito_support import ShishitoSupport
from shishito.ui.selenium_support import SeleniumTest
from shishito.conf.conftest import get_test_info


@pytest.mark.usefixtures("test_status")
class TestMainPage():
    """ Contextual help test """

    def setup_class(self):
        self.tc = ShishitoSupport().get_test_control()
        self.driver = self.tc.start_browser()
        self.ts = SeleniumTest(self.driver)

    def teardown_class(self):
        self.tc.stop_browser()

    def setup_method(self, method):
        self.tc.start_test(True)

    def teardown_method(self, method):
        self.tc.stop_test(get_test_info())

    ### Tests ###
    @pytest.mark.smoke
    def test_google_search(self):
        """ test google search """
        Assert.equal(self.driver.title, 'Google')

