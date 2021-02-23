# -*- coding: utf-8 -*-

from email.mime.text import MIMEText
from email.header import Header
import datetime
import smtplib
import socket
import datetime


class EmailSend(object):
    def __init__(self, templatecontent, templatehtml, smtpserver, emailfrom,
                 emailto, gracedays, logger):
        self.templatecontent = templatecontent
        self.templatehtml = templatehtml
        self.smtpserver = smtpserver
        self.emailfrom = emailfrom
        self.emailto = emailto
        self.logger = logger
        self.gracedays = gracedays

    def _construct_email(self):
        text = None
        with open(self.templatecontent) as fp:
            text = fp.readlines()
            self.subject = text[0].strip()

        with open(self.templatehtml) as fp:
            html = fp.readlines()

        text.pop(0); text.pop(0)
        text = ''.join(text)
        text = text.replace('__DATETO__', str(datetime.date.today()))
        text = text.replace('__DATEGRACETO__', str(datetime.date.today() + self.gracedays))
        html = ''.join(html)
        html = html.replace('__MESSAGE__', text)
        html = html.replace('__YEAR__', str(datetime.date.today().year))

        if html:
            m = MIMEText(html, 'html', 'utf-8')
            m['From'] = self.emailfrom
            m['Cc'] = self.emailfrom
            m['To'] = self.emailto
            m['Subject'] = Header(self.subject, 'utf-8')

            return m.as_string()

        else:
            return None

    def send(self):
        email_text = self._construct_email()

        for part in [self.emailfrom, self.emailto, self.subject]:
            if not part:
                self.logger.error('To, From or Subject missing')
                return False

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
