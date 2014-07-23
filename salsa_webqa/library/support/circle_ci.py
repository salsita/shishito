# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
"""
import requests
import json
from salsa_webqa.library.control_test import ControlTest
import os


class CircleAPI():
    """ Handles communication with Circle CI via REST API """

    def __init__(self):
        self.test_control = ControlTest()
        self.api_token = self.test_control.gid('circleci_api_token')
        self.circle_username = self.test_control.gid('circleci_username')
        self.circle_project = self.test_control.gid('circleci_project')
        self.circle_branch = self.test_control.gid('circleci_branch')

    def collect_artifacts(self, destination_folder):
        """ downloads build artifacts from CircleCI for latest build from specific branch """
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        artifact_data = self.get_artifact_data()
        for artifact in artifact_data:
            self.save_artifact(artifact, destination_folder)

    def save_artifact(self, artifact, destination_folder):
        """ saves artifact into specified folder """
        file_name = artifact['url'].split('/')[-1]
        file_request_url = artifact['url'] + '?circle-token=' + self.api_token
        extension = open(os.path.join(destination_folder, file_name), 'wb')
        response = requests.get(file_request_url, stream=True)

        if not response.ok:
            # Something went wrong
            print 'error'

        for block in response.iter_content(1024):
            if not block:
                break

            extension.write(block)
        extension.close()

    def get_artifact_data(self):
        """ returns json with artifact urls """
        latest_dev_build_url = 'https://circleci.com/api/v1/project/' + self.circle_username + '/' \
                               + self.circle_project + '/tree/' + self.circle_branch + '?circle-token=' \
                               + self.api_token + '&limit=1'

        headers = {'Accept': 'application/json'}
        response = requests.get(latest_dev_build_url, headers=headers)
        builds_json = json.loads(response.text)
        build_number = int(builds_json[0]['build_num'])

        artifacts_url = 'https://circleci.com/api/v1/project/' + self.circle_username + '/' \
                        + self.circle_project + '/' + str(build_number) + '/artifacts?circle-token=' + self.api_token
        response = requests.get(artifacts_url, headers=headers)
        return json.loads(response.text)