import glob
import os
import shutil
import time
import xml.etree.ElementTree as ET

from jinja2 import Environment, FileSystemLoader

from shishito.runtime.shishito_support import ShishitoSupport


class Reporter(object):
    def __init__(self, project_root=None, test_timestamp=None):
        self.project_root = project_root or ShishitoSupport().project_root
        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        self.timestamp = test_timestamp or time.strftime("%Y-%m-%d_%H-%M-%S")

        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)

    def cleanup_results(self):
        """ Cleans up test result folder """
        if os.path.exists(os.path.join(self.project_root, 'results')):
            shutil.rmtree(os.path.join(self.project_root, 'results'))
        os.makedirs(self.result_folder)
        os.symlink(self.timestamp, os.path.join(self.project_root, 'results', 'current'))

    def archive_results(self):
        """ Archives test results in zip package """
        archive_folder = os.path.join(self.project_root, 'results_archive')
        if not (os.path.exists(archive_folder)):
            os.makedirs(archive_folder)
        shutil.make_archive(os.path.join(archive_folder, self.timestamp), "zip",
                            os.path.join(self.project_root, 'results'))

    def generate_combined_report(self):
        data = os.listdir(os.path.join(self.project_root, 'results', self.timestamp))
        result_reports = [item[:-5] for item in data if item.endswith('.html')]

        if not result_reports:
            return

        env = Environment(
            loader=FileSystemLoader(os.path.join(self.current_folder, 'resources'))
        )

        template = env.get_template('CombinedReportTemplate.html')
        template_vars = {'data': result_reports}
        output = template.render(template_vars)
        formatted_output = output.encode('utf8').strip()
        final_report = open(os.path.join(self.project_root, 'results', self.timestamp, 'CombinedReport.html'), 'w')
        final_report.write(formatted_output.decode('utf8'))
        final_report.close()
        shutil.copy(
            os.path.join(self.current_folder, 'resources', 'combined_report.js'),
            os.path.join(self.project_root, 'results', self.timestamp)
        )

    def get_xunit_test_cases(self, timestamp):
        """ Parses test names and results from xUnit result file

        :return: Dictionary of test-case (name, result) for each report file """
        result_folder = os.path.join(self.project_root, 'results', timestamp)
        files = glob.glob(os.path.join(result_folder, '*.xml'))
        test_cases = []
        for result_file in files:
            case = {'name': os.path.basename(result_file), 'cases': []}
            tree = ET.parse(result_file)
            root = tree.getroot()
            for child in root[0]:
                if child.tag == 'testcase':
                    entry = {'name': child.get('name')}
                    result = 'success'
                    failure_message = ''
                    for subChild in child:
                        if failure_message != '': failure_message += '\n'
                        failure_message += subChild.text or ''
                        if subChild.tag == 'failure' and result == 'success':
                            result = 'failure'
                        elif subChild.tag == 'error' and result == 'success':
                            result = 'error'
                        elif subChild.tag == 'skipped' and result == 'success':
                            result = 'skipped'
                    entry['result'] = result
                    if result == 'success':
                        entry['failure_message'] = None
                    else:
                        entry['failure_message'] = failure_message
                    case['cases'].append(entry)
            test_cases.append(case)
        return test_cases
