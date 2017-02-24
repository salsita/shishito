import inspect
import os
import re
import configparser
from selenium import webdriver


class ShishitoEnvironment(object):

    """ Base class for test environment. """

    BROWSER_OPTION_KEYWORDS = {     # map lowercase browser name to option keyword understood by chromedriver/geckodriver...
            'chrome': 'chromeOptions',
            'firefox': 'moz:firefoxOptions',
    }

    def __init__(self, shishito_support):
        self.shishito_support = shishito_support


    def get_browser_arguments(self, config_section):
        """
        return array of browser command line arguments from config_section
            [Chrome]
            browser_arguments=--enable-experimental-web-platform-features --unlimited-storage
            ...
        :param config_section: name of config section in web/*.properties (e.g. Chrome)
        :return: array
        """

        if config_section is None:
            return []

        try:
            arguments_string = self.shishito_support.get_opt(config_section, 'browser_arguments')
        except configparser.NoOptionError:
            return []
        arguments = [i for i in re.split('\s+', arguments_string) if i != '']
        return arguments


    def add_cmdline_arguments_to_browser(self, browser_capabilities, config_section):
        """
        Add browser command line arguments to capabilities dict
        :param browser_capabilities: dict (see https://w3c.github.io/webdriver/webdriver-spec.html)
        :param config_section: name of the browser config section (e.g. 'Chrome')
        """

        get_opt = self.shishito_support.get_opt
        browser_name = get_opt(config_section, 'browser').lower()

        if browser_name not in self.BROWSER_OPTION_KEYWORDS:
            return

        arguments = self.get_browser_arguments(config_section)
        if arguments:
            args_keyword = 'args'
            browser_keyword = self.BROWSER_OPTION_KEYWORDS[browser_name]

            if browser_keyword not in browser_capabilities:
                browser_capabilities[browser_keyword] = {}
            if args_keyword not in browser_capabilities[browser_keyword]:
                browser_capabilities[browser_keyword][args_keyword] = []

            browser_capabilities[browser_keyword][args_keyword].extend(arguments)


    def add_extension_to_browser(self, browser_type, browser_profile):
        """ Return browser profile updated with one or more extensions """

        if browser_type == 'chrome':
            all_extensions = self.get_extension_file_names('crx')
            for chr_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.shishito_support.project_root, 'extension', chr_extension + '.crx'))

        elif browser_type == 'firefox':
            all_extensions = self.get_extension_file_names('xpi')
            for ff_extension in all_extensions:
                browser_profile.add_extension(os.path.join(self.shishito_support.project_root, 'extension', ff_extension + '.xpi'))

        return browser_profile

    def call_browser(self, config_section):
        """ Start webdriver for given config section. Prepare capabilities for the browser, set browser resolution.

        :param str config_section: section in platform/environment.properties config
        :return: created webdriver
        """

        # get browser capabilities
        capabilities = self.get_capabilities(config_section)

        # get browser type
        browser_type = self.shishito_support.get_opt(config_section, 'browser')
        browser_type = browser_type.lower()

        # get driver
        driver = self.start_driver(browser_type, capabilities, config_section=config_section)

        # set browser size is defined
        browser_size = self.shishito_support.get_opt(config_section, 'resolution')
        if browser_size:
            # default size --> leave it on webdriver
            width, height = browser_size.split('x')
            driver.set_window_size(width, height)

        return driver

    def get_capabilities(self, config_section):
        """ Return dictionary of capabilities for specific config combination/

        :param str config_section: section in platform/environment.properties config
        :return: dict with capabilities
        Example of browser capabilities object:
             "desiredCapabilities" : {
                "browserName" : "chrome",
                "version" : "50.1",
                "acceptSslCerts" : true,
                "javascriptEnabled" : true,
                "platform" : "ANY",
                "chromeOptions" : {
                   "args" : [ "--ignore-certificate-errors" ],
                   "extensions" : [ "base64-xxxxx" ]
                }
             }
        """
        return {}

    def start_driver(self, browser_type, capabilities, config_section=None):
        """ Prepare selenium webdriver.

        :param str browser_type: type of browser for which prepare driver
        :param dict capabilities: capabilities used for webdriver initialization
        """

        raise NotImplementedError()

    def get_browser_profile(self, browser_type, capabilities, config_section=None):
        """ Return updated browser profile ready to be passed to driver.

        :param str browser_type: browser type (chrome, firefox, ..)
        :param dict capabilities: capabilities dict - can be updated
        :return: browser profile or None
        """

        # lowercase browser_type
        browser_type = browser_type.lower()

        profile = None

        if browser_type == 'chrome':
            chrome_options = webdriver.ChromeOptions()

            # chrome command line agruments (browser_arguments=--enable-experimental-web-platform-features --unlimited-storage)
            browser_arguments = self.get_browser_arguments(config_section)
            for argument in browser_arguments:
                chrome_options.add_argument(argument)

            # accept self-signed certificates
            if self.shishito_support.get_opt('accept_ssl_cert').lower() == 'true':
                chrome_options.add_argument('--ignore-certificate-errors')

            capabilities.update(chrome_options.to_capabilities())

        elif browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
        if profile is None:
            return None

        # add extensions to remote driver
        if self.shishito_support.get_opt('with_extension'):
            # TODO: add support for extensions again
            # profile = self.add_extension_to_browser(browser_type, profile)
            pass

        # add Chrome options to desired capabilities
        if browser_type == 'chrome':
            chrome_capabilities = profile.to_capabilities()
            capabilities.update(chrome_capabilities)
            profile = None

        return profile

    def get_pytest_arguments(self, config_section):
        """ Get environment specific arguments for pytest.

        :param config_section: section in platform/environment.properties config
        :return: dict with arguments for pytest or None
        """
        pass

    def get_test_name(self):
        """ Return test name from the call stack, assuming there can be only
        one "test\_" file in the stack. If there are more it means two PyTest
        tests ran when calling get_test_name, which is invalid use case.

        :return: test name or project_name setting
        """

        frames = inspect.getouterframes(inspect.currentframe())
        for frame in frames:
            if re.match('test_.*', os.path.basename(frame[1])):
                return os.path.basename(frame[1])[:-3]

        return self.shishito_support.get_opt('project_name')
