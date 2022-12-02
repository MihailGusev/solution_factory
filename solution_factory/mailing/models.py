from django.db import models

class Mailing(models.Model):
    start_time = models.DateTimeField()
    text = models.TextField()
    client_operator_code_filter = models.CharField(max_length=10, null=True)
    client_tag_filter = models.CharField(max_length=50, null=True)
    end_time = models.DateTimeField()


class Client(models.Model):
    phone = models.CharField(max_length=11)
    operator_code = models.CharField(max_length=10)
    tag = models.CharField(max_length=50, null=True)
    timezone = models.CharField(max_length=10)


class Message(models.Model):
    send_time = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, default='PENDING')
    mailing = models.ForeignKey(Mailing, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)

    def set_status_timeout(self):
        self.status = 'TIMEOUT'
        self.save()

    def set_status_sent(self):
        self.status = 'SENT'
        self.save()

    def set_status_failed(self):
        self.status = 'FAILED'
        self.save()
