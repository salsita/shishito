import inspect
import os
import re
import configparser
import base64
from selenium import webdriver
import json

OPTIONS = 'OPTIONS'
ARGUMENTS = 'ARGUMENTS'
EXTENSIONS = 'EXTENSIONS'

BROWSER_KEYWORDS = {  # map lowercase browser name to option keyword understood by chromedriver/geckodriver...
    'chrome': {
        OPTIONS: 'chromeOptions',
        ARGUMENTS: 'args',
        EXTENSIONS: 'extensions',
    },
    'firefox': {
        OPTIONS: 'moz:firefoxOptions',
        ARGUMENTS: 'args',
    }
}


class ShishitoEnvironment(object):

    """ Base class for test environment. """


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

    def get_experimental_arguments(self, config_section):
        """
        return array of browser command line arguments from config_section
            [Chrome]
            experimental_arguments=--mobileEmulation--{"deviceName": "Apple iPhone 6"}
            ...
        :param config_section: name of config section in web/*.properties (e.g. Chrome)
        :return: array
        """

        if config_section is None:
            return []

        try:
            arguments_string = self.shishito_support.get_opt(config_section, 'experimental_arguments')
        except configparser.NoOptionError:
            return []
        arguments = arguments_string.split('--')
        return arguments[1:]

    def get_browser_extensions(self, config_section):
        """
        Check browser config for 'extensions' parameter, if not found fallback to common config.
        Return array of browser extension files from config_section.
        If the extension name is a variable ( $VAR_NAME ), get the value from the environment
            [Chrome]
            extensions=/tmp/extensions/my-extension.crx  another_extension.crx
            ...
        :param config_section: name of config section in web/*.properties (e.g. Chrome)
        :return: array
        """

        extension_string = None
        extensions = []
        if config_section is not None:
            try:
                extension_string = self.shishito_support.get_opt(config_section, 'browser_extensions')  # browser config
            except configparser.NoOptionError:
                extension_string = None

        if extension_string is None:
            try:
                extension_string = self.shishito_support.get_opt('browser_extensions')                 # common config
            except configparser.NoOptionError:
                pass

        if extension_string is None:
            return []

        for item in re.split('\s+', extension_string):
            if item != '':
                m = re.match('^\$([A-Z][A-Z_]+)$', item)
                if m is not None:
                    var_name = m.group(1)
                    if var_name not in os.environ:
                        raise Exception("Error getting browser_extensions: env variable '" + item + "' not defined")
                    extensions.append(os.environ[var_name])  # take the extension path as configured
                else:
                    extensions.append(item)     # take the extension path as configured

        return extensions


    def add_cmdline_arguments_to_browser(self, browser_capabilities, config_section):
        """
        Add browser command line arguments to capabilities dict
        :param browser_capabilities: dict (see https://w3c.github.io/webdriver/webdriver-spec.html)
        :param config_section: name of the browser config section (e.g. 'Chrome')
        """

        browser_name = self.shishito_support.get_opt(config_section, 'browser').lower()
        arguments = self.get_browser_arguments(config_section)
        if arguments:
            try:
                options_kw = BROWSER_KEYWORDS[browser_name][OPTIONS]
                args_kw = BROWSER_KEYWORDS[browser_name][ARGUMENTS]
                browser_capabilities.setdefault(options_kw, {}).setdefault(args_kw, []).extend(arguments)
            except:
                pass


    def add_extensions_to_browser(self, browser_capabilities, config_section):
        """
        Add base64-encoded extensions to capabilities dict
        :param browser_capabilities: dict (see https://w3c.github.io/webdriver/webdriver-spec.html)
        :param config_section: name of the browser config section (e.g. 'Chrome')
        """

        browser_name = self.shishito_support.get_opt(config_section, 'browser').lower()
        extensions = self.get_browser_extensions(config_section)
        if extensions:
            try:
                options_kw = BROWSER_KEYWORDS[browser_name][OPTIONS]
                exts_kw = BROWSER_KEYWORDS[browser_name][EXTENSIONS]
                browser_capabilities.setdefault(options_kw, {}).setdefault(exts_kw, [])
            except:
                return

            for extension in extensions:
                with open(extension, 'rb') as ext_file:
                    extension_base64 = base64.b64encode(ext_file.read()).decode('UTF-8')
                browser_capabilities[options_kw][exts_kw].append(extension_base64)

    def add_experimental_option(self, browser_capabilities, config_section):
        browser_name = self.shishito_support.get_opt(config_section, 'browser').lower()
        arguments = self.get_experimental_arguments(config_section)
        if arguments and browser_name == 'chrome':
            chrome_options = webdriver.ChromeOptions()
            if('mobileEmulation' in arguments):
                index = arguments.index('mobileEmulation')
                chrome_options.add_experimental_option(arguments[index], json.loads(arguments[index+1]))
            return browser_capabilities.update(chrome_options.to_capabilities())
        return browser_capabilities

    def call_browser(self, config_section):
        """ Start webdriver for given config section."""
        raise NotImplementedError()

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
        get_opt = self.shishito_support.get_opt
        test_platform = self.shishito_support.test_platform
        if(test_platform == 'web'):
            capabilities = {
                'browserName': get_opt(config_section, 'browser').lower(),
                'version': get_opt(config_section, 'browser_version'),
                'resolution': get_opt(config_section, 'resolution'),
                'javascriptEnabled': True,
                'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'true',
            }
        if(test_platform == 'mobile'):
            capabilities = {
                'browserName': get_opt(config_section, 'browser').lower(),
                'javascriptEnabled': True,
                'acceptSslCerts': get_opt('accept_ssl_cert').lower() == 'true',
            }

        self.add_cmdline_arguments_to_browser(capabilities, config_section)
        self.add_extensions_to_browser(capabilities, config_section)
        self.add_experimental_option(capabilities, config_section)
        return capabilities


    def start_driver(self, browser_type, capabilities, config_section=None):
        """ Prepare selenium webdriver.

        :param str browser_type: type of browser for which prepare driver
        :param dict capabilities: capabilities used for webdriver initialization
        """

        raise NotImplementedError()


    def get_browser_profile(self, browser_type, capabilities, config_section=None):
        """ Return browser profile ready to be passed to driver.

        :param str browser_type: browser type (chrome, firefox, ..)
        :param dict capabilities: capabilities dict - can be updated
        :return: browser profile or None
        """

        # lowercase browser_type
        browser_type = browser_type.lower()
        profile = None

        if browser_type == 'firefox':
            profile = webdriver.FirefoxProfile()
            for ext in self.get_browser_extensions(config_section):
                profile.add_extension(ext)

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
