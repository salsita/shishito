"""
@author: Irina
@summary: Functions that operate over BrowserStack API
"""
import json
import requests
import sys
import time


class BrowserStackAPI():
    def __init__(self):
        pass

    def get_projects(self, auth):
        url = "https://browserstack.com/automate/projects.json"
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        return json_res

    def get_project(self, auth, project_name):
        projects = self.get_projects(auth)
        project_id = None
        for i in range(0, len(projects)):
            if projects[i]['automation_project']['name'] == project_name:
                project_id = projects[i]['automation_project']['id']
                url = "https://browserstack.com/automate/projects/%s.json" % project_id
                r = requests.get(url, auth=auth)
                break
        if project_id is None:
            project = None
        else:
            project = json.loads(r.text)
        return project

    def get_builds(self, auth):
        url = "https://browserstack.com/automate/builds.json"
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        return json_res

    def get_build_hash_id(self, auth, build_name):
        builds = self.get_builds(auth)
        hashed_id = None
        for i in range(0, len(builds)):
            if builds[i]['automation_build']['name'] == build_name:
                hashed_id = builds[i]['automation_build']['hashed_id']
        if hashed_id is None:
            hashed_id = None
        return hashed_id

    def get_sessions(self, auth, build_name):
        hashed_id = self.get_build_hash_id(auth, build_name)
        url = "https://browserstack.com/automate/builds/%s/sessions.json" % hashed_id
        r = requests.get(url, auth=auth)
        sessions = json.loads(r.text)
        return sessions

    def get_session(self, auth, build_name, status):
        sessions = self.get_sessions(auth, build_name)
        session = None
        for i in range(0, len(sessions)):
            if sessions[i]['automation_session']['status'] == status:
                session = sessions[i]['automation_session']
        if session is None:
            session = None
        return session

    def get_session_link(self, session):
        if session is not None:
            link = session['logs']
            link = link[:-4]
        else:
            link = None
        return link

    def get_session_hashed_id(self, session):
        if session is not None:
            hashed_id = session['hashed_id']
        else:
            hashed_id = None
        return hashed_id

    def is_session_available(self, auth):
        url = "https://www.browserstack.com/automate/plan.json"
        r = requests.get(url, auth=auth)
        session = json.loads(r.text)
        session_running = session["parallel_sessions_running"]
        session_all = session["parallel_sessions_max_allowed"]
        if int(session_all) - int(session_running) > 0:
            session = True
        else:
            session = False
        return session

    def change_status(self, auth, session_id):
        url = "https://www.browserstack.com/automate/sessions/%s.json" % session_id
        status = {'status': 'error'}
        headers = {'content-type': 'application/json'}
        requests.put(url, auth=auth, data=json.dumps(status), headers=headers)

    def wait_for_free_sessions(self, auth, wait_total, wait_delay):
        """ Waits for BrowserStack session to be available """
        wait_steps = int(wait_total) / int(wait_delay)
        counter = 0
        session_available = self.is_session_available(auth)
        while not session_available:
            print('No BrowserStack session available. Waiting for ' + str(wait_delay) + ' minutes...')
            if counter >= wait_steps:
                sys.exit('No BrowserStack session got available'
                         ' after ' + str(wait_total) + ' minutes. No test will be executed.')
            counter += 1
            time.sleep(int(wait_delay) * 60)
            session_available = self.is_session_available(auth)
        return session_available