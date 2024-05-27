import json
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from accounts.models import CustomUser
from .models import *

# Create your tests here.


class QueueTest(APITestCase):
    def setUp(self) -> None:
        self.user1 = CustomUser.objects.create_user(
            username='twistru',
            password='123',
        )
        self.talonpurpose1 = TalonPurposes.objects.create(
            name='Заявление', code='З', description='description')
        self.talonpurpose2 = TalonPurposes.objects.create(
            name='Оригинал', code='О', description='description')
        self.operatorlocation1 = OperatorLocation.objects.create(name='Стол 1')
        self.operatorlocation2 = OperatorLocation.objects.create(name='Стол 2')
        self.client.force_authenticate(self.user1)

    def test_get_operator_settings(self):
        url = reverse('queue:operator-settings')
        self.client.force_authenticate(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_patch_operator_settings(self):
        url = reverse('queue:operator-settings')
        response = self.client.patch(url, {
            "purposes": [self.talonpurpose1.pk, self.talonpurpose2.pk],
            "location": self.operatorlocation1.pk,
            "automatic_assignment": False},
            format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
