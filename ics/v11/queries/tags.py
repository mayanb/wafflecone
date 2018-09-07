from ics.models import *

def patchTags(request, *args, **kwargs):
	pk = kwargs['pk']
	patchType = kwargs['patchType']
	teamId = request.data.get('team', None)
	tagsData = request.data.get('tags', None)

	# query for all existing tags
	existingTags = Tag.objects.filter(team_id=teamId)
	if patchType == 'process':
		existingTags = existingTags.filter(process_types=pk).values('name')
	elif patchType == 'product':
		existingTags = existingTags.filter(product_types=pk).values('name')

	# create a set of all the tags that already exist
	allTags = set()
	for t in existingTags:
		allTags.add(t['name'])

	tagsToKeep = set()
	# Add tags to database or update existing tags
	for tagData in tagsData:
		tag, created = Tag.objects.update_or_create(team_id=teamId, name=tagData['name'])

		# If tag is in allTags then mark it to be kept
		if tag.name in allTags:
			tagsToKeep.add(tag.name)
		else:
			if patchType == 'process':
				tag.process_types.add(pk)
			elif patchType == 'product':
				tag.product_types.add(pk)

	# remove tags
	tagsToRemove = allTags - tagsToKeep
	tags = Tag.objects.filter(name__in=tagsToRemove)
	if patchType == 'process':
		ProcessType.objects.get(pk=pk).tags.remove(*tags)
	elif patchType == 'product':
		ProductType.objects.get(pk=pk).tags.remove(*tags)