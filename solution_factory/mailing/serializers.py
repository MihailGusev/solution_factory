import re

from django.utils import timezone
from rest_framework import serializers

from .models import Mailing, Client

phone_regex = re.compile("^7\d{10}$")


class MailingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mailing
        fields = '__all__'

    def __init__(self, instance=None, data=..., **kwargs):
        self.update_instance = kwargs.pop('update_instance', False)
        super().__init__(instance, data, **kwargs)

    def validate(self, data):
        """
        Check that the start is before the stop.
        """
        if data['start_time'] > data['end_time']:
            raise serializers.ValidationError({
                "end_time": "end must occur after start"
            })
        
        if timezone.now() > data['end_time']:
            raise serializers.ValidationError({
                "end_time": "end time cannot be in the past"
            })
        
        if self.update_instance:
            if timezone.now() > self.instance.start_time:
                raise serializers.ValidationError({
                    "start_time": "unable to update mailing with start time in the past"
                })
            self.start_changed = self.instance.start_time != data['start_time']
        return data


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = '__all__'

    def validate_phone(self, value):
        if not phone_regex.search(value):
            raise serializers.ValidationError({
                "phone": "The phone must have '7XXXXXXXXXX' format"
            })
        return value