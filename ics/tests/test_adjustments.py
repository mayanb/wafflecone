from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, UserProfileFactory
import datetime

class TestAdjustments(APITestCase):

	def test_create_adjustment(self):
		userprofile = UserProfileFactory()
		process_type = ProcessTypeFactory()
		product_type = ProductTypeFactory()
		data = {
			'userprofile': userprofile.id,
			'process_type': process_type.id,
			'product_type': product_type.id,
			'amount': 175
		}
		url = reverse('adjustments')
		self.assertEqual(Adjustment.objects.count(), 0)
		response = self.client.post(url, data, format='json')
		self.assertEqual(Adjustment.objects.count(), 1)
		adjustment = Adjustment.objects.get()
		self.assertEqual(adjustment.userprofile.id, userprofile.id)
		secondsDiff = abs((datetime.datetime.today() - adjustment.created_at.replace(tzinfo=None)).total_seconds())
		self.assertLess(secondsDiff, 10)
		self.assertEqual(adjustment.process_type.id, process_type.id)
		self.assertEqual(adjustment.product_type.id, product_type.id)
		self.assertEqual(adjustment.amount, 175)

