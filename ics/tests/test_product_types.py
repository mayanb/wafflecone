from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import UserProfileFactory, ProductTypeFactory
from django.urls import reverse


class TestProductTypes(APITestCase):

	def setUp(self):
		self.user_profile = UserProfileFactory()

	def test_create_product_type(self):
		url = reverse('product_types')
		data = {
			'created_by': self.user_profile.user.id,
			'team_created_by': self.user_profile.team.id,
			'name': 'product-name',
			'code': 'product-code',
			'description': 'Product Description',
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		product_type = ProductType.objects.get(id=response.data['id'])
		self.assertEqual(product_type.created_by, self.user_profile.user)
		self.assertEqual(product_type.team_created_by, self.user_profile.team)
		self.assertEqual(product_type.name, 'product-name')
		self.assertEqual(product_type.code, 'product-code')
		self.assertEqual(product_type.description, 'Product Description')

	def test_list_product_types(self):
		ProductTypeFactory(
			created_by=self.user_profile.user,
			team_created_by=self.user_profile.team,
			name='product-name',
			code='product-code',
			description='Product Description',
		)

		url = reverse('product_types')
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		product_type = response.data[0]
		self.assertEqual(product_type['created_by'], self.user_profile.user.id)
		self.assertEqual(product_type['team_created_by'], self.user_profile.team.id)
		self.assertEqual(product_type['name'], 'product-name')
		self.assertEqual(product_type['code'], 'product-code')
		self.assertEqual(product_type['description'], 'Product Description')

	def test_list_product_types_exclude_deleted(self):
		active_product_type = ProductTypeFactory()
		ProductTypeFactory(is_trashed=True)
		url = reverse('product_types')
		response = self.client.get(url, format='json')
		self.assertEqual(len(response.data), 1)
		product_type = response.data[0]
		self.assertEqual(product_type['id'], active_product_type.id)

	def test_edit_product_type(self):
		product_type = ProductTypeFactory(name='old-name')
		url = reverse('product_type_detail', args=[product_type.id])
		data = {
			'created_by': product_type.created_by.id,
			'team_created_by': product_type.team_created_by.id,
			'name': 'new-name',
			'code': 'new-code',
			'description': 'new-description',
		}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		product_type = ProductType.objects.get(id=product_type.id)
		self.assertEqual(product_type.name, 'new-name')
		self.assertEqual(product_type.code, 'new-code')
		self.assertEqual(product_type.description, 'new-description')
