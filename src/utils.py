'''
General functions that support the project
- send email
'''
import yagmail


def send_email(body):
    # send an email

    receiver = "tom.logan@canterbury.ac.nz"

    yag = yagmail.SMTP('toms.scrapers',open('pass_email.txt', 'r').read().strip('\n'))
    yag.send(
        to=receiver,
        subject="Your code notification",
        contents=body,
        # attachments=filename,
    )
