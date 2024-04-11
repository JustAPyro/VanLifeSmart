from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import os

def send_gas_email(name, pitstop):
        message = MIMEMultipart()
        message['To'] = 'friends'
        message['From'] = name
        message['Subject'] = f'Gas receipt from {name}'

        title = '<b> Invite! </b>'
        message_text = MIMEText(
        f'''
        Gas Receipt from {name}
        ---
        
        Total Cost: {pitstop.total_cost}
        Gallons: {pitstop.gallons_filled}
        Time: {pitstop.date}

        ''')
        message.attach(message_text)

        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo('Gmail')
        server.starttls()
        server.login(
            os.getenv('VLS_WEB_EMAIL_ADDRESS'),
            os.getenv('VLS_WEB_EMAIL_PASSWORD')
        )

        fromaddr = 'luke.m.hanna@gmail.com'
        toaddrs = 'luke.m.hanna@gmail.com'
        server.sendmail(fromaddr, [toaddrs], message.as_string())
        server.quit()

