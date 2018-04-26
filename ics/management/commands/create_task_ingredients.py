from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import Count

class Command(BaseCommand):
	help = 'Backfills every previous task to have task ingredients.'

	def handle(self, *args, **options):
		inputs = Input.objects.filter(input_item__creating_task__is_trashed=False)\
			.annotate(count =Count('input_item__inputs'))
		for input in inputs:
			ing, created = Ingredient.objects.get_or_create(
				recipe=None,
				product_type=input.input_item.creating_task.product_type,
				process_type=input.input_item.creating_task.process_type
			)

			amount = input.amount
			if amount is None:
				amount = input.input_item.amount/input.count

			task_ing_params = { 'task': input.task, 'ingredient': ing }
			task_ing, created = TaskIngredient.objects.get_or_create(**task_ing_params)
			task_ing.actual_amount = task_ing.actual_amount + amount
			task_ing.save()

