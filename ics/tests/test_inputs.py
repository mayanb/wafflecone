from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory


class TestInputs(APITestCase):

	def setUp(self):
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')
		self.creating_process_type = ProcessTypeFactory(name='creating-process-name', code='creating-pc', unit='process-unit')
		self.creating_task = TaskFactory.create(amount=912, process_type=self.creating_process_type, product_type=self.product_type)
		self.consuming_process_type = ProcessTypeFactory(name='consuming-process-name', code='consuming-pc', unit='process-unit')
		self.consuming_task = TaskFactory.create(amount=500, process_type=self.consuming_process_type, product_type=self.product_type)

	def test_create_input(self):
		url = '/ics/v8/inputs/create/'
		data = {
			'task': self.consuming_task.id,
			'creating_task': self.creating_task.id,
			'amount': 500,
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		input = Input.objects.get(id=response.data['id'])
		self.assertEqual(input.task, self.consuming_task)
		self.assertEqual(input.creating_task, self.creating_task)
		self.assertEqual(input.amount, 500)
