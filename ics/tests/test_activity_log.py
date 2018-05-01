from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory, TeamFactory, ItemFactory
from decimal import Decimal
import datetime
from django.utils import timezone
import mock
from ics.tests.utilities import format_date


class TestActivityLog(APITestCase):
	def setUp(self):
		self.team = TeamFactory()
		self.url = reverse('activity_log')
		self.query_params = {
			'team': self.team.id
		}

	def test_no_team_error(self):
		response = self.client.get(self.url, {})
		self.assertEqual(response.status_code, 400)
		self.assertEqual(response.data[0], 'Request must include "team" query param')

	def test_activity_list(self):
		task1 = TaskFactory()
		task2 = TaskFactory()
		ItemFactory(creating_task=task1, amount=29.7)
		response = self.client.get(self.url, self.query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)
		row = response.data[0]
		self.assertEqual(row['runs'], 1)
		self.assertEqual(row['process_type']['id'], task1.process_type.id)
		self.assertEqual(len(row['product_types']), 1)
		self.assertEqual(row['product_types'][0]['id'], task1.product_type.id)
		self.assertEqual(row['amount'], Decimal('29.700'))

	def test_is_trashed_filter(self):
		TaskFactory()
		TaskFactory(is_trashed=True)
		query_params = {'team': self.team.id}
		response = self.client.get(self.url, query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)

	def test_team_filter(self):
		task = TaskFactory()
		other_team = TeamFactory(name='other-team')
		other_team_process_type = ProcessTypeFactory(team_created_by=other_team)
		other_team_product_type = ProductTypeFactory(team_created_by=other_team)
		other_team_task = TaskFactory(process_type=other_team_process_type, product_type=other_team_product_type)
		response = self.client.get(self.url, self.query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['process_type']['id'], task.process_type.id)

	def test_date_filter(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 1, 10), timezone.utc)
			task1 = TaskFactory()
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 2, 10), timezone.utc)
			task2 = TaskFactory()
		query_params = {
			'team': self.team.id,
			'start': format_date(datetime.datetime(2018, 1, 5)),
			'end': format_date(datetime.datetime(2018, 1, 15))
		}
		response = self.client.get(self.url, query_params)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['process_type']['id'], task1.process_type.id)

	def test_flag_filter(self):
		unflagged_task = TaskFactory()
		flagged_task = TaskFactory(is_flagged=True, process_type=unflagged_task.process_type,
		                           product_type=unflagged_task.product_type)
		ItemFactory(creating_task=unflagged_task, amount=2.3)
		ItemFactory(creating_task=flagged_task, amount=5.9)
		query_params = {'team': self.team.id, 'flagged': 'true'}
		response = self.client.get(self.url, query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		row = response.data[0]
		self.assertEqual(row['runs'], 1)
		self.assertEqual(row['amount'], Decimal('5.9'))

	def test_product_type_filter(self):
		task1 = TaskFactory()
		task2 = TaskFactory()
		task3 = TaskFactory()
		product_types = '{},{}'.format(task2.product_type.id, task3.product_type.id)
		query_params = {'team': self.team.id, 'product_types': product_types}
		response = self.client.get(self.url, query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)

	def test_process_type_filter(self):
		task1 = TaskFactory()
		task2 = TaskFactory()
		task3 = TaskFactory()
		process_types = '{},{}'.format(task2.process_type.id, task3.process_type.id)
		query_params = {'team': self.team.id, 'process_types': process_types}
		response = self.client.get(self.url, query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)

	def test_label_search(self):
		task1 = TaskFactory()
		task2 = TaskFactory(custom_display='customtaskname')
		query_params = {'team': self.team.id, 'label': 'customtaskname'}
		response = self.client.get(self.url, query_params)
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
