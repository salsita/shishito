""" report test results in HTML format
author: Irina Gvozdeva
Based on initial code from Ross Lawley and mozilla selenium report generating.
"""

import py
from py.xml import html
from py.xml import raw
import pkg_resources
import os
import time
import datetime
import cgi
import shutil

def mangle_testnames(names):
    names = [x.replace(".py", "") for x in names if x != '()']
    names[0] = names[0].replace("/", '.')
    #print("names %s" %names)
    return names

class LogHTML(object):
    def __init__(self, logfile, prefix):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.prefix = prefix
        self.tests = []
        self.passed = self.skipped = 0
        self.failed = self.errors = 0
        self.test_logs = []
        self.errors = self.failed = 0
        self.passed = self.skipped = 0
        self.xfailed = self.xpassed = 0
        self.resources = ('style.css', 'jquery.js', 'main.js')

    def _make_report_dir(self):
        logfile_dirname = os.path.dirname(self.logfile)
        if logfile_dirname and not os.path.exists(logfile_dirname):
            os.makedirs(logfile_dirname)
        # copy across the static resources
        for file in self.resources:
            shutil.copyfile(
                pkg_resources.resource_filename(
                    __name__, os.path.sep.join(['resources', file])),
                os.path.abspath(os.path.join(logfile_dirname, file)))
        return logfile_dirname

    def _write_captured_output(self, report):
        sec = dict(report.sections)
        output=""
        for name in ('out', 'err'):
            content = sec.get("Captured std%s" % name)
            if content:
                output=output+content
        return output


    def append_pass(self, report):
        self.passed += 1
        self._appendrow('Passed', report)

    def append_failure(self, report):
        if "xfail" in report.keywords:
            self._appendrow('XPassed', report)
            self.xpassed += 1
        else:
            self._appendrow('Failed', report)
            self.failed += 1

    def append_error(self, report):
        self._appendrow('Error', report)
        self.errors += 1

    def append_skipped(self, report):
        if "xfail" in report.keywords:
            self._appendrow('XFailed', report)
            self.xfailed += 1
        else:
            self._appendrow('Skipped', report)
            self.skipped += 1

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == 'call':
                self.append_pass(report)
        elif report.failed:
            if report.when != "call":
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self.append_skipped(report)

    def pytest_sessionstart(self):
        self.suite_start_time = time.time()

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep("-", "generated html file: %s" % (self.logfile))

    def pytest_sessionfinish(self, session, exitstatus, __multicall__):
        self._make_report_dir()
        logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed
        generated = datetime.datetime.now()
        doc = html.html(
            html.head(
                html.meta(charset='utf-8'),
                html.title('Test Report'),
                html.link(rel='stylesheet', href='style.css'),
                html.script(src='jquery.js'),
                html.script(src='main.js')),

            html.body(
                html.p('Report generated on %s at %s ' % (
                    generated.strftime('%d-%b-%Y'),
                    generated.strftime('%H:%M:%S'),
                    )),
                #html.h2('Configuration'),
                #html.table(
                    ##[html.tr(html.td(k), html.td(v)) for k, v in sorted(configuration.items()) if v],
                    #id='configuration'),
                html.h2('Summary'),
                html.p(
                    '%i tests ran in %i seconds.' % (numtests, suite_time_delta),
                    html.br(),
                    html.span('%i passed' % self.passed, class_='passed'), ', ',
                    html.span('%i skipped' % self.skipped, class_='skipped'), ', ',
                    html.span('%i failed' % self.failed, class_='failed'), ', ',
                    html.span('%i errors' % self.errors, class_='error'), '.',
                    html.br(),),
                    #commented on future usage
                    #html.span('%i expected failures' % self.xfailed, class_='skipped'), ', ',
                    #html.span('%i unexpected passes' % self.xpassed, class_='failed'), '.'),
                html.h2('Results'),
                html.table([
                    html.thead(html.tr([
                        html.th('Result', class_='sortable', col='result'),
                        html.th('Class', class_='sortable', col='class'),
                        html.th('Name', class_='sortable', col='name'),
                        html.th('Duration', class_='sortable numeric', col='duration'),
                        #html.th('Output')]), id='results-table-head'),
                        html.th('Links to BrowserStack')]), id='results-table-head'),
                    html.tbody(*self.test_logs, id='results-table-body')], id='results-table')))
        logfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' + doc.unicode(indent=2))
        logfile.close()

    def _appendrow(self, result, report):
        names=mangle_testnames(report.nodeid.split("::"))
        testclass=(names[:-1])
        if self.prefix:
            testclass.insert(0, self.prefix)
        testclass=".".join(testclass)
        testmethod=names[-1]
        time = getattr(report, 'duration', 0.0)
        '''
        links = {}

        if hasattr(report, 'debug') and any(report.debug.values()):
            (relative_path, full_path) = self._debug_paths(testclass, testmethod)

            if report.debug['screenshots']:
                filename = 'screenshot.png'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(base64.decodestring(report.debug['screenshots'][-1]))
                links.update({'Screenshot': os.path.join(relative_path, filename)})

            if report.debug['html']:
                filename = 'html.txt'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(report.debug['html'][-1])
                links.update({'HTML': os.path.join(relative_path, filename)})

            # Log may contain passwords, etc so we only capture it for tests marked as public
            if report.debug['logs'] and 'public' in report.keywords:
                filename = 'log.txt'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(report.debug['logs'][-1])
                links.update({'Log': os.path.join(relative_path, filename)})

            if report.debug['network_traffic']:
                filename = 'networktraffic.json'
                f = open(os.path.join(full_path, filename), 'wb')
                f.write(report.debug['network_traffic'][-1])
                links.update({'Network Traffic': os.path.join(relative_path, filename)})

            if report.debug['urls']:
                links.update({'Failing URL': report.debug['urls'][-1]})

        self.sauce_labs_job = None
        if self.config.option.sauce_labs_credentials_file and getattr(report, 'session_id', None):
            self.sauce_labs_job = sauce_labs.Job(report.session_id)
            links['Sauce Labs Job'] = self.sauce_labs_job.url

        links_html = []
        for name, path in links.iteritems():
            links_html.append(html.a(name, href=path, target='_blank'))
            links_html.append(' ')'''

        additional_html = []

        if not 'Passed' in result:
            '''
            if self.sauce_labs_job:
                additional_html.append(self.sauce_labs_job.video_html)

            if 'Screenshot' in links:
                additional_html.append(
                    html.div(
                        html.a(html.img(src=links['Screenshot']),
                               href=links['Screenshot']),
                        class_='screenshot'))'''
            if report.longrepr:
                log = html.div(class_='log')
                for line in str(report.longrepr).splitlines():
                    separator = line.startswith('_ ' * 10)
                    if separator:
                        log.append(line[:80])
                    else:
                        exception = line.startswith("E   ")
                        if exception:
                            log.append(html.span(raw(cgi.escape(line)),
                                                 class_='error'))
                        else:
                            log.append(raw(cgi.escape(line)))
                    log.append(html.br())
                additional_html.append(log)
        output=self._write_captured_output(report)
        info=output.split(" ")
        links_html = []
        for i in range(0, len(info)):
            if("http" in info[i] and "browserstack.com" in info[i]):
                links_html.append(html.a("link", href=info[i], target='_blank'))
                links_html.append(' ')

        self.test_logs.append(html.tr([
            html.td(result, class_='col-result'),
            html.td(testclass, class_='col-class'),
            html.td(testmethod, class_='col-name'),
            html.td(round(time), class_='col-duration'),
            html.td(links_html, class_='col-links'),
            html.td(additional_html, class_='debug')], class_=result.lower() + ' results-table-row'))