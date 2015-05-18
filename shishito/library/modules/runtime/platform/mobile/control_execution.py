# -*- coding: utf-8 -*-
import os
import pytest

from shishito.library.modules.runtime.platform.shishito_execution import ShishitoExecution


class ControlExecution(ShishitoExecution):
    """ App control execution """

    def run_tests(self):
        """ Triggers PyTest runner.
        It runs PyTest for each BS combination, taken from versioned .properties file """

        # check that runner is not run directly
        test_status = 0

        for config_section in self.shishito_support.env_config.sections():
            print 'Running combination: ' + config_section
            test_status = self.trigger_pytest(config_section)

        return test_status

    def trigger_pytest(self, config_section):
        """ Runs PyTest runner on specific configuration """

        platform = self.shishito_support.gid('platformName', config_section)
        platform_version = self.shishito_support.gid('platformVersion', config_section)

        junit_xml_path = os.path.join(self.result_folder, config_section + '.xml')
        html_path = os.path.join(self.result_folder, config_section + '.html')

        test_result_prefix = '[%s, %s, %s]' % (config_section, platform, platform_version)

        # prepare pytest arguments into execution list
        pytest_arguments_dict = {
            '--test_platform=': '--test_platform=' + self.shishito_support.test_platform,
            '--test_environment=': '--test_environment=' + self.shishito_support.test_environment,
            '--environment_configuration=': '--environment_configuration=' + config_section,
            '--junitxml=': '--junitxml=' + junit_xml_path,
            '--junit-prefix=': '--junit-prefix=' + test_result_prefix,
            '--html=': '--html=' + html_path,
            '--html-prefix=': '--html-prefix=' + test_result_prefix,
            '--instafail': '--instafail',
        }

        # extend pytest_arguments with environment specific args
        extra_pytest_arguments = self.environment.get_pytest_arguments(config_section)
        if extra_pytest_arguments:
            pytest_arguments_dict.update(extra_pytest_arguments)

        test_directory = self.shishito_support.gid('test_directory')
        if not test_directory:
            test_directory = 'tests'

        pytest_arguments = [
            os.path.join(self.shishito_support.project_root, test_directory),
        ]

        pytest_arguments.extend(pytest_arguments_dict.values())

        # set pytest parallel execution argument
        parallel_tests = int(self.shishito_support.gid('parallel_tests'))
        if parallel_tests > 1:
            pytest_arguments.extend(['-n', str(parallel_tests)])

        # set pytest smoke test argument
        smoke = self.shishito_support.gid('smoke')
        if smoke:
            pytest_arguments.extend(['-m', 'smoke'])

        return pytest.main(pytest_arguments)
