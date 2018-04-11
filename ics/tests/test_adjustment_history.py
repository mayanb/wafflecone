from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory, AdjustmentFactory, ItemFactory, \
	TeamFactory, InputFactory
import datetime
import mock
from django.utils import timezone
from decimal import Decimal


class TestAdjustmentHistory(APITestCase):

	def setUp(self):
		self.process_type = ProcessTypeFactory(name='process-name', code='process-code', unit='process-unit')
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')
		self.url = reverse('adjustment-history')
		self.query_params = {
			'team': self.process_type.team_created_by.id,
			'process_type': self.process_type.id,
			'product_type': self.product_type.id,
		}
		self.past_time = timezone.make_aware(datetime.datetime(2018, 1, 10), timezone.utc)
		self.task = TaskFactory(process_type=self.process_type, product_type=self.product_type)

	def test_no_items(self):
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		item_summary = response.data[0]
		self.assertEqual(item_summary['type'], 'item_summary')
		self.assertEqual(item_summary['data']['created_count'], 0)
		self.assertEqual(item_summary['data']['created_amount'], 0)
		self.assertEqual(item_summary['data']['used_count'], 0)
		self.assertEqual(item_summary['data']['used_amount'], 0)

	def test_no_team_error(self):
		query_params = {
			'process_type': self.process_type.id,
			'product_type': self.product_type.id,
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data[0], 'Request must include "team" query param')

	def test_no_process_type_error(self):
		query_params = {
			'team': self.process_type.team_created_by.id,
			'product_type': self.product_type.id
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0], 'Request must include "process_type" query param')

	def test_no_product_type_error(self):
		query_params = {
			'team': self.process_type.team_created_by.id,
			'process_type': self.process_type.id,
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0], 'Request must include "product_type" query param')

	def test_adjustment(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = self.past_time
			adjustment = AdjustmentFactory(
				process_type=self.process_type,
				product_type=self.product_type,
				amount=37.3,
			)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 3)
		history = response.data[1]
		self.assertEqual(history['type'], 'adjustment')
		self.assertEqual(history['date'], self.past_time)
		self.assertEqual(history['data']['amount'], Decimal('37.300'))

	def test_items(self):
		ItemFactory(creating_task=self.task, amount=18.2)
		ItemFactory(creating_task=self.task, amount=9.4)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		item_summary = response.data[0]
		self.assertEqual(item_summary['type'], 'item_summary')
		self.assertEqual(item_summary['data']['created_count'], 2)
		self.assertEqual(item_summary['data']['created_amount'], Decimal('27.600'))
		self.assertEqual(item_summary['data']['used_count'], 0)
		self.assertEqual(item_summary['data']['used_amount'], 0)

	def test_used_items(self):
		ItemFactory(creating_task=self.task, amount=18.2)
		used_item = ItemFactory(creating_task=self.task, amount=9.4)
		InputFactory(input_item=used_item)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		item_summary = response.data[0]
		self.assertEqual(item_summary['type'], 'item_summary')
		self.assertEqual(item_summary['data']['created_count'], 2)
		self.assertEqual(item_summary['data']['created_amount'], Decimal('27.600'))
		self.assertEqual(item_summary['data']['used_count'], 1)
		self.assertEqual(item_summary['data']['used_amount'], Decimal('9.400'))


	def test_partial_inputs(self):
		partially_used_item = ItemFactory(creating_task=self.task, amount=39.3)
		InputFactory(input_item=partially_used_item, amount=7.8)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		item_summary = response.data[0]
		self.assertEqual(item_summary['type'], 'item_summary')
		self.assertEqual(item_summary['data']['created_count'], 1)
		self.assertEqual(item_summary['data']['created_amount'], Decimal('39.300'))
		self.assertEqual(item_summary['data']['used_count'], 1)
		self.assertEqual(item_summary['data']['used_amount'], Decimal('7.800'))


	def test_adjustments_and_items(self):
		ItemFactory(creating_task=self.task, amount=11.1)
		AdjustmentFactory(
			process_type=self.process_type,
			product_type=self.product_type,
			amount=22.4,
		)
		ItemFactory(creating_task=self.task, amount=33.9)
		AdjustmentFactory(
			process_type=self.process_type,
			product_type=self.product_type,
			amount=44.6,
		)
		ItemFactory(creating_task=self.task, amount=55.5)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 5)
		self.assertEqual(response.data[0]['data']['created_amount'], Decimal('55.500'))
		self.assertEqual(response.data[1]['data']['amount'], Decimal('44.600'))
		self.assertEqual(response.data[2]['data']['created_amount'], Decimal('33.900'))
		self.assertEqual(response.data[3]['data']['amount'], Decimal('22.400'))
		self.assertEqual(response.data[4]['data']['created_amount'], Decimal('11.100'))

	def test_other_items(self):
		wrong_process_task = TaskFactory(process_type=ProcessTypeFactory(), product_type=self.product_type)
		wrong_product_task = TaskFactory(process_type=self.process_type, product_type=ProductTypeFactory())
		deleted_task = TaskFactory(process_type=self.process_type, product_type=self.product_type, is_trashed=True)
		other_team = TeamFactory(name='other-team')
		ItemFactory(creating_task=wrong_process_task)
		ItemFactory(creating_task=wrong_product_task)
		ItemFactory(creating_task=deleted_task)
		other_team_item = ItemFactory(creating_task=self.task)
		other_team_item.team_inventory = other_team
		other_team_item.save()
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['data']['created_count'], 0)
