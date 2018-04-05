from ics.models import *
from django.urls import reverse
from rest_framework.test import APITestCase
from ics.tests.factories import ProcessTypeFactory, ProductTypeFactory, ItemFactory, TeamFactory, TaskFactory


class TestMovements(APITestCase):

	def setUp(self):
		self.sending_team = TeamFactory(name='sending-team')
		self.receiving_team = TeamFactory(name='receiving-team')
		self.process_type = ProcessTypeFactory(team_created_by=self.sending_team)
		self.product_type = ProductTypeFactory(team_created_by=self.sending_team)

	def test_create_movement(self):
		task1 = TaskFactory(process_type=self.process_type, product_type=self.product_type)
		task2 = TaskFactory(process_type=self.process_type, product_type=self.product_type)
		task3 = TaskFactory(process_type=self.process_type, product_type=self.product_type)
		old_item1 = ItemFactory(creating_task=task1)
		old_item2 = ItemFactory(creating_task=task2)
		old_item3 = ItemFactory(creating_task=task3)
		self.assertEqual(old_item1.team_inventory, self.sending_team)
		self.assertEqual(old_item2.team_inventory, self.sending_team)
		self.assertEqual(old_item3.team_inventory, self.sending_team)
		url = reverse('create_movement')
		data = {
			'origin': self.process_type.created_by.id,
			'team_origin': self.sending_team.id,
			'team_destination': self.receiving_team.id,
			'items': [
				{
					'item': old_item1.id
				},
				{
					'item': old_item2.id
				}
			]
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, 201)

		new_item1 = Item.objects.get(id=old_item1.id)
		new_item2 = Item.objects.get(id=old_item2.id)
		new_item3 = Item.objects.get(id=old_item3.id)
		self.assertEqual(new_item1.team_inventory, self.receiving_team)
		self.assertEqual(new_item2.team_inventory, self.receiving_team)
		self.assertEqual(new_item3.team_inventory, self.sending_team)
