from __future__ import absolute_import, unicode_literals

import requests
from celery import shared_task
from django.utils import timezone

from .models import Mailing, Client, Message

MAX_FAIL_COUNT = 5
URL = 'https://probe.fbrq.cloud/v1/send'
HEADERS = {
    'accept': 'application/json',
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MDEzNDc3MzIsImlzcyI6ImZhYnJpcXVlIiwibmFtZSI6Imd1c2V2MjU2In0.pGRj_gHJgb3p0d3-ahORzUSXTEb2RQvq1h-fxrX006Q',
    'Content-Type': 'application/json',
}


@shared_task(name='send_mailing')
def send_mailing(mailing_id):
    mailing = Mailing.objects.get(pk=mailing_id)

    clients = Client.objects.all()
    if mailing.client_operator_code_filter:
        clients = clients.filter(operator_code=mailing.client_operator_code_filter)
    if mailing.client_tag_filter:
        clients = clients.filter(tag=mailing.client_tag_filter)

    # Generate a message for each client
    messages = (Message(status='PENDING', mailing=mailing, client=c) for c in clients)

    for message in messages:
        if timezone.now() > mailing.end_time:
            message.set_status_timeout()
            break

        message.save()

        data = {
            'id': message.pk,
            'phone': message.client.phone,
            'text': mailing.text,
        }

        # Try to send data MAX_FAIL_COUNT times
        # successfull post request breaks the loop
        for _ in range(MAX_FAIL_COUNT):
            try:
                result = requests.post(f'{URL}/{message.pk}', json=data, headers=HEADERS)
                result.raise_for_status()
                message.send_time = timezone.now()
                message.set_status_sent()
                break
            except:
                continue
        else:
            message.set_status_failed()

    # If we only break loop in case of timeout, so we can just set all other messages as timedout as well
    for message in messages:
        message.set_status_timeout()
