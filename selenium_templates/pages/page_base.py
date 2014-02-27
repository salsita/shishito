# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
"""
from library.common import gid, config_loader
from selenium.common.exceptions import NoSuchElementException, \
    ElementNotVisibleException, TimeoutException
import time
from selenium.webdriver.support.wait import WebDriverWait
from unittestzero import Assert


class Page(object):
    """ Base class for all Pages """
    def __init__(self, driver):
        self.base_url = gid('base_url', config_loader())
        self.profile_name = gid('profile_name', config_loader())
        self._admin_username = gid('user_name', config_loader())
        self._admin_password = gid('password', config_loader())
        self._default_implicit_wait = gid('default_implicit_wait', config_loader())
        self._timeout = gid('timeout', config_loader())
        self.driver = driver
        
    @property    
    def admin_credentials(self):
        """ returns administrator user account credentials """
        return [self._admin_username, self._admin_password]
       
    def is_element_present(self, *locator):
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
            self.driver.implicitly_wait(self._default_implicit_wait)

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
            self.driver.implicitly_wait(self._default_implicit_wait)

    def wait_for_element_present(self, locator):
        """ Wait for the element at the specified locator 
        to be present in the DOM. """
        count = 0
        while not self.is_element_present(*locator):
            time.sleep(1)
            count += 1
            if count == self._timeout:
                raise Exception(*locator + ' has not loaded')

    def wait_for_element_visible(self, locator):
        """
        Wait for the element at the specified locator to be visible.
        """
        count = 0
        while not self.is_element_visible(*locator):
            time.sleep(1)
            count += 1
            if count == self._timeout:
                raise Exception(*locator + " is not visible")

    def wait_for_element_not_present(self, locator):
        """ Wait for the element at the specified locator
         not to be present in the DOM. """
        self.driver.implicitly_wait(0)
        try:
            WebDriverWait(self.driver, self._timeout).until(
                lambda s: len(self.find_elements(*locator)) < 1)
            return True
        except TimeoutException:
            Assert.fail(TimeoutException)
        finally:
            self.driver.implicitly_wait(self._default_implicit_wait)

    def get_url_current_page(self):
        """Return the url for the current page."""
        return(self.driver.current_url)

    def find_element(self, locator):
        """Return the element at the specified locator."""
        return self.driver.find_element(*locator)

    def find_elements(self, locator):
        """Return a list of elements at the specified locator."""
        return self.driver.find_elements(*locator)
    
    def find_elements_with_text(self, text, locator):
        elements = self.driver.find_elements(*locator)
        selected = []
        for item in elements:
            if item.text == text:
                selected.append(item)
        if len(selected) == 1:
            return selected[0]
        else:
            return selected

    def link_destination(self, locator):
        """Return the href attribute of the element at the specified locator."""
        link = self.find_element(*locator)
        return link.get_attribute('href')

    def image_source(self, locator):
        """Return the src attribute of the element at the specified locator."""
        link = self.find_element(*locator)
        return link.get_attribute('src')

    def wait_for_text_to_match(self, locator, text, max_count=20, delay=0.25):
        """ waiting for element text to match specified text, until certain deadline """
        element = self.find_element(*locator)
        counter = 0
        while element.text != text:
            if counter < max_count:
                time.sleep(delay)
                counter += 1
            else:
                Assert.fail('"' + text + '" text did not match "' + element.text
                            + '" after ' + str(counter * delay) + ' seconds')
                break

