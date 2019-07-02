# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from email.header import Header
import datetime
import smtplib
import socket

class InfoAccOpen(object):
    def __init__(self, username, password, templatepath, smtpserver, emailfrom,
                 emailto, emailsubject, logger):
        self.username = username
        self.password = password
        self.templatepath = templatepath
        self.smtpserver = smtpserver
        self.emailfrom = emailfrom
        self.emailto = emailto
        self.emailsubject = emailsubject
        self.logger = logger

    def _construct_email(self):
        text = None
        with open(self.templatepath) as fp:
            text = fp.readlines()

        if text:
            text = ''.join(text)
            text = text.replace('__USERNAME__', self.username)
            text = text.replace('__PASSWORD__', self.password)

            m = MIMEText(text, 'plain', 'utf-8')
            m['From'] = self.emailfrom
            m['Cc'] = self.emailfrom
            m['To'] = self.emailto
            m['Subject'] = Header(self.emailsubject, 'utf-8')

            return m.as_string()

        else:
            return None

    def send(self):
        email_text = self._construct_email()
        if not email_text:
            self.logger.error('Could not construct an email')

        else:
            try:
                s = smtplib.SMTP(self.smtpserver, 25, timeout=120)
                s.ehlo()
                s.sendmail(self.emailfrom, [self.emailto, self.emailfrom], email_text)
                s.quit()

                return True

            except (socket.error, smtplib.SMTPException) as e:
                self.logger.error(repr(e))
