# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common selenium webdriver related functions.
Helper functions that abstract often basic webdriver operations into more usable functional blocks.
"""
import inspect
import time
import os
import glob

import requests
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, \
    ElementNotVisibleException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from unittestzero import Assert
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from shishito.runtime.shishito_support import ShishitoSupport


class SeleniumTest(object):
    def __init__(self, driver):
        self.driver = driver
        self.shishito_support = ShishitoSupport()
        self.base_url = self.shishito_support.get_opt('base_url')
        self.default_implicit_wait = int(self.shishito_support.get_opt('default_implicit_wait'))
        self.timeout = int(self.shishito_support.get_opt('timeout'))

    def save_screenshot(self, name=None, project_root=None):
        """ Saves application screenshot """
        if not name:
            # Use the name of browser and caller function (e.g. 'chrome_test_google_search'
            name = self.driver.name + "_" + inspect.stack()[1][3]
        if not project_root:
            project_root = self.shishito_support.project_root
        screenshot_folder = os.path.join(project_root, 'screenshots')
        if not os.path.exists(screenshot_folder):
            os.makedirs(screenshot_folder)

        existing_images = glob.glob(os.path.join(screenshot_folder, name + '_*.png'))
        actual_pic_nr = len(existing_images) + 1
        self.driver.save_screenshot(os.path.join(screenshot_folder, '{}_{}.png'.format(name, actual_pic_nr)))

    def save_file_from_url(self, file_path, url):
        """ Saves file from url """
        if os.path.isfile(file_path):
            print('File %s already exists.' % file_path)
            return

        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(file_path, 'wb') as save_file:
            for block in response.iter_content(1024):
                if not block:
                    break
                save_file.write(block)

    # Deprecated use property directly
    def get_base_url(self):
        return self.base_url

    # Deprecated use property directly
    def get_current_url(self):
        return self.current_url

    @property
    def current_url(self):
        """ Return the url for the current page."""
        return self.driver.current_url

    def hover_on(self, element):
        """ Mouse over specific element """
        mouse_over = ActionChains(self.driver).move_to_element(element)
        mouse_over.perform()

    def go_to_page(self, url):
        """ Opens url in currently active window """
        self.driver.get(url)
        self.driver.implicitly_wait(self.default_implicit_wait)

    def click_and_wait(self, element, locator=None):
        """ clicks on a element and then waits for specific element to be present or simply waits implicitly """
        element.click()
        if locator:
            self.wait_for_element_ready(locator)
        else:
            self.driver.implicitly_wait(10)

    def check_images_are_loaded(self):
        """ checks all images on the pages and verifies if they are properly loaded """
        script = 'return arguments[0].complete && typeof arguments[0].naturalWidth' \
                 ' != "undefined" && arguments[0].naturalWidth > 0'
        images_not_loaded = []
        for image in self.driver.find_elements_by_tag_name('img'):
            loaded = self.driver.execute_script(script, image)
            if not loaded and image.get_attribute('src'):
                images_not_loaded.append('%s: %s' % (self.driver.title, image.get_attribute('src')))
        return images_not_loaded

    def is_element_present(self, locator):
        """
        True if the element at the specified locator is present in the DOM.
        Note: It returns false immediately if the element is not found.
        """
        self.driver.implicitly_wait(0)
        try:
            self.driver.find_element(*locator)
            return True
        except NoSuchElementException:
            return False
        finally:
            # set the implicit wait back
            self.driver.implicitly_wait(self.default_implicit_wait)

    def is_element_visible(self, locator):
        """
        True if the element at the specified locator is visible in the browser.
        Note: It uses an implicit wait if element is not immediately found.
        """
        try:
            return self.driver.find_element(*locator).is_displayed()
        except (NoSuchElementException, ElementNotVisibleException):
            return False

    def is_element_not_visible(self, locator):
        """
        True if the element at the specified locator is not visible.
        Note: It returns true immediately if the element is not found.
        """
        self.driver.implicitly_wait(0)
        try:
            return not self.driver.find_element(*locator).is_displayed()
        except (NoSuchElementException, ElementNotVisibleException):
            return True
        finally:
            # set the implicit wait back
            self.driver.implicitly_wait(self.default_implicit_wait)

    def wait_for_element_present(self, locator, timeout=None):
        """ Wait for the element at the specified locator
        to be present in the DOM. """
        timeout = timeout or self.timeout
        count = 0
        while not self.is_element_present(locator):
            time.sleep(1)
            count += 1
            if count == timeout:
                raise Exception('{0} has not loaded'.format(locator))

    def wait_for_element_visible(self, locator, timeout=None):
        """
        Wait for the element at the specified locator to be visible.
        """
        timeout = timeout or self.timeout
        count = 0
        while not self.is_element_visible(locator):
            time.sleep(1)
            count += 1
            if count == timeout:
                raise Exception("{0} is not visible".format(locator))

    def wait_for_element_not_visible(self, locator, timeout=None):
        """
        Wait for the element at the specified locator not to be visible anymore.
        """
        timeout = timeout or self.timeout
        count = 0
        while self.is_element_visible(locator):
            time.sleep(1)
            count += 1
            if count == timeout:
                raise Exception("{0} is still visible".format(locator))

    def wait_for_element_not_present(self, locator, timeout=None):
        """ Wait for the element at the specified locator
         not to be present in the DOM. """
        timeout = timeout or self.timeout
        self.driver.implicitly_wait(0)
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda s: len(self.find_elements(*locator)) < 1)
            return True
        except TimeoutException:
            Assert.fail(TimeoutException)
        finally:
            self.driver.implicitly_wait(self.default_implicit_wait)

    def wait_for_text_to_match(self, text, locator, max_count=20, delay=0.25):
        """ Waits for element text to match specified text, until certain deadline """
        element = self.driver.find_element(*locator)
        counter = 0
        while element.text != text:
            if counter < max_count:
                time.sleep(delay)
                counter += 1
                element = self.driver.find_element(*locator)
            else:
                Assert.fail('"' + text + '" text did not match "' + element.text
                            + '" after ' + str(counter * delay) + ' seconds')
                break

    def wait_for_attribute_value(self, attribute, attribute_text, locator, max_count=20, delay=0.25):
        """ Waits for element attribute value to match specified text, until certain deadline """
        element = self.driver.find_element(*locator)
        counter = 0
        while element.get_attribute(attribute) != attribute_text:
            if counter < max_count:
                time.sleep(delay)
                counter += 1
            else:
                Assert.fail('"' + attribute_text + '" text did not match "' + element.get_attribute(attribute)
                            + '" after ' + str(counter * delay) + ' seconds')
                break

    def wait_for_element_ready(self, locator, timeout=None):
        """ Waits until certain element is present and clickable """
        timeout = timeout or self.timeout
        WebDriverWait(self.driver, timeout).until(EC.presence_of_element_located(locator),
                                                  'Element specified by {0} was not present!'.format(locator))
        WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator),
                                                  'Element specified by {0} did not become clickable!'.format(locator))

    def find_element(self, locator):
        """ Return the element at the specified locator."""
        return self.driver.find_element(*locator)

    def find_elements(self, locator):
        """ Return a list of elements at the specified locator."""
        return self.driver.find_elements(*locator)

    def find_elements_with_text(self, text, locator):
        """ Find elements that have specified text """
        elements = self.driver.find_elements(*locator)
        selected = [item for item in elements if item.text == text]
        return selected[0] if len(selected) == 1 else selected


    def link_destination(self, locator):
        """ Return the href attribute of the element at the specified locator."""
        link = self.driver.find_element(*locator)
        return link.get_attribute('href')

    def image_source(self, locator):
        """ Return the src attribute of the element at the specified locator."""
        link = self.driver.find_element(*locator)
        return link.get_attribute('src')

    def select_dropdown_value(self, select, value):
        """ Set 'select' dropdown value """
        select = Select(select)
        option = [option for option in select.options if option.text == value][0]
        option.click()

    def upload_file(self, file_path, input_field_locator, delay=5):
        """ uploads file through the file input field
            @file_path: path to file (including the file name) relative to test project root
            @input_field_locator: locator of input element with type="file"
            @delay: seconds to wait for file to upload
        """
        file_path = os.path.join(self.shishito_support.project_root, file_path)
        self.driver.find_element(*input_field_locator).send_keys(file_path)
        time.sleep(delay)

    def download_path(self):
        """:return value of variable download_path"""
        return self.shishito_support.get_opt('download_path')

    def wait_for_file_to_be_downloaded(self, file_path: str, timeout: int = None):
        timeout = timeout or self.timeout

        while not os.path.exists(file_path):
            if timeout < 0:
                raise FileNotFoundError(f'file not found in {timeout} seconds, make sure you specified download_path')

            time.sleep(0.5)
            timeout -= 0.5

    def execute_js_script(self, script, arguments=None):
        """execute any js command with arguments or without it"""
        script_value = self.driver.execute_script(script, arguments)
        return script_value

    def open_new_tab(self, url):
        """Open new tab using keyboard, for now work only in Firefox and IE, in Chrome use js script to open tab """
        ActionChains(self.driver).send_keys(Keys.CONTROL, "t").perform()
        windows = self.driver.window_handles
        self.driver.switch_to_window(windows[-1])
        self.driver.get(url)

    def switch_new_tab(self):
        """switch to new tab/window"""
        windows = self.driver.window_handles
        self.driver.switch_to_window(windows[-1])

    def switch_first_tab(self):
        """Close current tab, switch to first tab/window"""
        windows = self.driver.window_handles
        self.driver.close()
        self.driver.switch_to_window(windows[0])


class ClickDelay:
    """
        Class to be used as a decorator that would add sleep after click() calls
        see click_delay() function for details
    """
    def __init__(self, obj):
        self.obj = obj

    def click_delay(self, delay = 2):
        self.obj.click()
        time.sleep(delay)
    
    def __getattr__(self, name):
        if (name == 'click'):
            return self.click_delay
        return getattr(self.obj, name)
    

def click_delay(function):
    """
        Function to be used as a decorator that would add sleep after click() calls.
        Usage scenario:
            this function will decorate a PageDefiniton property/method that returns a webpage Element object.
            The Element object is encapsulated by ClickDelay class (see above) which redefines click() method by adding sleep() to it.
            e.g:
                class LoginPage:

                    @property
                    @click_delay
                    def submit_button(self):
                        return self.driver.find_element_by_css_selector('form button')

                class TestLogin:
                    def test_login_err(self):
                        loginPage.submit_button.click()     # -- will click and sleep(2)
    """
    name = function.__name__
    def wrapper(*args, **kwargs):
        obj = function(*args, **kwargs)
        if (obj == None):
            raise Exception("Error: " + name + "() returned None")
        return ClickDelay(obj)
    return wrapper
 
 

