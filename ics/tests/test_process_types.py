from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import UserProfileFactory, ProcessTypeFactory


class TestProcessTypes(APITestCase):

	def setUp(self):
		self.user_profile = UserProfileFactory()

	def test_create_process(self):
		url = '/ics/v8/processes/'
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
		response = self.client.post(url, data, format='json')
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

	def test_list_processes(self):
		ProcessTypeFactory(
			created_by= self.user_profile.user,
			team_created_by= self.user_profile.team,
			name= 'process-name',
			code= 'process-code',
			description= 'Process Description',
			output_desc= 'Output Description',
			default_amount= 425,
			unit= 'kg',
		)

		url = '/ics/v8/processes/'
		response = self.client.get(url, format='json')
		print response.data
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		process_type = response.data[0]
		self.assertEqual(process_type['created_by'], self.user_profile.user.id)
		self.assertEqual(process_type['team_created_by'], self.user_profile.team.id)
		self.assertEqual(process_type['name'], 'process-name')
		self.assertEqual(process_type['code'], 'process-code')
		self.assertEqual(process_type['description'], 'Process Description')
		self.assertEqual(process_type['output_desc'], 'Output Description')
		self.assertEqual(process_type['default_amount'], 425)
		self.assertEqual(process_type['unit'], 'kg')
		self.assertEqual(process_type['created_by_name'], self.user_profile.user.username)
		self.assertEqual(process_type['team_created_by_name'], self.user_profile.team.name)

