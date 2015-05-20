import imaplib
import email
import time
import re

from salsa_webqa.library.control_test import ControlTest


class EmailIMAP(object):
    def __init__(self):
        self.test_control = ControlTest()
        self.email_address = self.test_control.gid('email_address')
        self.email_imap = self.test_control.gid('email_imap')
        self.email_password = self.test_control.gid('email_password')
        self.email_mailbox = self.test_control.gid('email_mailbox')

        self.mail = imaplib.IMAP4_SSL(self.email_imap)
        self.mail.login(self.email_address, self.email_password)

    def retrieve_latest_email(self, timeout=36):
        """ tries to retrieve latest email. If there are no emails,
        it waits for 5 seconds and then tries again, until total (default 36*5 = 180s) timeout is reached """
        count = 0
        while count < timeout:
            id_list = self.get_all_email_ids()
            if id_list:
                return self.get_message(id_list[-1])
            time.sleep(5)
            count += 1

    def cleanup_emails(self):
        """ cleans up email folder """
        for num in self.get_all_email_ids():
            self.mail.store(num, '+FLAGS', '\\Deleted')
        self.mail.expunge()

    def is_pattern_in_message(self, pattern, message):
        """ return Boolean if pattern is to be found in message """
        return bool(re.match(pattern, message))

    # SUPPORT METHODS

    def get_message(self, message_id):
        """ gets email message """
        data = self.mail.fetch(message_id, "(RFC822)")[1]  # fetch the email body (RFC822) for the given ID
        raw_email = data[0][1]  # here's the body, which is raw text of the whole email
        return email.message_from_string(raw_email)

    def get_all_email_ids(self):
        """ connects to gmail account and return list of all email ids """
        self.mail.select(self.email_mailbox)
        data = self.mail.search(None, "ALL")[1]
        return data[0].split() #ids split
