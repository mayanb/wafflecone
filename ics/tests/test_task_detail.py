from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, TaskFactory, AttributeFactory


class TestTaskDetail(APITestCase):

	def setUp(self):
		self.process_type = ProcessTypeFactory()
		task = TaskFactory(process_type=self.process_type)
		self.url = reverse('task_detail', args=[task.id])

	def test_task(self):
		response = self.client.get(self.url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['process_type']['attributes']), 0)

	def test_task_with_attribute(self):
		AttributeFactory(process_type=self.process_type)
		response = self.client.get(self.url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['process_type']['attributes']), 1)

	def test_task_with_deleted_attribute(self):
		AttributeFactory(process_type=self.process_type, is_trashed=True)
		response = self.client.get(self.url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['process_type']['attributes']), 0)
