from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory, AdjustmentFactory, ItemFactory, \
	TeamFactory, InputFactory
import datetime
import mock


class TestInventoriesList(APITestCase):

	def setUp(self):
		self.process_type = ProcessTypeFactory(name='process-name', code='process-code', unit='process-unit')
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')
		self.url = reverse('adjustment-history')
		self.query_params = {
			'team': self.process_type.team_created_by.id,
			'process_type': self.process_type.id,
			'product_type': self.product_type.id,
		}
		self.past_time = datetime.datetime(2018, 1, 10)
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
				amount=37,
			)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 3)
		history = response.data[1]
		self.assertEqual(history['type'], 'adjustment')
		self.assertEqual(history['date'], self.past_time)
		self.assertEqual(float(history['data']['amount']), 37)

	def test_items(self):
		ItemFactory(creating_task=self.task, amount=18)
		ItemFactory(creating_task=self.task, amount=9)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		item_summary = response.data[0]
		self.assertEqual(item_summary['type'], 'item_summary')
		self.assertEqual(item_summary['data']['created_count'], 2)
		self.assertEqual(item_summary['data']['created_amount'], 27)
		self.assertEqual(item_summary['data']['used_count'], 0)
		self.assertEqual(item_summary['data']['used_amount'], 0)

	def test_used_items(self):
		ItemFactory(creating_task=self.task, amount=18)
		used_item = ItemFactory(creating_task=self.task, amount=9)
		InputFactory(input_item=used_item)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		item_summary = response.data[0]
		self.assertEqual(item_summary['type'], 'item_summary')
		self.assertEqual(item_summary['data']['created_count'], 2)
		self.assertEqual(item_summary['data']['created_amount'], 27)
		self.assertEqual(item_summary['data']['used_count'], 1)
		self.assertEqual(item_summary['data']['used_amount'], 9)


	def test_adjustments_and_items(self):
		ItemFactory(creating_task=self.task, amount=11)
		AdjustmentFactory(
			process_type=self.process_type,
			product_type=self.product_type,
			amount=22,
		)
		ItemFactory(creating_task=self.task, amount=33)
		AdjustmentFactory(
			process_type=self.process_type,
			product_type=self.product_type,
			amount=44,
		)
		ItemFactory(creating_task=self.task, amount=55)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 5)
		self.assertEqual(float(response.data[0]['data']['created_amount']), 55)
		self.assertEqual(float(response.data[1]['data']['amount']), 44)
		self.assertEqual(float(response.data[2]['data']['created_amount']), 33)
		self.assertEqual(float(response.data[3]['data']['amount']), 22)
		self.assertEqual(float(response.data[4]['data']['created_amount']), 11)

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
