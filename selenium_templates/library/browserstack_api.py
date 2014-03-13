"""
@author: Irina
@summary: Functions that operate over BrowserStack API
"""
import json
import requests


class BrowserStackAPI():

    def get_projects(self, auth):
        url = "https://browserstack.com/automate/projects.json"
        r = requests.get(url, auth=auth)
        json_res = json.loads(r.text)
        return json_res

    def get_project(self, auth, project_name):
        projects = self.get_projects(auth)
        id = None
        for i in range(0, len(projects)):
            if (projects[i]['automation_project']['name'] == project_name):
                id = projects[i]['automation_project']['id']
                url = "https://browserstack.com/automate/projects/%s.json" % (id)
                r = requests.get(url, auth=auth)
                break
                #print r.text
        if (id == None):
            project = "Can't find project with such name"
        else:
            project = json.loads(r.text)
        return project

    def get_builds(self, auth):
        url = "https://browserstack.com/automate/builds.json"
        r = requests.get(url, auth=auth)
        #print r.text
        json_res = json.loads(r.text)
        return json_res

    def get_build_hash_id(self, auth, build_name):
        builds = self.get_builds(auth)
        hashed_id = None
        for i in range(0, len(builds)):
            if (builds[i]['automation_build']['name'] == build_name):
                hashed_id = builds[i]['automation_build']['hashed_id']
        if (hashed_id == None):
            hashed_id = "Can't find build_id for provided build name"
        return hashed_id

    def get_sessions(self, auth, build_name):
        hashed_id = self.get_build_hash_id(auth, build_name)
        url = "https://browserstack.com/automate/builds/%s/sessions.json" % (hashed_id)
        r = requests.get(url, auth=auth)
        #print r.text
        sessions = json.loads(r.text)
        #for i in range(0, len(sessions)):
        #print sessions[i]['automation_session']
        return sessions

    def get_session(self, auth, build_name, status):
        sessions = self.get_sessions(auth, build_name)
        session = None
        for i in range(0, len(sessions)):
            if (sessions[i]['automation_session']['status'] == status):
                session = sessions[i]['automation_session']
        if (session == None):
            session = 0
        return session

    def get_session_link(self, session):
        if (session != 0):
            link = session['logs']
            link = link[:-4]
        else:
            link = "Not found session"
        return link

    def get_session_hashed_id(self, session):
        if (session != 0):
            hashed_id = session['hashed_id']
        else:
            hashed_id = "Not found session"
        return hashed_id

    def get_session_running(self, auth):
        url = "https://www.browserstack.com/automate/plan.json"
        r = requests.get(url, auth=auth)
        print r.text
        session = json.loads(r.text)
        session_run = session["parallel_sessions_running"]
        session_all = session["parallel_sessions_max_allowed"]
        if (int(session_all) - int(session_run) > 0):
            session = 0
        else:
            session = 1
        return session

    def change_status(self, auth, session_id):
        url = "https://www.browserstack.com/automate/sessions/%s.json" % session_id
        status = {'status': 'error'}
        headers = {'content-type': 'application/json'}
        requests.put(url, auth=auth, data=json.dumps(status), headers=headers)