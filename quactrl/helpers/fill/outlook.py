class OutlookMailFiller(Filler):

    def __init__(self, environment):
        self.outlook = win32.Dispatch('outlook.application')
        self.engine = environment.template_engine


    def create(self, data):
        mail_stream = super().create(data)
        mail_stream = mail_stream.replace('\n', '')
        mail_fields = json.loads(mail_stream, encoding='UTF-8')

        mail = self.outlook.CreateItem(0)
        mail.To = mail_fields['To']
        mail.Subject = mail_fields['subject']
        attachments = mail_fields.get('Attachments', [])
        for attachment in attachments:
            mail.Attachments.Add(Source=attachment)

        mail.HtmlBody = mail_fields['HtmlBody']

        return mail
