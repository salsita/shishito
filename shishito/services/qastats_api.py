# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Tomas Jirka
@summary: QAStats API functions
"""
import json
import re
import requests
import os

from shishito.reporting.reporter import Reporter
from shishito.runtime.shishito_support import ShishitoSupport


class QAStats(object):
    """ QAStats object """

    def __init__(self, user, password, timestamp, epoch, build):
        self.shishito_support = ShishitoSupport()
        self.qastats_base_url = self.shishito_support.get_opt('qastats_url')
        self.user = user
        self.password = password
        self.timestamp = timestamp
        self.epoch = epoch
        self.build = build

        # project specific config
        self.project_id = self.shishito_support.get_opt('qastats_project_id')

        # shishito results
        self.reporter = Reporter()
        self.shishito_results = self.reporter.get_xunit_test_cases(timestamp)

        self.default_headers = {'Content-Type': 'application/json'}
        self.result_url = self.qastats_base_url + '/api/v1/results'
        self.project_url = self.shishito_support.get_opt('base_url')

    def post_results(self):
        """ Create test-cases on QAStats, adds a new test run and update results for the run
            {
               "project_id": 123,
               "timestamp": 1470133472,
               "build": "773",              // optional
               "environment": "Firefox"     // optional
               "branch": "develop",         // optional
               "git": "ae232a",             // optional
               "results": [
                  { "test": "test_login", "result": "pass" },   // [pass fail err nr]
                  ...
               ],
            }
        """

        for (i, run) in enumerate(self.shishito_results):
            environment = run['name'];
            m =re.match('^(.*)\.xml$', environment)
            if m != None: environment = m.group(1)

            payload = {
                    'project_id': self.project_id,
                    'timestamp': self.epoch + i,
                    'environment': environment
            }
            if self.build:
                payload['build'] = self.build
            if 'QA_BRANCH_TO_TEST' in os.environ:
                payload['branch'] = os.environ['QA_BRANCH_TO_TEST']
            if 'QA_GIT_COMMIT' in os.environ:
                payload['git'] = os.environ["QA_GIT_COMMIT"]
            elif 'CIRCLE_REPOSITORY_URL' in os.environ:
                print('github url is known')
                payload['git'] = os.environ['CIRCLE_REPOSITORY_URL']
            if 'CIRCLE_TEST_REPORTS' in os.environ:
                print('result url is known')
                payload['reporturl'] = os.environ.get('CIRCLE_TEST_REPORTS')
            if self.project_url is not None:
                payload['testurl']=self.project_url
            status_map = {
                'error': 'err',
                'failure': 'fail',
                'success': 'pass',
                'skipped': 'nr'
            }
            results = [ {'test': t['name'], 'result': status_map[t['result']]} for t in run['cases'] ]
            payload['results'] = results
            print(payload)
            json_payload = json.dumps(payload)
            r = requests.post(self.result_url, auth=(self.user, self.password), data=json_payload,
                                 headers=self.default_headers)

            if r.status_code == requests.codes.ok:
                try:
                    resp = r.json()
                    if 'result' in resp and resp['result'] == 'OK':
                        print("Results uploaded to QAStats")
                        return True
                except (ValueError, AttributeError):
                    pass

            print("Error: uploading tests to QAStats\n\n", json_payload, "\n")
            print("\tStatus-code:\t" + str(r.status_code) + "\n")
            for n, v in r.headers.items():
                print("\t" + n + "\t" + v)
            print("")
            print(r.text)