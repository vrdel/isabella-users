from email.mime.text import MIMEText
import datetime
import smtplib
import socket

class InfoAccOpen(object):
    def __init__(self, username, password, templatepath,
                 smtpserver, emailfrom, emailto, logger):
        self.username = username
        self.password = password
        self.templatepath = templatepath
        self.smtpserver = smtpserver
        self.emailfrom = emailfrom
        self.emailto = emailto
        self.logger = logger

    def _construct_email(self):
        pass

    def send(self):
        try:
            s = smtplib.SMTP(self.smtpserver, 25, timeout=120)
            s.ehlo()
            s.sendmail(self.emailfrom, [self.emailto], self._construct_email())
            s.quit()

            return True

        except (socket.error, smtplib.SMTPException) as e:
            self.logger.error(repr(self.__class__.__name__).replace('\'', '') + ': ' + repr(e))

            return False
