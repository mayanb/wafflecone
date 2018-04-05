from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory, ItemFactory
from django.urls import reverse


class TestInputs(APITestCase):

	def setUp(self):
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')
		self.process_type = ProcessTypeFactory(name='process-name', code='pc', unit='process-unit')
		self.task = TaskFactory.create(process_type=self.process_type, product_type=self.product_type)
		self.item = ItemFactory()

	def test_create_input(self):
		url = reverse('create_input')
		data = {
			'task': self.task.id,
			'input_item': self.item.id,
			'amount': 943
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		input = Input.objects.get(id=response.data['id'])
		self.assertEqual(input.task, self.task)
		self.assertEqual(input.input_item, self.item)
		self.assertEqual(input.amount, 943)

