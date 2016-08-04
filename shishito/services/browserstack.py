"""
@author: Irina
@summary: Functions that operate over BrowserStack API
"""
import json
import requests
import sys
import time


class BrowserStackAPI(object):

    def request_get_verify(self, auth, url):
        '''
        Returns the response from Browserstack API, if the status code is 200.
        Retries 5 times before failing completely
        :param auth: Browserstack authorization (tuple)
        :param url: API url
        :return: Response from Browserstack (or raise Connection Error)
        '''

        response = None

        for attempt in range(5):

            response = requests.get(url, auth=auth)
            if response.status_code == 200:
                return response

            else:
                print("Browserstack responded with {0} status code".format(response.status_code))
                time.sleep(1)

        #attempts depleted
        raise ConnectionError('Cannot get valid response from Browserstack. Latest status code = {0}'.format(response.status_code))

    def get_projects(self, auth):
        url = "https://www.browserstack.com/automate/projects.json"
        r = self.request_get_verify(auth, url)
        return r.json()


    def get_project(self, auth, project_name):
        for project in self.get_projects(auth):
            if project['automation_project']['name'] == project_name:
                project_id = project['automation_project']['id']
                url = "https://browserstack.com/automate/projects/%s.json" % project_id
                r = self.request_get_verify(auth, url)
                return r.json()

    def get_builds(self, auth):
        url = "https://www.browserstack.com/automate/builds.json"
        r = self.request_get_verify(auth, url)
        return r.json()

    def get_build_hash_id(self, auth, build_name):
        for build in self.get_builds(auth):
            if build['automation_build']['name'] == build_name:
                return build['automation_build']['hashed_id']

    def get_sessions(self, auth, build_name):
        hashed_id = self.get_build_hash_id(auth, build_name)
        url = "https://www.browserstack.com/automate/builds/%s/sessions.json" % hashed_id
        r = self.request_get_verify(auth, url)
        return r.json()

    def get_session(self, auth, build_name, status):
        for session in self.get_sessions(auth, build_name):
            automation_session = session['automation_session']
            if automation_session['status'] == status:
                return automation_session

    def get_session_link(self, session):
        if session:
            session_link = session['logs'][:-4]
            print(session_link) #Printing to stdout, so that it can be added to test report
            return session_link

    def get_session_hashed_id(self, session):
        return session['hashed_id'] if session else None

    def is_session_available(self, auth):
        url = "https://www.browserstack.com/automate/plan.json"
        r = self.request_get_verify(auth, url)
        session = r.json()
        session_running = session["parallel_sessions_running"]
        session_all = session["parallel_sessions_max_allowed"]
        return int(session_all) - int(session_running)

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
            print('No BrowserStack session available. Waiting for %s minutes...' % wait_delay)
            if counter >= wait_steps:
                sys.exit('No BrowserStack session got available'
                         ' after %s minutes. No test will be executed.' % wait_total)
            counter += 1
            time.sleep(int(wait_delay) * 60)
            session_available = self.is_session_available(auth)
        return session_available
