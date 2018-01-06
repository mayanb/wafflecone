from django.db.models import F

def reorder(instance, validated_data, all_instances): 
	old_rank = instance.rank
	new_rank = validated_data.get('new_rank', instance.rank)
	values = range(old_rank+1, new_rank+1)

	increment = -1
	if old_rank > new_rank:
		values = range(new_rank, old_rank)
		increment = 1
	
	to_update = all_instances.filter(rank__in=values)
	to_update.update(rank=F('rank') + increment)

	instance.rank = new_rank
	instance.save()

	return instance