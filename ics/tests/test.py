from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import TaskFactory
from ics.tests.utilities import format_date
import datetime
from django.utils import timezone
import mock


class TestCreateBasics(APITestCase):

	def test_get_tasks(self):
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 1, 10), timezone.utc)
			task1 = TaskFactory(label='Jan-Task')
		with mock.patch('django.utils.timezone.now') as mock_now:
			mock_now.return_value = timezone.make_aware(datetime.datetime(2018, 2, 10), timezone.utc)
			task2 = TaskFactory(label='Feb-Task')
		print task1.created_at
		url = reverse('tasks')
		query_params = {
			'start': format_date(datetime.datetime(2018, 1, 5)),
			'end': format_date(datetime.datetime(2018, 1, 15))
		}
		response = self.client.get(url, query_params, format='json')
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['label'], 'Jan-Task')

	def test_create_process(self):
		# create a user
		user = User.objects.create_user(username='testuser_testteam', password='ABCD12345*')
		# create a team
		team = Team.objects.create(name="testteam")
		# create a userprofile
		userprofile = UserProfile.objects.create(user=user, team=team)

		url = reverse('processes')
		data = {'code': 'TPC', 'name': 'TestProcess', 'created_by': user.id, 'team_created_by': team.id,
		        'icon': "testicon", 'default_amount': 10.0}
		response = self.client.post(url, data, format='json')
		# self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(ProcessType.objects.count(), 1)
		self.assertEqual(ProcessType.objects.get().name, 'TestProcess')

	def test_create_product(self):
		# create a user
		user = User.objects.create_user(username='testuser_testteam', password='ABCD12345*')
		# create a team
		team = Team.objects.create(name="testteam")
		# create a userprofile
		userprofile = UserProfile.objects.create(user=user, team=team)

		url = reverse('products')
		data = {'code': 'TPD', 'name': 'TestProduct', 'created_by': user.id, 'team_created_by': team.id}
		response = self.client.post(url, data, format='json')
		# self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(ProductType.objects.count(), 1)
		self.assertEqual(ProductType.objects.get().name, 'TestProduct')

	def test_create_attribute(self):
		# create a user
		user = User.objects.create_user(username='testuser_testteam', password='ABCD12345*')
		# create a team
		team = Team.objects.create(name="testteam")
		# create a userprofile
		userprofile = UserProfile.objects.create(user=user, team=team)
		# create a process
		url = reverse('processes')
		data = {'code': 'TPC', 'name': 'TestProcess', 'created_by': user.id, 'team_created_by': team.id,
		        'icon': "testicon", 'default_amount': 10.0}
		response = self.client.post(url, data, format='json')
		process = ProcessType.objects.all()[0].id

		url = reverse('attributes')
		data = {'name': 'TestAttribute', 'process_type': process}
		response = self.client.post(url, data, format='json')
		# self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Attribute.objects.count(), 1)
		self.assertEqual(Attribute.objects.get().name, 'TestAttribute')


# def test_formulaattributes_dependencies_and_taskformulaattributes:
# create 4 attributes
# create 2 formula_attributes - 1 static, and 1 adding 2 of the attributes
# check there are 2 formula dependencies
# create a task
# check there is a taskformulaattribute for the static attribute with a predicted value
#

# 1) pick a producttype (e.g. 31) and processtype (e.g.  33)
# 2) post to ics/v7/formula-attributes/create/ with a comparator (e.g. :smiley:, a formula e,g. {attribute_id1}+{attribute_id2}+3.5 (such as {115}+{121} , the product_type you chose (id) e.g. 31, and the attribute (id) you are defining the formula for  (e.g. 211) - the attributes referenced in the formula as well as the attribute the formula is defined on should all be defined on the processtype you chose above
# 3) pick a task that has that same product and process (e.g.  10932)
# 3) post to ics/v7/taskAttributes/create with the attribute (id), task (id), and your value - post a value for each attribute defined in the formula (115 and 121)
# [5:22 PM]
# 4) check ics/v7/tasks/10932 and you should see the predicted_attribute_values has an object in it for that task

#       response = self.client.get('/users/4/')
# self.assertEqual(response.data, {'id': 4, 'username': 'lauren'})
