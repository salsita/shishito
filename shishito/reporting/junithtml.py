""" report test results in HTML format
author: Irina Gvozdeva
Based on initial code from Ross Lawley and mozilla selenium report generating.
"""

import pkg_resources
import os
import time
import datetime
import cgi
import shutil
import re

import py

from py.xml import html
from py.xml import raw


def mangle_testnames(names):
    names = [x.replace(".py", "") for x in names if x != '()']
    names[0] = names[0].replace("/", '.')
    #print("names %s" %names)
    return names


class LogHTML(object):
    def __init__(self, logfile, prefix):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        # TODO will not work if shishito runner is not used
        self.project_root = os.getcwd()
        self.screenshot_path = os.path.join(os.path.dirname(self.logfile), 'screenshots')
        self.debug_event_path = os.path.join(os.path.dirname(self.logfile), 'debug_events')
        self.used_screens = []
        self.used_debug_events = []
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
        output = ""
        for name in ('out', 'err'):
            content = sec.get("Captured std%s setup" % name)
            if content:
                output = output + content
        return output

    def append_screenshot(self, name, log):
        name = re.sub('[^A-Za-z0-9_. ]+', '', name)
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path)
        source = os.path.join(self.project_root, 'screenshots', name + '.png')
        self.used_screens.append(source)
        log.append(html.img(src='screenshots/' + name + '.png'))

    def append_link_to_debug_event(self, name, log):
        name = re.sub('[^A-Za-z0-9_. ]+', '', name)
        if not os.path.exists(self.debug_event_path):
            os.makedirs(self.debug_event_path)
        source = os.path.join(self.project_root, 'debug_events', name + '.json')
        self.used_debug_events.append(source)
        log.append(html.h3('DebugEvent log'))
        log.append(html.a(name + '.json', href='debug_events/' + name + '.json'))

    def process_screenshot_files(self):
        for screen in self.used_screens:
            if os.path.exists(screen):
                shutil.copy(screen, self.screenshot_path)
        screenshot_folder = os.path.join(self.project_root, 'screenshots')
        if os.path.exists(screenshot_folder):
            shutil.rmtree(screenshot_folder)

    def process_debug_event_files(self):
        for event in self.used_debug_events:
            if os.path.exists(event):
                shutil.copy(event, self.debug_event_path)
        debug_event_folder = os.path.join(self.project_root, 'debug_events')
        if os.path.exists(debug_event_folder):
            shutil.rmtree(debug_event_folder)

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
                html.div([html.p(
                    html.span('%i tests' % numtests, class_='all clickable'),
                    ' ran in %i seconds.' % suite_time_delta,
                    html.br(),
                    html.span('%i passed' % self.passed, class_='passed clickable'), ', ',
                    html.span('%i skipped' % self.skipped, class_='skipped clickable'), ', ',
                    html.span('%i failed' % self.failed, class_='failed clickable'), ', ',
                    html.span('%i errors' % self.errors, class_='error clickable'), '.',
                    html.br(), ),
                          html.span('Hide all errors', class_='clickable hide_all_errors'), ', ',
                          html.span('Show all errors', class_='clickable show_all_errors'),
                         ], id='summary-wrapper'),
                html.div(id='summary-space'),
                html.table([
                               html.thead(html.tr([
                                   html.th('Result', class_='sortable', col='result'),
                                   html.th('Class', class_='sortable', col='class'),
                                   html.th('Name', class_='sortable', col='name'),
                                   html.th('Duration', class_='sortable numeric', col='duration'),
                                   #html.th('Output')]), id='results-table-head'),
                                   html.th('Links to BrowserStack')]), id='results-table-head'),
                               html.tbody(*self.test_logs, id='results-table-body')], id='results-table')))
        logfile.write(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' + doc.unicode(
                indent=2))
        logfile.close()
        self.process_screenshot_files()
        self.process_debug_event_files()

    def _appendrow(self, result, report):
        names = mangle_testnames(report.nodeid.split("::"))
        testclass = (names[:-1])
        if self.prefix:
            testclass.insert(0, self.prefix)
        testclass = ".".join(testclass)
        testmethod = names[-1]
        time = getattr(report, 'duration', 0.0)

        additional_html = []

        if not 'Passed' in result:
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

                if not os.path.exists(self.screenshot_path):
                    os.makedirs(self.screenshot_path)
                self.append_screenshot(testmethod, log)

                self.append_link_to_debug_event(testmethod, log)

                additional_html.append(log)
        output = self._write_captured_output(report)
        info = output.split(" ")
        links_html = []
        for i in range(0, len(info)):
            match_obj = re.search(r'(https?://www.browserstack.com/automate/builds/[\w]*/sessions/[\w]*)/', info[i])
            if match_obj:
                links_html.append(html.a("link", href=match_obj.group(1), target='_blank'))
                links_html.append(' ')

        self.test_logs.append(html.tr([
                                          html.td(result, class_='col-result'),
                                          html.td(testclass, class_='col-class'),
                                          html.td(testmethod, class_='col-name'),
                                          html.td(round(time), class_='col-duration'),
                                          html.td(links_html, class_='col-links'),
                                          html.td(additional_html, class_='debug')],
                                      class_=result.lower() + ' results-table-row'))
