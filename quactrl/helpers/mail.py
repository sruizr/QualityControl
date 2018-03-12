import smtplib
from email.message import EmailMessage


class MailSender:
    def __init__(self, environment):
        self._pars = environment['controller']['mail']
        self.env = Environment()
        self.subject = self.env.from_string(self._pars['subject'])
        self.content = self.env.from_string(self._pars['content'])

    def notify_check(self, check):
        server = smtplib.SMTP(self._pars['host'], self._pars['port'])
        server.ehlo()
        server.login(self._pars['user'], self._pars['psw'])

        message = EmailMessage()
        message.set_content(self.content.render(check=check))
        message['subject'] = self.subject.render(check=check)
        message['from'] = self._pars['user']
        message['to'] = self._pars['to']

        server.sendmail(self._pars['user'], self._pars['to'],
                        message.as_string())

        server.quit()
