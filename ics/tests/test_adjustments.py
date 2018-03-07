from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, UserFactory, AdjustmentFactory
import datetime
from ics.tests.utilities import format_date

class TestAdjustments(APITestCase):

	def test_create_adjustment(self):
		user = UserFactory()
		process_type = ProcessTypeFactory()
		product_type = ProductTypeFactory()
		adjustment_date = datetime.datetime(2018, 1, 10)
		data = {
			'created_by': user.id,
			'process_type': process_type.id,
			'product_type': product_type.id,
			'adjustment_date': adjustment_date,
			'amount': 175
		}
		url = reverse('adjustments')
		self.assertEqual(Adjustment.objects.count(), 0)
		response = self.client.post(url, data, format='json')
		self.assertEqual(Adjustment.objects.count(), 1)
		adjustment = Adjustment.objects.get()
		self.assertEqual(adjustment.created_by.id, user.id)
		secondsDiff = abs((datetime.datetime.today() - adjustment.created_at).total_seconds())
		self.assertLess(secondsDiff, 10)
		self.assertEqual(adjustment.process_type.id, process_type.id)
		self.assertEqual(adjustment.product_type.id, product_type.id)
		self.assertEqual(adjustment.adjustment_date, adjustment_date)
		self.assertEqual(adjustment.amount, 175)

	def test_edit_adjustment(self):
		adjustment_date = datetime.datetime(2018, 1, 10)
		adjustment = AdjustmentFactory(adjustment_date=adjustment_date, amount=175)
		new_adjustment_date = datetime.datetime(2018, 2, 10)
		data = {
			'adjustment_date': new_adjustment_date,
			'amount': 225
		}
		url = reverse('adjustmentDetail', kwargs={'pk': adjustment.id})
		response = self.client.patch(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(Adjustment.objects.count(), 1)
		adjustment = Adjustment.objects.get()
		self.assertEqual(adjustment.adjustment_date, new_adjustment_date)
		self.assertEqual(adjustment.amount, 225)

	def test_delete_adjustment(self):
		adjustment_date = datetime.datetime(2018, 1, 10)
		adjustment = AdjustmentFactory(adjustment_date=adjustment_date, amount=175)
		url = reverse('adjustmentDetail', kwargs={'pk': adjustment.id})
		self.assertEqual(Adjustment.objects.count(), 1)
		response = self.client.delete(url, format='json')
		self.assertEqual(response.status_code, 204)
		self.assertEqual(Adjustment.objects.count(), 0)

