from simplegmail import Gmail

class MailManager():
    def __init__(self, sender):
        self.sender = sender
        self.gmail = Gmail()

    def sendMail(self, msg, subject, toSend):
         self.gmail.send_message(to= toSend, msg_html=msg, sender=self.sender, subject=subject)

    def sendMailFromHTML(self, subject, msg):
        self.gmail.send_message(to="radek.szczygielski87@gmail.com", msg_html=msg, subject=subject, sender=self.sender)


if __name__ == "__main__":
    mailManager = MailManager("radek.szczygielski.trash@gmail.com")
    mailManager.sendMail(msg="Hello World", subject="Test email", toSend="radek.szczygielski87@gmail.com")