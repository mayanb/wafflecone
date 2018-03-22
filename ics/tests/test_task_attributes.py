from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import AttributeFactory, TaskFactory
from django.urls import reverse


class TestTaskAttributes(APITestCase):

	def setUp(self):
		self.task = TaskFactory.create()
		self.attribute = AttributeFactory()

	def test_create_input(self):
		url = reverse('create_task_attribute')
		data = {
			'task': self.task.id,
			'attribute': self.attribute.id,
			'value': 498
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		task_attribute = TaskAttribute.objects.get(id=response.data['id'])
		self.assertEqual(task_attribute.task, self.task)
		self.assertEqual(task_attribute.attribute, self.attribute)
		#self.assertEqual(task_attribute.value, 498)
