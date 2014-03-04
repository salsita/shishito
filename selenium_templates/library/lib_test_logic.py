# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common function library
"""


def log_in(email_field, email, password_field, password, submit_button):
    """ basic login function """
    email_field.clear()
    password_field.clear()

    email_field.send_keys(email)
    password_field.send_keys(password)
    submit_button.click()