from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory, ItemFactory
from django.urls import reverse


class TestItems(APITestCase):

	def setUp(self):
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')
		self.process_type = ProcessTypeFactory(name='process-name', code='pc', unit='process-unit')
		self.task = TaskFactory.create(process_type=self.process_type, product_type=self.product_type)

	def test_create_item(self):
		url = reverse('create_item')
		data = {
			'creating_task': self.task.id,
			'amount': 432,
			'is_generic': True,
			'item_qr': 'qr-code43'
		}
		response = self.client.post(url, data, format='json')
		print response.data
		self.assertEqual(response.status_code, 201)
		item = Item.objects.get(id=response.data['id'])
		self.assertEqual(item.creating_task, self.task)
		self.assertEqual(item.amount, 432)
		self.assertEqual(item.is_generic, True)
