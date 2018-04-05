from ics.models import *
from rest_framework.test import APITestCase
from ics.tests.factories import UserProfileFactory, ProcessTypeFactory, ProductTypeFactory, GoalWithProductTypeFactory, GoalFactory
from django.urls import reverse


class TestGoals(APITestCase):

	def setUp(self):
		self.user_profile = UserProfileFactory()
		self.process_type = ProcessTypeFactory(created_by=self.user_profile.user)
		self.product_type1 = ProductTypeFactory(created_by=self.user_profile.user)
		self.product_type2 = ProductTypeFactory(created_by=self.user_profile.user)

	def test_create_goal(self):
		url = reverse('create_goal')
		data = {
			'userprofile': self.user_profile.id,
			'process_type': self.process_type.id,
			'input_products': "{},{}".format(self.product_type1.id, self.product_type2.id),
			'timerange': 'm',
			'goal': '65'
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)
		goal = Goal.objects.get(id=response.data['id'])
		self.assertEqual(goal.userprofile, self.user_profile)
		self.assertEqual(goal.process_type, self.process_type)
		self.assertEqual(goal.timerange, 'm')
		self.assertEqual(goal.goal, 65)
		self.assertEqual(goal.product_types.count(), 2)
		self.assertEqual(goal.product_types.first(), self.product_type1)
		self.assertEqual(goal.product_types.last(), self.product_type2)

	def test_list_goals(self):
		goal = GoalWithProductTypeFactory(
			userprofile=self.user_profile,
			process_type=self.process_type,
			timerange='m',
			goal=29
		)

		url = reverse('goals')
		response = self.client.get(url, format='json')
		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		goal = response.data[0]
		self.assertEqual(goal['userprofile'], self.user_profile.id)
		self.assertEqual(goal['all_product_types'], False)
		self.assertEqual(goal['process_type'], self.process_type.id)
		self.assertEqual(goal['goal'], '29.000')
		self.assertEqual(goal['timerange'], 'm')
		self.assertEqual(goal['rank'], 1)
		self.assertEqual(goal['is_trashed'], False)

	def test_list_goals_exclude_deleted(self):
		GoalWithProductTypeFactory(is_trashed=True)
		active_goal = GoalWithProductTypeFactory()
		url = reverse('goals')
		response = self.client.get(url, format='json')
		self.assertEqual(len(response.data), 1)
		goal = response.data[0]
		self.assertEqual(goal['id'], active_goal.id)

	def test_edit_goal(self):
		old_goal = GoalWithProductTypeFactory(goal='123')
		url = reverse('goal_edit', args=[old_goal.id])
		data = {
			'process_type': old_goal.process_type.id,
			'goal': '456'
		}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		new_goal = Goal.objects.get(id=old_goal.id)
		self.assertEqual(new_goal.goal, 456)

	def test_move_goal(self):
		process_type = ProcessTypeFactory()
		old_goal_1 = GoalFactory(process_type=process_type)
		old_goal_2 = GoalFactory(process_type=process_type)
		old_goal_3 = GoalFactory(process_type=process_type)
		self.assertEqual(old_goal_1.rank, 1)
		self.assertEqual(old_goal_2.rank, 2)
		self.assertEqual(old_goal_3.rank, 3)
		url = reverse('goal_move', args=[old_goal_1.id])
		data = {'new_rank': 2}
		response = self.client.put(url, data, format='json')
		self.assertEqual(response.status_code, 200)
		new_goal_1 = Goal.objects.get(id=old_goal_1.id)
		new_goal_2 = Goal.objects.get(id=old_goal_2.id)
		new_goal_3 = Goal.objects.get(id=old_goal_3.id)
		self.assertEqual(new_goal_1.rank, 2)
		self.assertEqual(new_goal_2.rank, 1)
		self.assertEqual(new_goal_3.rank, 3)

