from django.urls import path, include
from rest_framework import routers

from .views import MailingViewSet, ClientViewSet

appname = 'mailing'
router = routers.SimpleRouter()
router.register(r'mailings', MailingViewSet)
router.register(r'clients', ClientViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
