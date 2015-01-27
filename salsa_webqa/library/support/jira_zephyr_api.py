"""
@author: Irina Gvozdeva
@summary: Functions that operate over ZAPI API
"""
import json
import requests
from datetime import datetime, timedelta

jira_server = "https://jira.salsitasoft.com"
execution_status = {"PASS": 1, "FAIL": 2, "WIP": 3, "BLOCKED": 4, "UNEXECUTED": -1}


class ZAPI(object):

    def get_projects(self, auth):
        #Get projects from JIRA
        url = "%s/rest/zapi/latest/util/project-list" % jira_server
        r = requests.get(url, auth=auth)
        return r.json["options"]

    def get_project_id(self, project_name, auth):
        #Get project id based on project name
        for project in self.get_projects(auth):
            if project["label"] == project_name:
                return project["value"]

    def get_project_versions(self, project_name, auth):
        #Get project versions, based on project name
        project_id = self.get_project_id(project_name, auth)
        url = "%s/rest/zapi/latest/util/versionBoard-list" % jira_server
        parameters = {"projectId": project_id, "showUnscheduled": "True"}
        r = requests.get(url, auth=auth, params=parameters)
        return r.json

    def get_version_id(self, project_name, version_name, auth):
        #Get version id based on project name and version name
        versions = self.get_project_versions(project_name, auth)
        for version in versions["unreleasedVersions"]:
            if version["label"] == version_name:
                return version["value"]

    # Cycle api
    # Not used !!!
    def get_project_cycles(self, project_name, version, auth):
        #Get project cycle based on project name and version name
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version, auth)
        url = "%s/rest/zapi/latest/cycle" % jira_server
        parameters = {"projectId": project_id, "versionId": version_id, "offset": 0, "expand": "executionSummaries"}
        r = requests.get(url, auth=auth, params=parameters)
        json_res = r.json
        test_cycle = {}
        for i in json_res.items():
            if i[0].isdigit():
                test_cycle[i[0]] = [i[1]]
        return test_cycle

    def get_cycle_execution_tests(self, cycle_id, auth):
        # Get all executions for cycle with id
        url = "%s/rest/zapi/latest/execution?cycleId=%s" % (jira_server, cycle_id)
        r = requests.get(url, auth=auth)
        json_res = r.json
        return json_res.get('executions', [])

    def get_issueid(self, cycle_id, jira_id, auth):
        # Get issue id based on id from Jira
        issues = self.get_cycle_execution_tests(cycle_id, auth)
        for issue in issues:
            if issue["issueKey"] == jira_id:
                return issue["issueId"]

    def create_new_test_cycle(self, cycle_name, project_name, version_name, auth):
        # Create new test cycle, based on project and version names
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        today = datetime.now()
        end_date = today + timedelta(days=30)
        url = "%s/rest/zapi/latest/cycle" % jira_server
        data = {
            "clonedCycleId": "",
            "name": cycle_name,
            "build": "",
            "environment": "",
            "description": "",
            "startDate": today.strftime("%d/%b/%y"),
            "endDate": end_date.strftime("%d/%b/%y"),
            "projectId": project_id,
            "versionId": version_id
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        return r.json["id"] #cycle_id

    def copy_test_cycle(self, cycle_id, cycle_name, project_name, version_name, auth):
        #Copy existing test cycle -didn't use it yet
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        today = datetime.now()
        end_date = today + timedelta(days=30)
        url = "%s/rest/zapi/latest/cycle" % jira_server
        data = {
            "clonedCycleId": cycle_id,
            "name": cycle_name,
            "build": "",
            "environment": "",
            "description": "",
            "startDate": today.strftime("%d/%b/%y"),
            "endDate": end_date.strftime("%d/%b/%y"),
            "projectId": project_id,
            "versionId": version_id
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        return r.json["id"] #cycle_id

    def delete_test_cycle(self, cycle_id, auth):
        #Delete existing test cycle use it's id
        url = "%s/rest/zapi/latest/cycle/%s" % (jira_server, cycle_id)
        r = requests.get(url, auth=auth)
        if "Error" not in r.json:
            url = "%s/rest/zapi/latest/cycle/%s" % (jira_server, cycle_id)
            r = requests.delete(url, auth=auth)
            return r.json

    #Execution API
    def add_new_execution(self, project_name, version_name, cycle_id, issue_id, auth):
        # Add new execution to cycle
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        url = "%s/rest/zapi/latest/execution" % jira_server
        data = {
            "issueId": issue_id,
            "versionId": version_id,
            "cycleId": cycle_id,
            "projectId": project_id
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        return r.json.keys()[0] #Strange!!!

    def add_tests_to_cycle(self, issue_keys, project_name, version_name, cycle_id, auth):
        project_id = self.get_project_id(project_name, auth)
        version_id = self.get_version_id(project_name, version_name, auth)
        url = "%s/rest/zapi/latest/execution/addTestsToCycle" % jira_server
        data = {
            "issues": issue_keys,
            "versionId": version_id,
            "cycleId": cycle_id,
            "projectId": project_id,
            "method": "1"
        }
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        return r.json

    def get_execution_id(self, execution_id, auth):
        url = jira_server + "/rest/zapi/latest/execution/%s" % execution_id
        r = requests.get(url, auth=auth)
        return r.json

    def get_execution_test(self, issue_id, auth):
        # Get all executions for issue_id
        url = "%s/rest/zapi/latest/execution/" % jira_server
        parameters = {"issueId": issue_id}
        r = requests.get(url, auth=auth, params=parameters)
        return r.json

    def update_execution_status(self, execution_id, status, auth):
        #Update execution status
        url = "%s/rest/zapi/latest/execution/%s/quickExecute" % (jira_server, execution_id)
        data = {'status': execution_status[status]}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=auth, data=json.dumps(data), headers=headers)
        return r.status_code
