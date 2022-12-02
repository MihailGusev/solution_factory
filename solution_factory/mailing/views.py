import json

from django_celery_beat.models import PeriodicTask, ClockedSchedule
from django.db.models import Count
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from .models import Mailing, Client, Message
from .serializers import MailingSerializer, ClientSerializer
from .tasks import send_mailing


class MailingViewSet(viewsets.ModelViewSet):
    queryset = Mailing.objects.all()
    serializer_class = MailingSerializer

    def create(self, request, *args, **kwargs):
        """Create new mailing and run/schedule task"""
        serializer = MailingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mailing = serializer.save()
        response = Response(serializer.data, status=status.HTTP_201_CREATED)

        if timezone.now() > mailing.start_time:
            send_mailing.delay(mailing.pk)
            # send_mailing(mailing.pk)
            return response

        schedule = ClockedSchedule.objects.create(clocked_time=mailing.start_time)
        PeriodicTask.objects.create(
            name=mailing.pk,
            task=send_mailing.__name__,
            one_off=True,
            args=json.dumps([mailing.pk]),
            clocked_id=schedule.pk
        )
        return response

    def retrieve(self, request, *args, **kwargs):
        """Statistics for one mailing"""
        mailing = self.get_object()
        status_data = Message.objects.filter(mailing_id=mailing.pk).values('status').annotate(count=Count('status'))
        return JsonResponse({'status_data': list(status_data)})

    def list(self, request, *args, **kwargs):
        """Statistics for all mailings"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        serializer.is_valid()
        mailing_count = Mailing.objects.all().count()
        status_data = Message.objects.all().values('status').annotate(count=Count('status'))
        response_data = {'total_mailings': mailing_count,
                         'status_data': list(status_data)}
        return JsonResponse(response_data)

    def update(self, request, *args, **kwargs):
        """Change existing mailing"""
        instance = self.get_object()
        serializer = MailingSerializer(
            instance, data=request.data, update_instance=True)
        serializer.is_valid(raise_exception=True)
        mailing = serializer.save()
        response = Response(serializer.data)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        if serializer.start_changed:
            periodic_task = PeriodicTask.objects.get(name=mailing.pk)
            schedule = ClockedSchedule.objects.get(pk=periodic_task.clocked_id)
            schedule.clocked_time = mailing.start_time
            schedule.save()

        return response

    def destroy(self, request, *args, **kwargs):
        """Delete existing mailing"""
        super().destroy
        instance = self.get_object()
        periodic_task = PeriodicTask.objects.get(name=instance.pk)
        schedule = ClockedSchedule.objects.get(pk=periodic_task.clocked_id)
        periodic_task.delete()
        schedule.delete()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ClientViewSet(mixins.CreateModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    GenericViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
