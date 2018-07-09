from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import UserProfileFactory, ProcessTypeFactory, AttributeFactory
from django.urls import reverse


class TestProcessTypes(APITestCase):

	def setUp(self):
		self.user_profile = UserProfileFactory()
		self.user_profile_two = UserProfileFactory(id=-1)

	def test_create_process_type(self):
		url = reverse('process_types')
		data = {
			'created_by': self.user_profile.user.id,
			'team_created_by': self.user_profile.team.id,
			'icon': 'process-icon.png',
			'name': 'process-name',
			'code': 'process-code',
			'output_desc': 'Output Description',
			'default_amount': 425,
			'unit': 'kg',
		}
		response = self.client.post(url, data)
		self.assertEqual(response.status_code, 201)
		process_type = ProcessType.objects.get(id=response.data['id'])
		self.assertEqual(process_type.created_by, self.user_profile.user)
		self.assertEqual(process_type.team_created_by, self.user_profile.team)
		self.assertEqual(process_type.name, 'process-name')
		self.assertEqual(process_type.code, 'process-code')
		self.assertEqual(process_type.output_desc, 'Output Description')
		self.assertEqual(process_type.default_amount, 425)
		self.assertEqual(process_type.unit, 'kg')

	def test_duplicate_process_type_to_duplicate(self):
		process_type_to_duplicate = ProcessTypeFactory(
			created_by=self.user_profile_two.user,
			team_created_by=self.user_profile_two.team,
			name='old-process-name',
			code='old-process-code',
			icon='old-icon',
			output_desc='old-output_desc',
			default_amount=111,
			unit='old-unit',
			is_trashed=False,
			category='wip'
		)
		num_attributes = 4
		for i in range(num_attributes):
			AttributeFactory(name=i, process_type=process_type_to_duplicate)
		url = reverse('process_duplicate')
		data = {
			'created_by': self.user_profile.user.id,
			'team_created_by': self.user_profile.team.id,
			'name': 'new-process-name',
			'code': 'new-process-code',
			'duplicate_id': process_type_to_duplicate.id,
			'icon': 'new-icon',
			'output_desc': 'new-output_desc',
			'default_amount': 333,
			'unit': 'new-unit',
			'is_trashed': False,
			'category':'wip',
		}
		response = self.client.post(url, data)
		self.assertEqual(response.status_code, 201)
		duplicate_process = ProcessType.objects.get(id=response.data['id'])

		# Verify duplicate process contains all properties assigned to it via the POST request
		self.assertEqual(data.get('created_by'), duplicate_process.created_by.id)
		self.assertEqual(data.get('team_created_by'), duplicate_process.team_created_by.id)
		self.assertEqual(data.get('name'), duplicate_process.name)
		self.assertEqual(data.get('code'), duplicate_process.code)
		self.assertEqual(data.get('icon'), duplicate_process.icon)
		self.assertEqual(data.get('output_desc'), duplicate_process.output_desc)
		self.assertEqual(data.get('default_amount'), duplicate_process.default_amount)
		self.assertEqual(data.get('unit'), duplicate_process.unit)
		self.assertEqual(data.get('is_trashed'), duplicate_process.is_trashed)
		self.assertEqual(data.get('category'), duplicate_process.category)

		# Verify that copied attributes are the same as the process type being copied
		old_attributes = process_type_to_duplicate.attribute_set.all()
		new_attributes = duplicate_process.attribute_set.all()
		for i in range(num_attributes):
			self.assertEqual(old_attributes[i].name, new_attributes[i].name)

	def test_list_process_types(self):
		ProcessTypeFactory(
			created_by=self.user_profile.user,
			team_created_by=self.user_profile.team,
			name='process-name',
			code='process-code',
			output_desc='Output Description',
			default_amount=425,
			unit='kg',
		)

		url = reverse('process_types')
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		process_type = response.data[0]
		self.assertEqual(process_type['created_by'], self.user_profile.user.id)
		self.assertEqual(process_type['team_created_by'], self.user_profile.team.id)
		self.assertEqual(process_type['name'], 'process-name')
		self.assertEqual(process_type['code'], 'process-code')
		self.assertEqual(process_type['output_desc'], 'Output Description')
		# self.assertEqual(process_type['default_amount'], 425)
		self.assertEqual(process_type['unit'], 'kg')
		self.assertEqual(process_type['created_by_name'], self.user_profile.user.username)
		self.assertEqual(process_type['team_created_by_name'], self.user_profile.team.name)

	def test_list_process_types_exclude_deleted(self):
		active_process_type = ProcessTypeFactory()
		ProcessTypeFactory(is_trashed=True)
		url = reverse('process_types')
		response = self.client.get(url, format='json')
		self.assertEqual(len(response.data), 1)
		process_type = response.data[0]
		self.assertEqual(process_type['id'], active_process_type.id)

	def test_edit_process_type(self):
		process_type = ProcessTypeFactory(name='old-name')
		url = reverse('process_type_detail', args=[process_type.id])
		data = {
			'created_by': self.user_profile.user.id,
			'team_created_by': self.user_profile.team.id,
			'name': 'new-process-name',
			'code': 'new-process-code',
			'icon': 'new-icon',
			'output_desc': 'new-output_desc',
			'default_amount': 333,
			'unit': 'new-unit',
			'is_trashed': False,
		}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		process_type = ProcessType.objects.get(id=process_type.id)
		self.assertEqual(process_type.name, 'new-process-name')
		self.assertEqual(process_type.code, 'new-process-code')


