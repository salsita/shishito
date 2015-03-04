from selenium import webdriver

from shishito.library.modules.runtime.shishito_support import ShishitoSupport


class EnvironmentControl(object):
    def __init__(self):
        self.module_name = 'local'
        self.shishito_support = ShishitoSupport()

        self.driver = None
        self.capabilities = None

    def call_browser(self, browser_type=None, capabilities=None):
        """ Starts browser """
        # get browser capabilities and profile
        if capabilities:
            self.capabilities.update(self.get_capabilities())
        self.start_driver(browser_type, self.capabilities)

    def get_capabilities(self):
        """ Returns dictionary of browser capabilities """
        return {'acceptSslCerts': self.shishito_support.gid('accept_ssl_cert').lower() == 'false'}

    def start_driver(self, browser_type, capabilities):
        """ Starts driver """
        # add extensions to browser
        browser_profile = self.get_browser_profile(capabilities)

        # starts local browser
        if browser_type == "firefox":
            self.driver = webdriver.Firefox(browser_profile, capabilities=capabilities)
        elif browser_type == "chrome":
            self.driver = webdriver.Chrome(desired_capabilities=capabilities, chrome_options=browser_profile)
        elif browser_type == "ie":
            self.driver = webdriver.Ie(capabilities=capabilities)
        elif browser_type == "phantomjs":
            self.driver = webdriver.PhantomJS(desired_capabilities=capabilities)
        elif browser_type == "opera":
            self.driver = webdriver.Opera(desired_capabilities=capabilities)
            # SafariDriver bindings for Python not yet implemented
            # elif browser == "Safari":
            # self.driver = webdriver.SafariDriver()

    def get_browser_profile(self, capabilities):
        """ Returns updated browser profile ready to be passed to driver """
        profile = None
        browser_type = capabilities['browser'].lower()

        # add extensions to remote driver
        if self.shishito_support.gid('with_extension'):
            # browser_profile = self.add_extension_to_browser(browser_type, browser_profile)
            pass

        if browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("excludeSwitches", ["ignore-certificate-errors"])
            self.capabilities.update(chrome_options.to_capabilities())
        elif browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
        return profile