from selenium import webdriver

from shishito.library.modules.runtime.environment.shishito_environment import ShishitoEnvironment


class ControlEnvironment(ShishitoEnvironment):
    """ Local control environment. """

    CAPABILITIES = (
        # (name, config_name, use_section, function),
        ('acceptSslCerts', 'accept_ssl_cert', False, lambda v: v.lower() == 'false'),
    )

    def start_driver(self, browser_type, capabilities, remote_driver_url=None):
        """ Starts driver """

        driver = None

        # get browser profile
        browser_profile = self.get_browser_profile(browser_type, capabilities)

        # starts local browser
        if browser_type == "firefox":
            driver = webdriver.Firefox(browser_profile, capabilities=capabilities)
        elif browser_type == "chrome":
            driver = webdriver.Chrome(desired_capabilities=capabilities, chrome_options=browser_profile)
        elif browser_type == "ie":
            driver = webdriver.Ie(capabilities=capabilities)
        elif browser_type == "phantomjs":
            driver = webdriver.PhantomJS(desired_capabilities=capabilities)
        elif browser_type == "opera":
            driver = webdriver.Opera(desired_capabilities=capabilities)
            # SafariDriver bindings for Python not yet implemented
            # elif browser == "Safari":
            # self.driver = webdriver.SafariDriver()
        else:
            raise ValueError('Unknown type of browser.')

        return driver
