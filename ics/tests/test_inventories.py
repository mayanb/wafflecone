from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory, AdjustmentFactory, ItemFactory, TeamFactory, InputFactory
import datetime
import mock


class TestInventoriesList(APITestCase):

	def setUp(self):
		self.process_type = ProcessTypeFactory(name='process-name', code='process-code', unit='process-unit')
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')
		self.url = reverse('inventories')
		self.query_params = {
			'team': self.process_type.team_created_by.id
		}
		self.past_time = datetime.datetime(2018, 1, 10)
		self.task = TaskFactory(process_type=self.process_type, product_type=self.product_type)

	def test_no_items(self):
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 0)

	def test_items_only(self):
		ItemFactory(creating_task=self.task, amount=18)
		ItemFactory(creating_task=self.task, amount=3)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 1)
		item = response.data['results'][0]
		self.assertEqual(item['process_id'], str(self.process_type.id))
		self.assertEqual(item['process_name'], 'process-name')
		self.assertEqual(item['process_unit'], 'process-unit')
		self.assertEqual(item['process_code'], 'process-code')
		self.assertEqual(item['product_id'], str(self.product_type.id))
		self.assertEqual(item['product_name'], 'product-name')
		self.assertEqual(item['product_code'], 'product-code')
		self.assertEqual(item['adjusted_amount'], 21)

	def test_adjustment(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = self.past_time
			ItemFactory(creating_task=self.task, amount=18)
			ItemFactory(creating_task=self.task, amount=3)
		adjustment = AdjustmentFactory(
			process_type=self.process_type,
			product_type=self.product_type,
			amount=37,
		)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['adjusted_amount'], 37)

	def test_multiple_adjustments(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = self.past_time
			ItemFactory(creating_task=self.task, amount=18)
			ItemFactory(creating_task=self.task, amount=3)
			past_adjustment = AdjustmentFactory(
				process_type=self.process_type,
				product_type=self.product_type,
				amount=37,
			)

		presnt_adjustment = AdjustmentFactory(
			process_type=self.process_type,
			product_type=self.product_type,
			amount=932,
		)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['adjusted_amount'], 932)

	def test_items_after_adjustment(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = self.past_time
			adjustment = AdjustmentFactory(
				process_type=self.process_type,
				product_type=self.product_type,
				amount=45,
			)
		ItemFactory(creating_task=self.task, amount=3)
		ItemFactory(creating_task=self.task, amount=19)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['adjusted_amount'], 67)

	def test_no_team_error(self):
		response = self.client.get(self.url, format='json')
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data[0], 'Request must include "team" query param')

	def test_team_filter(self):
		item = ItemFactory(creating_task=self.task, amount=3)

		other_team = TeamFactory(name='other-team')
		other_team_process_type = ProcessTypeFactory(team_created_by=other_team)
		other_team_product_type = ProductTypeFactory(team_created_by=other_team)
		other_team_task = TaskFactory(process_type=other_team_process_type, product_type=other_team_product_type)
		other_team_item = ItemFactory(creating_task=other_team_task, amount=34)

		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(len(response.data['results']), 1)

	def test_exclude_used_items(self):
		item = ItemFactory(creating_task=self.task, amount=3)
		InputFactory(input_item=item)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(len(response.data['results']), 0)

	def test_exlude_items_with_deleted_tasks(self):
		deleted_task = TaskFactory(process_type=self.process_type, product_type=self.product_type, is_trashed=True)
		item = ItemFactory(creating_task=deleted_task, amount=3)
		response = self.client.get(self.url, self.query_params, format='json')
		self.assertEqual(len(response.data['results']), 0)

	def test_process_filter(self):
		ItemFactory(creating_task=self.task, amount=3)
		other_process_type = ProcessTypeFactory()
		other_task = TaskFactory(process_type=other_process_type, product_type=self.product_type)
		other_item = ItemFactory(creating_task=other_task, amount=7)
		query_params = {
			'team': self.process_type.team_created_by.id,
			'process_type': self.process_type.id
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(len(response.data['results']), 1)
		item = response.data['results'][0]
		self.assertEqual(item['process_id'], str(self.process_type.id))

	def test_product_filter(self):
		ItemFactory(creating_task=self.task, amount=3)
		other_product_type = ProductTypeFactory()
		other_task = TaskFactory(process_type=self.process_type, product_type=other_product_type)
		other_item = ItemFactory(creating_task=other_task, amount=7)
		query_params = {
			'team': self.product_type.team_created_by.id,
			'product_type': self.product_type.id
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(len(response.data['results']), 1)
