from shishito.runtime.platform.shishito_execution import ShishitoExecution


class ControlExecution(ShishitoExecution):
    """ ControlExecution for node-webkit platform"""

    def get_test_result_prefix(self, config_section):
        """ Create string prefix for test results.

        :param str config_section: section in platform/environment.properties config
        :return: str with test result prefix
        """

        return 'node_webkit'

    def run_tests(self):
        """ Trigger PyTest runner. Run PyTest for for node-webkit tests. """

        return self.trigger_pytest('node_webkit')
