from ics.models import Task
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory
from ics.tests.utilities import format_date
import datetime
from django.utils import timezone
import mock


class TestTasks(APITestCase):

	def test_create_task(self):
		process_type = ProcessTypeFactory()
		product_type = ProductTypeFactory()
		url = reverse('create_task')
		data = {'label': 'T1', 'process_type': process_type.id, 'product_type': product_type.id}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		self.assertEqual(Task.objects.count(), 1)
		self.assertEqual(Task.objects.get().label, 'T1')

	def test_list_tasks(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 1, 10), timezone.utc)
			task1 = TaskFactory(label='Jan-Task')
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 2, 10), timezone.utc)
			task2 = TaskFactory(label='Feb-Task')
		url = reverse('tasks')
		query_params = {
			'start': format_date(datetime.datetime(2018, 1, 5)),
			'end': format_date(datetime.datetime(2018, 1, 15))
		}
		response = self.client.get(url, query_params, format='json')
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['label'], 'Jan-Task')
