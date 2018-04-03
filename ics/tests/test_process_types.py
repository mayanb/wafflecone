from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import UserProfileFactory, ProcessTypeFactory
from django.urls import reverse


class TestProcessTypes(APITestCase):

	def setUp(self):
		self.user_profile = UserProfileFactory()

	def test_create_process_type(self):
		url = reverse('process_types')
		data = {
			'created_by': self.user_profile.user.id,
			'team_created_by': self.user_profile.team.id,
			'name': 'process-name',
			'code': 'process-code',
			'description': 'Process Description',
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
		self.assertEqual(process_type.description, 'Process Description')
		self.assertEqual(process_type.output_desc, 'Output Description')
		self.assertEqual(process_type.default_amount, 425)
		self.assertEqual(process_type.unit, 'kg')

	def test_duplicate_process_type_to_duplicate(self):
		process_type_to_duplicate = ProcessTypeFactory(name='old-name')

		url = reverse('process_duplicate')
		data = {
			'created_by': self.user_profile.user.id,
			'team_created_by': self.user_profile.team.id,
			'name': 'new-process-name',
			'code': 'new-process-code',
			'duplicateID': process_type_to_duplicate.id,
		}
		response = self.client.post(url, data)
		self.assertEqual(response.status_code, 201)
		duplicate_process = ProcessType.objects.get(id=response.data['id'])
		self.assertEqual(duplicate_process.created_by, self.user_profile.user)
		self.assertEqual(duplicate_process.team_created_by, self.user_profile.team)
		self.assertEqual(duplicate_process.name, 'new-process-name')
		self.assertEqual(duplicate_process.code, 'new-process-code')
		self.assertEqual(duplicate_process.description, process_type_to_duplicate.description)
		self.assertEqual(duplicate_process.output_desc, process_type_to_duplicate.output_desc)
		self.assertEqual(duplicate_process.default_amount, process_type_to_duplicate.default_amount)
		self.assertEqual(duplicate_process.unit,  process_type_to_duplicate.unit)

		self.assertNotEqual(duplicate_process.name, process_type_to_duplicate.name)
		self.assertNotEqual(duplicate_process.id, process_type_to_duplicate.id)
		self.assertNotEqual(duplicate_process.code, process_type_to_duplicate.code)

		# CHECK RESPONSE BODY

	def test_list_process_types(self):
		ProcessTypeFactory(
			created_by=self.user_profile.user,
			team_created_by=self.user_profile.team,
			name='process-name',
			code='process-code',
			description='Process Description',
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
		self.assertEqual(process_type['description'], 'Process Description')
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
			'created_by': process_type.created_by.id,
			'team_created_by': process_type.team_created_by.id,
			'name': 'new-name',
			'code': 'new-code',
			'description': 'new-description',
		}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		process_type = ProcessType.objects.get(id=process_type.id)
		self.assertEqual(process_type.name, 'new-name')
		self.assertEqual(process_type.code, 'new-code')
		self.assertEqual(process_type.description, 'new-description')


