from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, TaskFactory


class TestTasks(APITestCase):

	def setUp(self):
		self.process_type = ProcessTypeFactory(name='process-name', code='process-code', unit='process-unit')
		self.product_type = ProductTypeFactory(name='product-name', code='product-code')

	def test_create_task(self):
		url = '/ics/v8/tasks/create/'
		data = {
			'label': 'T1',
			'process_type': self.process_type.id,
			'product_type': self.product_type.id,
			'amount': 925
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		task = Task.objects.get(id=response.data['id'])
		self.assertEqual(task.label, 'T1')
		self.assertEqual(task.process_type.id, self.process_type.id)
		self.assertEqual(task.product_type.id, self.product_type.id)
		self.assertEqual(task.amount, 925)

	def test_task_list(self):
		TaskFactory.create(amount=912, process_type=self.process_type, product_type=self.product_type)
		TaskFactory.create(amount=913, process_type=self.process_type, product_type=self.product_type)
		url = '/ics/v8/tasks/'
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 2)
		self.assertEqual(response.data[0]['amount'], 912)

	def test_task_detail(self):
		task = TaskFactory.create(amount=414, process_type=self.process_type, product_type=self.product_type)
		url = '/ics/v8/tasks/{}/'.format(task.id)
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['amount'], 414)

	def test_task_edit(self):
		task = TaskFactory.create(amount=414, process_type=self.process_type, product_type=self.product_type)
		url = '/ics/v8/tasks/edit/{}/'.format(task.id)
		data = {
			'is_trashed': True,
			'process_type': self.process_type.id,
			'product_type': self.product_type.id,
			'amount': 536
		}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['is_trashed'], True)
		self.assertEqual(response.data['amount'], 536)

	def test_task_search(self):
		TaskFactory.create(amount=414, label='T1', process_type=self.process_type, product_type=self.product_type)
		TaskFactory.create(amount=338, label='S5', process_type=self.process_type, product_type=self.product_type)
		url = '/ics/v8/tasks/search/'
		query_params = {
			'label': 'S5'
		}
		response = self.client.get(url, query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['amount'], 338)

	def test_simple_task_search(self):
		TaskFactory.create(amount=414, label='T1', process_type=self.process_type, product_type=self.product_type)
		TaskFactory.create(amount=338, label='S5', process_type=self.process_type, product_type=self.product_type)
		url = '/ics/v8/tasks/simple/'
		query_params = {
			'label': 'S5'
		}
		response = self.client.get(url, query_params, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['results']), 1)
		self.assertEqual(response.data['results'][0]['amount'], 338)
