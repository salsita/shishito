from library.lib_selenium import check_images_are_loaded
from library.lib_test_config import start_browser, start_test, stop_browser, gid
import time
from unittestzero import Assert
import requests


class TestLinksImages():
    """ automated website link & image checking bot (from the future) """

    def setup_class(self):
        self.driver = start_browser(self)

        # BOT CONFIGURATION
        # -----------------
        self.acceptable_url_substrings = [get_acceptable_substring(gid('base_url'))]
        self.invalid_chars = ['$']
        self.ignore_hrefs = [None, 'javascript:void(0)', 'javascript:void(0);']
        self.time_delay = 3  # important mainly because we need to wait for images to load (and cannot tell how long)

        # state variables for link testing (do not modify)
        self.links_visited = [gid('base_url')]
        self.invalid_urls = []
        self.error_links = []
        self.images_not_loaded = []

    def teardown_class(self):
        stop_browser(self)

    def setup_method(self, method):
        start_test(self)

    def test_unleash_robot(self):
        """ tests links on page """
        self.check_links()
        self.report_failures()

    def check_links(self):
        """ recursively checks links on websites; checks if images are loaded properly """
        links_objects = self.driver.find_elements_by_tag_name('a')
        valid_links_on_page = []
        # collect valid links on page for testing
        for link in links_objects:
            url = link.get_attribute('href')
            if self.is_url_valid(url):
                valid_links_on_page.append(link.get_attribute('href'))

        # start testing each link with valid url
        for link in valid_links_on_page:
            if link not in self.links_visited:
                self.links_visited.append(link)
                # test link if request does not return invalid response
                if self.is_link_response_ok(link):
                    print 'Visiting: ' + link
                    self.driver.get(link)
                    self.wait_for_page_to_load()
                    self.check_images_are_loaded()
                    # recursively crawl test links found on this page
                    self.check_links()
                    self.driver.back()

    def report_failures(self):
        """ makes assertion if there are any kind of failures reported """
        fail_message = ''
        if len(self.invalid_urls) > 0:
            fail_message += 'Invalid URLs detected: ' + str(self.invalid_urls) + '\n'
        if len(self.images_not_loaded) > 0:
            fail_message += 'Following images were not loaded: ' + str(self.images_not_loaded) + '\n'
        if len(self.error_links) > 0:
            fail_message += 'Following links returned bad status codes: ' + str(self.error_links)
        if fail_message != '':
            Assert.fail(fail_message)
        print self.links_visited

    def is_url_valid(self, url):
        """ checks wheter url is valid and whether browser should try to load it """
        url_valid = True
        # excludes urls with values not required for testing
        if url in self.ignore_hrefs:
            url_valid = False
        # excludes urls that do not contain acceptable substrings (links leading to different domains)
        if url_valid:
            for domain in self.acceptable_url_substrings:
                if domain not in url:
                    url_valid = False
        # reports urls with invalid characters
        if url_valid:
            for item in self.invalid_chars:
                if item in url:
                    if url not in self.invalid_urls:
                        self.invalid_urls.append(url)
                        url_valid = False
        # reports empty urls with invalid characters
        if url_valid:
            if url == '':
                if url not in self.invalid_urls:
                    self.invalid_urls.append(url)
                url_valid = False
        return url_valid

    def is_link_response_ok(self, url):
        """ checks if request to link does not return invalid error code """
        response = requests.get(url)
        is_ok = True
        try:
            response.raise_for_status()
        except:
            self.error_links.append(url)
            is_ok = False
        return is_ok

    def wait_for_page_to_load(self):
        """ waits for page to load properly; important mainly for checking images """
        self.driver.implicitly_wait(int(gid('default_implicit_wait')))

    def check_images_are_loaded(self):
        """ checks all images on the pages and verifies if they are properly loaded;
         if images are not loaded at first, script waits for certain amount of time and try again """
        images_not_loaded = check_images_are_loaded(self)
        if len(images_not_loaded) != 0:
            time.sleep(self.time_delay)
            images_not_loaded = check_images_are_loaded(self)
            if len(images_not_loaded) != 0:
                self.images_not_loaded.extend(images_not_loaded)


def get_acceptable_substring(url):
    """ strips url and returns acceptable substring format for comparison """

    def strip_url(url_list):
        if len(url_list) == 1:
            new_url = url_list[0]
        else:
            new_url = url_list[1]
        return new_url

    new_url = strip_url(strip_url(url.split('//')).split('@'))
    return new_url.rsplit('.', 1)[0]