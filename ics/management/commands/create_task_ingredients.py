
from django.core.management.base import BaseCommand, CommandError
from ics.models import *
from django.db.models import Count
from django.db.models import Count, CharField, Value
from django.db.models.functions import Concat
from django.db.models import F, Q, Count, Case, When, Min, Value, Subquery, OuterRef, Sum, DecimalField, CharField
class Command(BaseCommand):
	help = 'Backfills every previous task to have task ingredients.'

	def handle(self, *args, **options):
		inputs = Input.objects.filter(input_item__creating_task__is_trashed=False) \
		.annotate(count =Count('input_item__inputs')) \
		.annotate(task_prod_proc=Concat(F('task__id'), Value(' '), F('input_item__creating_task__product_type'), Value(' '), F('input_item__creating_task__process_type'), output_field=CharField())) \
		.annotate(fixed_amount = Case( When(amount=None, then=F('input_item__amount')/F('count')), default=F('amount'), output_field=DecimalField()))

		inputs = inputs.values('fixed_amount', 'task_prod_proc')
		input_map = {}
		input_num = 0
		print("processing inputs")
		for inp in inputs:
			if(input_num%1000 == 0):
				print("done with " + str(input_num) + " inputs")
			if inp['task_prod_proc'] not in input_map:
				input_map[inp['task_prod_proc']] = 0
			input_map[inp['task_prod_proc']] += inp['fixed_amount']
			input_num += 1
		print("creating ingredients and task ingredients ")
		tasking_num = 0
		print(str(len(input_map)) + " task ings to create")
		for task_ing_info, amount in input_map.iteritems():
			if(tasking_num%100 == 0):
				print("done with creating " + str(tasking_num) + " task ingredients")
			task_ing = task_ing_info.split(' ')
			task_id = task_ing[0]
			product_id = task_ing[1]
			process_id = task_ing[2]
			task = Task.objects.get(pk=task_id)
			product = ProductType.objects.get(pk=product_id)
			process = ProcessType.objects.get(pk=process_id)
			ing, created = Ingredient.objects.get_or_create(
				recipe=None,
				product_type=product,
				process_type=process
			)
			TaskIngredient.objects.get_or_create(task=task, ingredient=ing, actual_amount=amount)
			tasking_num += 1


