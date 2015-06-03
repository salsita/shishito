from shishito.reporting.reporter import Reporter
from shishito.runtime.shishito_support import ShishitoSupport

__author__ = 'vojta'

import json

import requests


class TestRail(object):
    """ TestRail object """

    def __init__(self, user, password, timestamp):
        self.shishito_support = ShishitoSupport()
        self.test_rail_instance = self.shishito_support.get_opt('test_rail_url')
        self.user = user
        self.password = password
        self.timestamp = timestamp

        # project specific config
        self.project_id = self.shishito_support.get_opt('test_rail_project_id')
        self.section_id = self.shishito_support.get_opt('test_rail_section_id')
        self.test_plan_id = self.shishito_support.get_opt('test_rail_test_plan_id')
        self.suite_id = self.shishito_support.get_opt('test_rail_suite_id')

        # shishito results
        self.reporter = Reporter()
        self.shishito_results = self.reporter.get_xunit_test_cases(timestamp)

        self.default_headers = {'Content-Type': 'application/json'}
        self.uri_base = self.test_rail_instance + '/index.php?/api/v2/'

    # GET request for TestRail API
    def tr_get(self, url):
        """ GET request for TestRail API
        :param url: url endpoint snippet
        :return: response JSON
        """
        return requests.get(self.uri_base + url, auth=(self.user, self.password), headers=self.default_headers).json()

    # POST request for TestRail API
    def tr_post(self, url, payload):
        """ GET request for TestRail API
        :param url: url endpoint snippet
        :param payload: payload for the POST api call
        :return: response object
        """
        return requests.post(self.uri_base + url, auth=(self.user, self.password), data=json.dumps(payload),
                             headers=self.default_headers)

    def get_all_test_cases(self, project_id):
        """ Gets list of all test-cases from certain project
        :param project_id: TestRail project ID
        :return: list of test-cases (names = strings)
        """
        test_case_list = self.tr_get('get_cases/{}'.format(project_id))
        return [{'title': test_case['title'], 'id': test_case['id']} for test_case in test_case_list]

    def create_test_case(self, title, section_id):
        """ Creates a new test case in TestRail
        :param title: Title of the test-case
        :param section_id: Section ID in which test-case should belong
        :return: response object
        """
        return self.tr_post('add_case/{}'.format(section_id), {"title": title})

    def create_missing_test_cases(self, project_id, section_id):
        """ Creates new test-cases on TestRail for those in test project (those run by pytest).
         Does not create test-cases if already existed on TestRail.
        :param project_id: TestRail project ID
        :param section_id: TestRail test-case section ID (~ category, e.g. "Smoke tests")
        :return: list of test-cases that could not be created on TestRail (post failure)
        """
        post_errors = []
        test_case_names = [item['title'] for item in self.get_all_test_cases(project_id)]
        for result_combination in self.shishito_results:
            for item in result_combination['cases']:
                if item['name'] not in test_case_names:
                    response = self.create_test_case(item['name'], section_id)
                    if response.status_code != requests.codes.ok:
                        post_errors.append(item['name'])
                    else:
                        test_case_names.append(item['name'])
        return post_errors

    def add_test_run(self, project_id, test_plan_id, suite_id):
        """ Adds new test run under certain test plan into TestRail
        :param test_plan_id: TestRail test plan ID
        :param suite_id: TestRail test suite ID
        :param test_run_name: Name of the test run
        :param test_case_ids: List of IDs of test-cases to be added into test run
        :return: dictionary of TestRail run names & IDs
        """
        runs_created = []
        for result_combination in self.shishito_results:
            run_name = '{} ({})'.format(result_combination['name'][:-4], self.timestamp)
            test_run = {"case_ids": [case['id'] for case in self.get_all_test_cases(project_id)]}
            result = self.tr_post('add_plan_entry/{}'.format(test_plan_id),
                                  {"suite_id": suite_id, "name": run_name, "runs": [test_run]}).json()
            # lookup test run id
            for run in result['runs']:
                if run['name'] == run_name:
                    runs_created.append({'combination': result_combination['name'], 'id': run['id']})
        return runs_created

    def add_test_results(self, test_runs):
        """ Add test results for specific test run based on parsed xUnit results
        :param test_run_id: TestRail test run ID
        :return: list of test run IDs for which results could not be added (post failure)
        """
        post_errors = []
        for run in test_runs:
            test_results = []
            tr_tests = self.tr_get('get_tests/{}'.format(run['id']))
            for result_combination in self.shishito_results:
                if result_combination['name'] == run['combination']:
                    for xunit_test in result_combination['cases']:
                        for test_rail_test in tr_tests:
                            if xunit_test['name'] == test_rail_test['title']:
                                result_id = None
                                if xunit_test['result'] == 'success':
                                    result_id = 1
                                elif xunit_test['result'] == 'failure':
                                    result_id = 5
                                if result_id:
                                    test_results.append({'test_id': test_rail_test['id'], 'status_id': result_id})
                    response = self.tr_post('add_results/{}'.format(run['id']), {'results': test_results})
                    if response.status_code != requests.codes.ok:
                        post_errors.append(run['id'])
        return post_errors
