from shishito.library.modules.runtime.platform.shishito_execution import ShishitoExecution


class ControlExecution(ShishitoExecution):
    """ ControlExecution for mobile platform"""

    def get_test_result_prefix(self, config_section):
        platform = self.shishito_support.gid('platformName', config_section)
        platform_version = self.shishito_support.gid('platformVersion', config_section)

        return '[%s, %s, %s]' % (config_section, platform, platform_version)
