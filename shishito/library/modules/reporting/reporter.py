import os
import shutil
import time

from jinja2 import Environment, FileSystemLoader


class Reporter(object):

    def __init__(self, project_root=None):
        if project_root:
            self.project_root = project_root
        else:
            self.project_root = os.getcwd()

        self.current_folder = os.path.dirname(os.path.abspath(__file__))
        self.timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        self.result_folder = os.path.join(self.project_root, 'results', self.timestamp)

    def cleanup_results(self):
        """ Cleans up test result folder """
        if os.path.exists(os.path.join(self.project_root, 'results')):
            shutil.rmtree(os.path.join(self.project_root, 'results'))
        os.makedirs(self.result_folder)

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
        final_report.write(formatted_output)
        final_report.close()
        shutil.copy(
            os.path.join(self.current_folder, 'resources', 'combined_report.js'),
            os.path.join(self.project_root, 'results', self.timestamp)
        )
