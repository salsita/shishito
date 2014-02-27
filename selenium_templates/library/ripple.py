# /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Vojtech Burian
@summary: Common library for executing Ripple Emulator UI actions
"""


def switch_to_ripple_app(self):
    """ switches to PhoneGap HMTL app iframe (so selenium can target elements inside it) """
    app_frame = self.driver.find_elements_by_tag_name('iframe')[0]
    self.driver.switch_to_frame(app_frame)


def switch_from_ripple_app(self):
    """ switches into the default Ripple Emulator UI DOM (so selenium can target Ripple control elements) """
    self.driver.switch_to_default_content()