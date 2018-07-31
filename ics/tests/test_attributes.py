from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, AttributeFactory


class TestAttributes(APITestCase):

	def test_create_attribute(self):
		process_type = ProcessTypeFactory()
		url = reverse('attributes')
		data = {'name': 'TestAttribute', 'process_type': process_type.id}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		self.assertEqual(Attribute.objects.count(), 1)
		self.assertEqual(Attribute.objects.get().name, 'TestAttribute')

	def test_delete_attribute(self):
		old_attribute = AttributeFactory()
		self.assertEqual(old_attribute.is_trashed, False)
		url = reverse('attribute_detail', args=[old_attribute.id])
		data = {'is_trashed': True}
		response = self.client.patch(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		new_attribute = Attribute.objects.get(id=old_attribute.id)
		self.assertEqual(new_attribute.is_trashed, True)

	def test_move_attribute(self):
		process_type = ProcessTypeFactory()
		old_attribute_1 = AttributeFactory(process_type=process_type)
		old_attribute_2 = AttributeFactory(process_type=process_type)
		old_attribute_3 = AttributeFactory(process_type=process_type)
		self.assertEqual(old_attribute_1.rank, 0)
		self.assertEqual(old_attribute_2.rank, 1)
		self.assertEqual(old_attribute_3.rank, 2)
		url = reverse('attribute_move', args=[old_attribute_1.id])
		data = {'new_rank': 1}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		new_attribute_1 = Attribute.objects.get(id=old_attribute_1.id)
		new_attribute_2 = Attribute.objects.get(id=old_attribute_2.id)
		new_attribute_3 = Attribute.objects.get(id=old_attribute_3.id)
		self.assertEqual(new_attribute_1.rank, 1)
		self.assertEqual(new_attribute_2.rank, 0)
		self.assertEqual(new_attribute_3.rank, 2)
