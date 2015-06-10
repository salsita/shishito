# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: TestRail API functions
"""
import json

import requests

from shishito.reporting.reporter import Reporter
from shishito.runtime.shishito_support import ShishitoSupport


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

    def post_results(self):
        """ Create test-cases on TestRail, adds a new test run and update results for the run """
        self.create_missing_test_cases()
        test_run = self.add_test_run()
        self.add_test_results(test_run)

    def tr_get(self, url):
        """ GET request for TestRail API

        :param url: url endpoint snippet
        :return: response JSON
        """
        return requests.get(self.uri_base + url, auth=(self.user, self.password), headers=self.default_headers).json()

    def tr_post(self, url, payload):
        """ GET request for TestRail API

        :param url: url endpoint snippet
        :param payload: payload for the POST api call
        :return: response object
        """
        return requests.post(self.uri_base + url, auth=(self.user, self.password), data=json.dumps(payload),
                             headers=self.default_headers)

    def get_all_test_cases(self):
        """ Gets list of all test-cases from certain project

        :return: list of test-cases (names = strings)
        """
        test_case_list = self.tr_get('get_cases/{}&section_id={}'.format(self.project_id, self.section_id))
        return [{'title': test_case['title'], 'id': test_case['id']} for test_case in test_case_list]

    def create_test_case(self, title):
        """ Creates a new test case in TestRail

        :param title: Title of the test-case
        :return: response object
        """
        return self.tr_post('add_case/{}'.format(self.section_id), {"title": title})

    def create_missing_test_cases(self):
        """ Creates new test-cases on TestRail for those in test project (those run by pytest).
         Does not create test-cases if already existed on TestRail.

        :return: list of test-cases that could not be created on TestRail (post failure)
        """
        post_errors = []
        test_case_names = [item['title'] for item in self.get_all_test_cases()]
        # Iterate over results for each environment combination
        for result_combination in self.shishito_results:
            # Create TestRail entry for every test-case in combination (if missing)
            for item in result_combination['cases']:
                if item['name'] not in test_case_names:
                    response = self.create_test_case(item['name'])
                    if response.status_code != requests.codes.ok:
                        post_errors.append(item['name'])
                    else:
                        test_case_names.append(item['name'])
        return post_errors

    def add_test_run(self):
        """ Adds new test run under certain test plan into TestRail

        :return: dictionary of TestRail run names & IDs
        """
        runs_created = []
        # Iterate over results for each environment combination
        for result_combination in self.shishito_results:
            run_name = '{} ({})'.format(result_combination['name'][:-4], self.timestamp)
            test_run = {"case_ids": [case['id'] for case in self.get_all_test_cases()]}
            result = self.tr_post('add_plan_entry/{}'.format(self.test_plan_id),
                                  {"suite_id": self.suite_id, "name": run_name, "runs": [test_run]}).json()
            # lookup test run id
            for run in result['runs']:
                if run['name'] == run_name:
                    runs_created.append({'combination': result_combination['name'], 'id': run['id']})
        return runs_created

    def add_test_results(self, test_runs):
        """ Add test results for specific test run based on parsed xUnit results

        :return: list of test run IDs for which results could not be added (post failure)
        """
        post_errors = []
        run_ids = {r['combination']: r['id'] for r in test_runs}
        # Iterate over results for each environment combination
        for result in self.shishito_results:
            run_id = run_ids.get(result['name'])
            if not run_id:
                continue

            test_results = []
            tr_tests = {t['title']: t['id'] for t in self.tr_get('get_tests/{}'.format(run_id))}
            # Create TestRail entry for every test-case in combination (if missing)
            for xunit_test in result['cases']:
                tr_test_id = tr_tests.get(xunit_test['name'])
                result_id = {'success': 1, 'failure': 5}.get(xunit_test['result'])
                if tr_test_id and result_id:
                    test_results.append({'test_id': tr_test_id, 'status_id': result_id})

            response = self.tr_post('add_results/{}'.format(run_id), {'results': test_results})
            if response.status_code != requests.codes.ok:
                post_errors.append(run_id)
        return post_errors
