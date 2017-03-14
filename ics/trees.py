from models import *

def children(found_children, curr_level_tasks):

	new_level_tasks = set()

	# get all the items from this task 
	child_items = Item.objects.filter(creating_task__in=curr_level_tasks)

	# get all the tasks they were input into
	for input in Input.objects.filter(item__in=child_tasks).select_related():
		t = input.task
		if !found_children.contains(t):
			new_level_tasks.add(input.task)
			found_children.add(input.task)

	children(found_children, new_level_tasks)



def deleteDups():
	tasks = Task.objects.all()
	attributes = Attributes.objects.all()
	for t in tasks:
		for a in attributes:
			taskAttrs = TaskAttributes.filter(task=t, attribute=a)
			let num = len(taskAttrs)
			if num > 1:
				for i in range(1, num):
					taskAttrs[i].delete()
