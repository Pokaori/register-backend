from celery import Celery
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

CELERY_BROKER_URL = os.environ['CELERY_BROKER_URL']
# CELERY_BROKER_URL ='amqp://Admin:1111@localhost:5672/'



tasks = Celery('email_worker', broker=CELERY_BROKER_URL)

PORT = 465   # For SSL
LOGIN = os.environ['EMAIL_LOGIN']
PASSWORD = os.environ['EMAIL_PASSWORD']
context = ssl.create_default_context()

@tasks.task()
def send_confirmation_email(user_email, password):
    print('hello')
    m = MIMEMultipart("alternative")
    m['From'] = LOGIN
    m['To'] = user_email
    m['Subject'] = "Email confirmation"
    text = f'Вітаємо на сайті Реєстратора методик проведення судових експертиз!\n' \
           f'Ваш логін: {user_email}\n' \
           f'Ваш пароль: {password}'

    part1 = MIMEText(text, "plain")

    m.attach(part1)
    with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
        server.login(LOGIN, PASSWORD)
        server.sendmail(LOGIN, user_email, m.as_string())


# @app.task(name='app.blueprints.user.email_worker.i_am_mail')
# def i_am_mail(email, msg):
#     print(f"I've recived ypour message, and now I will save it into db {email}, {msg}")

# Create a secure SSL context
# celery -A celery_worker.tasks worker




