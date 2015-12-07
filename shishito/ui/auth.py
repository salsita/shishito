# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: User authorization selenium library
"""
import time

from selenium.webdriver.common.keys import Keys


def log_in(email_field, email, password_field, password, submit_button=None):
    """ basic login function """
    email_field.clear()
    password_field.clear()

    email_field.send_keys(email)
    password_field.send_keys(password)
    if submit_button:
        submit_button.click()
    else:
        password_field.send_keys(Keys.RETURN)
    time.sleep(1)
