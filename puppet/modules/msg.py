# -*- coding: utf-8 -*-

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import datetime
import smtplib
import socket
import datetime
import re


class EmailSend(object):
    def __init__(self, templatecontent, templatehtml, smtpserver, emailfrom,
                 emailto, project, gracedays, logger):
        self.templatecontent = templatecontent
        self.templatehtml = templatehtml
        self.smtpserver = smtpserver
        self.emailfrom = emailfrom
        self.emailto = emailto
        self.logger = logger
        self.gracedays = gracedays
        self.project = project

    def _construct_email(self):
        text = None

        with open(self.templatecontent) as fp:
            text = fp.readlines()
            self.subject = text[0].strip()

        with open(self.templatehtml) as fp:
            html = fp.readlines()

        multipart_email = MIMEMultipart('alternative')
        multipart_email['From'] = self.emailfrom
        multipart_email['Cc'] = self.emailfrom
        multipart_email['To'] = self.emailto
        multipart_email['Subject'] = Header(self.subject, 'utf-8')
        # remove subject in first two lines of the template
        text.pop(0); text.pop(0)
        text = ''.join(text)
        text = text.replace('__DATETO__', str(self.project.date_to.strftime('%d.%m.%Y')))
        text = text.replace('__PROJECTNAME__', self.project.name)
        text = text.replace('__PROJECTID__', str(self.project.feedid))
        text = text.replace('__GRACEDAYS__', str(self.gracedays.days))
        html = ''.join(html)
        html = html.replace('__MESSAGE__', text)
        html = html.replace('__YEAR__', str(datetime.date.today().year))

        # remove html newlines for plain email
        text = text.replace('<br>', '')
        text = re.sub(r'<a href.*\">', '', text)
        text = re.sub(r'</a>', '', text)
        if text and html:
            mailplain = MIMEText(text, 'plain', 'utf-8')
            mailhtml = MIMEText(html, 'html', 'utf-8')

            multipart_email.attach(mailhtml)
            multipart_email.attach(mailplain)

            return multipart_email.as_string()

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
