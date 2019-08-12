""" report test results in HTML format
author: Irina Gvozdeva
Based on initial code from Ross Lawley and mozilla selenium report generating.
"""
import glob

import pkg_resources
import os
import time
import datetime
import cgi
import shutil
import re

import py
from _pytest.runner import TestReport

from py.xml import html
from py.xml import raw

from html import escape


def find_urls(text):
    return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)


class LogHTML(object):
    def __init__(self, logfile, prefix):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.project_root = os.getcwd()
        self.screenshot_path = os.path.join(os.path.dirname(self.logfile), 'screenshots')
        self.debug_event_path = os.path.join(os.path.dirname(self.logfile), 'debug_events')
        self.performance_path = os.path.join(os.path.dirname(self.logfile), 'performance_logs')
        self.used_screens = []
        self.used_debug_events = []
        self.prefix = prefix
        self.current_test_info = dict.fromkeys(['package', 'class', 'name'])
        self.current_test_reports = {}
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

    def process_testnames_from_report(self, test_node_path):
        names = [x.replace(".py", "") for x in test_node_path.split("::") if x != '()']
        self.current_test_info['package'] = names[0].replace("/", '.')
        self.current_test_info['class'] = names[1] if 1 < len(names) else "N/A"
        self.current_test_info['name'] = names[2] if 2 < len(names) else "N/A"
        return names

    def _write_captured_output(self, report):
        sec = dict(report.sections)
        output = ""
        for type in ('out', 'err'):
            for section in ('setup', 'call', 'teardown'):
                content = sec.get("Captured std{} {}".format(type, section))
                if content:
                    output += content
        return output

    def process_screenshot_files(self):
        if not os.path.exists(self.screenshot_path):
            os.makedirs(self.screenshot_path)

        for screenshot in self.used_screens:
            if os.path.exists(screenshot):
                shutil.copy(screenshot, self.screenshot_path)
        screenshot_folder = os.path.join(self.project_root, 'screenshots')
        if os.path.exists(screenshot_folder):
            shutil.rmtree(screenshot_folder)

    def process_debug_event_files(self):
        if not os.path.exists(self.debug_event_path):
            os.makedirs(self.debug_event_path)

        for event in self.used_debug_events:
            if os.path.exists(event):
                shutil.copy(event, self.debug_event_path)
        debug_event_folder = os.path.join(self.project_root, 'debug_events')
        if os.path.exists(debug_event_folder):
            shutil.rmtree(debug_event_folder)

    def process_performance_files(self):
        # TODO: The file processing code smells, need to refactor it to be more DRY :)
        if not os.path.exists(self.performance_path):
            os.makedirs(self.performance_path)

        performance_tmp_folder = os.path.join(self.project_root, 'performance_logs')
        perf_log_files = glob.glob(os.path.join(performance_tmp_folder, '*.log'))

        for perf_log_file in perf_log_files:
            shutil.copy(perf_log_file, self.performance_path)

        if os.path.exists(performance_tmp_folder):
            shutil.rmtree(performance_tmp_folder)

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

    def pytest_collectreport(self, report):
        """
        For processing status of pytest test collection so we can report errors from there as well
        """

        if report.failed:
            self.process_testnames_from_report(report.nodeid)
            self.append_error(report)

    def pytest_runtest_logreport(self, report):
        self.process_testnames_from_report(report.nodeid)

        # It is the first report for that test
        current_test = self.current_test_info['name']
        if current_test not in self.current_test_reports:
            self.current_test_reports[current_test] = dict.fromkeys(['setup', 'call', 'teardown'])

        current_test_reports = self.current_test_reports[current_test]

        # Save the reports for all three test phases
        current_test_reports[report.when] = report  # type: TestReport

        if report.when == 'teardown':  # finish processing the test and not flaky
            setup_report = current_test_reports['setup']  # type: TestReport
            call_report = current_test_reports['call']  # type: TestReport
            teardown_report = current_test_reports['teardown']  # type: TestReport

            if setup_report.failed:
                self.append_error(setup_report)

            elif teardown_report.failed:
                self.append_error(teardown_report)

            elif setup_report.skipped:
                self.append_skipped(setup_report)

            if call_report:     # Fix of problems with Flaky Report not having the "call" state
                if call_report.skipped:
                    self.append_skipped(call_report)

                if call_report.passed:
                    self.append_pass(call_report)

                if call_report.failed:
                    self.append_failure(call_report)

    def pytest_sessionstart(self):
        self.suite_start_time = time.time()

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep("-", "generated html file: %s" % (self.logfile))

    def pytest_sessionfinish(self, session, exitstatus):
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
                        # html.th('Output')]), id='results-table-head'),
                        html.th('Links')]), id='results-table-head'),
                    html.tbody(*self.test_logs, id='results-table-body')], id='results-table')))
        logfile.write(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">' + doc.unicode(
                indent=2))
        logfile.close()
        self.process_screenshot_files()
        self.process_debug_event_files()
        self.process_performance_files()

    def _appendrow(self, result, report):
        testclass = f"{self.prefix}/{self.current_test_info['package']}/{self.current_test_info['class']}"
        testmethod = self.current_test_info['name']

        duration = getattr(report, 'duration', 0.0)

        additional_html = []
        links_html = []

        log = html.div(class_='log')

        if report.passed:
            log.append('Your tests are passing, but you are still curious. I like it :)')

        else:

            if hasattr(report, 'wasxfail'):
                self._append_xpass_section(log, report)

            if not report.skipped:
                self._append_crash_message_section(log, report)
                self._append_screenshot(testmethod, log)

                self._append_stacktrace_section(log, report)

                links_html.append(self._link_to_debug_event(testmethod, log))

        output = self._append_captured_output(log, report)

        additional_html.append(log)

        links_html.append(self._link_to_browserstack_log(output))

        self.test_logs.append(html.tr([
            html.td(result, class_='col-result'),
            html.td(testclass, class_='col-class'),
            html.td(testmethod, class_='col-name'),
            html.td(round(duration), class_='col-duration'),
            html.td(links_html, class_='col-links'),
            html.td(additional_html, class_='debug')],
            class_=result.lower() + ' results-table-row'))

    def _link_to_browserstack_log(self, output):
        info = output.split(" ")
        link_html = []
        for i in range(0, len(info)):
            match_obj = re.search(r'(https?://www.browserstack.com/automate/builds/[\w]*/sessions/[\w]*)/', info[i])
            if match_obj:
                link_html.append(html.a("Browserstack", href=match_obj.group(1), target='_blank'))
                link_html.append(' ')
        return link_html

    def _link_to_debug_event(self, name, log):
        name = re.sub('[^A-Za-z0-9_.]+', '_', name)
        browser_name = self.prefix.split(",")[0].replace('[', '').lower()

        source = os.path.join(self.project_root, 'debug_events', browser_name + '_' + name + '.json')
        self.used_debug_events.append(source)
        return [html.a("Console log", href='debug_events/' + browser_name + '_' + name + '.json'), ' ']

    def _append_captured_output(self, log, report) -> str:
        # Use the output section from the "teardown" report - as it has all the previous sections (setup, call) as well
        test_name = self.current_test_info['name']

        if test_name == "N/A":   # Report was taken during test collection -> no names there
            return ''

        output = self._write_captured_output(self.current_test_reports[test_name]['teardown'])
        log.append(html.h3('Captured output'))
        stacktrace_p = html.p(class_='stacktrace')
        stacktrace_p.append(output)
        log.append(stacktrace_p)
        return output

    @staticmethod
    def _append_crash_message_section(log, report):
        try:
            message = report.longrepr.reprcrash.message
            log.append(html.h3('Crash Message'))
            crash_message_p = html.p(class_='crash_message')
            for line in message.splitlines():
                crash_message_p.append(line)
                crash_message_p.append(html.br())
            log.append(crash_message_p)
        except:
            return

    @staticmethod
    def _append_stacktrace_section(log, report):
        log.append(html.h3('Stacktrace'))
        stacktrace_p = html.p(class_='stacktrace')
        for line in str(report.longrepr).splitlines():
            separator = line.startswith('_ ' * 10)
            if separator:
                stacktrace_p.append(line[:80])
            else:
                exception = line.startswith("E   ")
                if exception:
                    stacktrace_p.append(html.span(raw(escape(line)),
                                                  class_='error'))
                else:
                    stacktrace_p.append(raw(escape(line)))
            stacktrace_p.append(html.br())
        log.append(stacktrace_p)

    @staticmethod
    def _append_xpass_section(log, report):
        log.append(html.h3('Expected failure'))
        xfail_p = html.p(class_='xfail')
        xfail_reason = report.wasxfail
        xfail_p.append("Reason: ")
        # Does xfail reason contain e.g. link to JIRA?
        urls = find_urls(xfail_reason)
        if len(urls) > 0:
            xfail_p.append(html.a(xfail_reason, href=urls[0], target='_blank'))
        else:
            xfail_p.append(xfail_reason)
        log.append(xfail_p)

    def _append_screenshot(self, name, log):
        name = re.sub('[^A-Za-z0-9_.]+', '_', name)

        images_saved = os.path.join(self.project_root, 'screenshots')

        if os.path.isdir(images_saved) and len(os.listdir(images_saved)) > 0:

            log.append(html.h3('Screenshots'))

            for file in os.listdir(images_saved):
                image_path = os.path.join(images_saved, file)
                if name in image_path:
                    self.used_screens.append(image_path)
                    # use relative path in img src
                    source = image_path.replace(self.project_root, '.')
                    log.append(source)
                    log.append(html.br())
                    log.append(html.img(src=source))
                    log.append(html.br())
