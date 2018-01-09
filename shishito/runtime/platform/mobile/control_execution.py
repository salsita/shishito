from shishito.runtime.platform.shishito_execution import ShishitoExecution


class ControlExecution(ShishitoExecution):
    """ ControlExecution for mobile platform"""

    def get_test_result_prefix(self, config_section):
        """ Create string prefix for test results.

        :param str config_section: section in platform/environment.properties config
        :return: str with test result prefix
        """
        test_env = self.shishito_support.get_opt('test_environment')
        if(test_env == 'browserstack'):
            platform = self.shishito_support.get_opt(config_section, 'platform')
            device = self.shishito_support.get_opt(config_section, 'device')
            browser = self.shishito_support.get_opt(config_section, 'browser')

            return '[%s, %s, %s, %s]' % (config_section, platform, device, browser)
        if(test_env == 'appium'):
            platform = self.shishito_support.get_opt(config_section, 'platformName')
            platform_version = self.shishito_support.get_opt(config_section, 'platformVersion')

            return '[%s, %s, %s]' % (config_section, platform, platform_version)

        if (test_env == 'appium_bs'):
            os_version = self.shishito_support.get_opt(config_section, 'os_version')
            device = self.shishito_support.get_opt(config_section, 'device')
            return '[%s, %s, %s]' % (config_section, os_version, device)

