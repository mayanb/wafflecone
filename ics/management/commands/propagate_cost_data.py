from django.contrib.postgres.aggregates import ArrayAgg
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from ics.models import *
from django.db.models.functions import Coalesce

"""
from django.db import connection
cursor = connection.cursor()
To update category for the process Label, Bag Intake, Package & Foil/Unfoil
update ics_processtype set category=rm where name like Label or name like %ag% or name like %oil%
To insert cost for Bag Intake tasks
update ics_task set cost=1000 where id in(select t.id from ics_task t, ics_processtype p where p.category=rm and (p.name like %Bag% or p.name like %bag%) and t.process_type_id=p.id)
To insert cost for Label tasks
update ics_task set cost='10' where id in(select t.id from ics_task t, ics_processtype p where p.category='rm' and p.name like 'Label' and t.process_type_id=p.id)
"""


class Command(BaseCommand):
    help = 'Propagates data to tasks'

    def handle(self, *args, **options):
        final_costs = self.propagate_data()
        # update data in task table
        # for task in final_costs:
        #     if final_costs[task]['cost'] is not None and final_costs[task]['remaining_worth'] is not None:
        #         Task.objects.filter(pk=task).update(cost=final_costs[task]['cost'], remaining_worth=final_costs[task]['remaining_worth'])

    # to get the list of tasks which are parent to some tasks and populate data in tasks
    def parents_list(self, tasks_with_child, tasks):
        for task in tasks_with_child:
            children = set(task.children_list)
            tasks[task.id] = {'list_children': children, 'visited': False, 'process_type': task.process_type_id, 'product_type': task.product_type_id, 'cost': task.cost, 'batch_size': task.batch_size}

    # creates list of all the taskingredients used by each task
    def get_ingredients(self, faulty_tasks, list_parents, parents):
        for child in parents:
            if child.task_parent_ids != [None]:
                list_parents[child.id] = {'parents': set(child.task_parent_ids)}
                list_parents[child.id]['task_ings'] = TaskIngredient.objects.filter(task=child.id)
                if len(list_parents[child.id]['task_ings']) == 0:
                    list_parents.pop(child.id)
                    faulty_tasks[child.id] = child.id

    def propagate_data(self):
        try:
            print "Started propagating data"
            # query to fetch tasks which are parent to atleast one task and their children
            tasks_with_child = Task.objects.filter(is_trashed=False).annotate(num_children=Count(F('items__inputs')), children_list=ArrayAgg('items__inputs__task'), batch_size=Coalesce(Sum('items__amount'), 0)).filter(num_children__gt=0)
            tasks = {}
            self.parents_list(tasks_with_child, tasks)

            ids = Task.objects.values('id')
            # query to fetch tasks along with their parent tasks
            parents = Task.objects.filter(is_trashed=False, pk__in=ids).annotate(task_parent_ids=ArrayAgg('inputs__input_item__creating_task__id'))
            faulty_tasks = {}  # stores tasks which are not available in taskingredient table
            list_parents = {}

            self.get_ingredients(faulty_tasks, list_parents, parents)
            # populate task_ing_map with taskingredients along with all the parents contributing that ingredient for each task
            for key in list_parents:
                task_ing_map = {}
                for task_ing in list_parents[key]['task_ings']:
                    task_ing_map[(task_ing.ingredient.process_type_id, task_ing.ingredient.product_type_id)] = {'amount': task_ing.actual_amount, 'parent_tasks': set()}
                for parent in list_parents[key]['parents']:
                    if parent in tasks:
                        task_ing_map[(tasks[parent]['process_type'], tasks[parent]['product_type'])]['parent_tasks'].add(parent)
                list_parents[key]['task_ing_map'] = task_ing_map

            # stores intermediate results of cost and remaining_worth for all tasks to avoid recursive db calls
            initial_costs = Task.objects.filter(is_trashed=False).all()
            final_costs = {}
            for task in initial_costs:
                final_costs[task.id] = {'id': task.id, 'cost': task.cost, 'remaining_worth': task.remaining_worth}

            # iterate through each task and update values in final_costs
            for task in tasks:
                # don't iterate if cost is None or task has been visited already
                if tasks[task]['visited'] is False and tasks[task]['cost'] is not None:
                    # unit_cost of the task is total cost associated with the task divided by batch size of the task
                    # batch_size should not be 0 (when you run script again)
                    # if tasks[task]['batch_size'] != 0:
                    unit_cost = float(round(tasks[task]['cost']/tasks[task]['batch_size'], 2))
                    # initially remaining worth of the task will be same as the total cost
                    final_costs[task]['remaining_worth'] = tasks[task]['cost']
                    # iterate through each child of the current task and propagate data
                    for child in tasks[task]['list_children']:
                        if child is not None and child not in faulty_tasks and child in final_costs:
                            new_difference = self.update_cost(task, child, unit_cost, tasks, list_parents, final_costs)
                            # call rec_cost to propagate values to children of child task if it is present in tasks list
                            if child in tasks:
                                visited = {}  # handles tasks with circular dependencies
                                self.rec_cost(child, new_difference, final_costs, tasks, faulty_tasks, list_parents, visited)

            print "Tasks successfully updated"
            return final_costs

        except Exception as e:
            print "except block"
            print(str(e))

    # updates cost and remaining worth of tasks and returns new_difference which will be passed to child task
    def update_cost(self, task, child, unit_cost, tasks, list_parents, final_costs):
        # find number of parent contributing same ingredient to the child task
        num_parents = len(list_parents[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['parent_tasks'])
        # total amount of ingredient associated with the child task
        total_amount = list_parents[child]['task_ing_map'][(tasks[task]['process_type'], tasks[task]['product_type'])]['amount']
        # actual amount to be transferred to the child
        actual_amount = float(total_amount / num_parents)
        new_difference = unit_cost * actual_amount
        # initially cost and remaining_worth can be None for tasks
        final_costs[child]['cost'] = final_costs[child]['cost'] or 0
        final_costs[child]['remaining_worth'] = final_costs[child]['remaining_worth'] or 0
        # updated total cost associated with the child
        final_costs[child]['cost'] = float(final_costs[child]['cost']) + new_difference
        # updated remaining worth of the child
        final_costs[child]['remaining_worth'] = float(final_costs[child]['remaining_worth']) + new_difference
        # updated remaining worth of parent after transferring some part to current child
        final_costs[task]['remaining_worth'] = float(final_costs[task]['remaining_worth']) - new_difference
        return new_difference

    # function to recursively propagate data
    def rec_cost(self, parent, proportional_cost, final_costs, tasks, faulty_tasks, list_parents, visited):
        # batch_size should not be 0 (when you run script again)
        # if tasks[parent]['batch_size'] != 0:
        unit_cost = float(round(proportional_cost / float(tasks[parent]['batch_size']), 2))
        for child in tasks[parent]['list_children']:
            if child is not None and child not in faulty_tasks and child in final_costs and child not in visited:
                visited[child] = child
                new_difference = self.update_cost(parent, child, unit_cost, tasks, list_parents, final_costs)
                if child in tasks:
                    tasks[child]['visited'] = True
                    self.rec_cost(child, new_difference, final_costs, tasks, faulty_tasks, list_parents, visited)
