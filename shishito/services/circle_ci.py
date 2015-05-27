# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
"""
import requests
import json
from shishito.runtime.shishito_support import ShishitoSupport
import os


class CircleAPI(object):
    """Handles communication with Circle CI via REST API"""

    def __init__(self):
        self.shishito_support = ShishitoSupport()
        self.api_token = self.shishito_support.get_opt('circleci_api_token')
        self.circle_username = self.shishito_support.get_opt('circleci_username')
        self.circle_project = self.shishito_support.get_opt('circleci_project')
        self.circle_branch = self.shishito_support.get_opt('circleci_branch')

    def collect_artifacts(self, destination_folder):
        """downloads build artifacts from CircleCI for latest build from specific branch"""
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        artifact_data = self.get_artifact_data()
        for artifact in artifact_data:
            self.save_artifact(artifact, destination_folder)
        return bool(os.listdir(destination_folder))

    def save_artifact(self, artifact, destination_folder):
        """ saves artifact into specified folder """
        file_name = artifact['url'].split('/')[-1]
        file_request_url = artifact['url'] + '?circle-token=' + self.api_token

        response = requests.get(file_request_url, stream=True)
        response.raise_for_status()

        with open(os.path.join(destination_folder, file_name), 'wb') as extension:
            for block in response.iter_content(1024):
                extension.write(block)

    def get_artifact_data(self):
        """returns json with artifact urls"""
        latest_dev_build_url = (
            'https://circleci.com/api/v1/project/{circle_username}/{circle_project}/tree/'
            '{circle_branch}?circle-token={api_token}&limit=1').format(**self.__dict__)

        headers = {'Accept': 'application/json'}
        response = requests.get(latest_dev_build_url, headers=headers)
        builds_json = json.loads(response.text)
        build_number = builds_json[0]['build_num']

        artifacts_url = (
            'https://circleci.com/api/v1/project/{circle_username}/'
            '{circle_project}/{build_number}/artifacts?circle-token={api_token}'
        ).format(build_number=build_number, **self.__dict__)

        response = requests.get(artifacts_url, headers=headers)
        return json.loads(response.text)
