from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import TaskFactory, ItemFactory, ProcessTypeFactory
import mock
from django.utils import timezone
from ics.tests.utilities import format_date
import datetime


class TestGraphs(APITestCase):

	def setUp(self):
		self.process_type = ProcessTypeFactory()
		self.url = reverse('production_actuals')
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 1, 10), timezone.utc)
			task1 = TaskFactory(label='Jan-Task', process_type=self.process_type)
			ItemFactory.create(creating_task=task1, amount=576)
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 1, 11), timezone.utc)
			task2 = TaskFactory(label='Jan-Task', process_type=self.process_type)
			ItemFactory.create(creating_task=task2, amount=14)
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 2, 10), timezone.utc)
			task3 = TaskFactory(label='Feb-Task', process_type=self.process_type)
			ItemFactory.create(creating_task=task3, amount=819)

	def test_production_actuals_month(self):
		query_params = {
			'bucket': 'month',
			'process_type': self.process_type.id,
			'team_created_by': self.process_type.team_created_by.id,
			'start': format_date(datetime.datetime(2018, 1, 5)),
			'end': format_date(datetime.datetime(2018, 1, 15))
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(len(response.data), 1)
		datum = response.data[0]
		self.assertEqual(datum['bucket'], '2018-01-01T00:00:00-08:00')
		self.assertEqual(datum['total_amount'], 590)
		self.assertEqual(datum['num_tasks'], 2)

	def test_production_actuals_day(self):
		query_params = {
			'bucket': 'day',
			'process_type': self.process_type.id,
			'team_created_by': self.process_type.team_created_by.id,
			'start': format_date(datetime.datetime(2018, 1, 5)),
			'end': format_date(datetime.datetime(2018, 1, 15))
		}
		response = self.client.get(self.url, query_params, format='json')
		self.assertEqual(len(response.data), 2)
		datum1 = response.data[0]
		self.assertEqual(datum1['bucket'], '2018-01-10')
		self.assertEqual(datum1['total_amount'], 576)
		self.assertEqual(datum1['num_tasks'], 1)
		datum2 = response.data[1]
		self.assertEqual(datum2['bucket'], '2018-01-11')
		self.assertEqual(datum2['total_amount'], 14)
		self.assertEqual(datum2['num_tasks'], 1)
