from ics.models import *

def patchTags(request, *args, **kwargs):
	pk = kwargs['pk']
	patchType = kwargs['patchType']
	teamId = request.data.get('team', None)
	tagsData = request.data.get('tags', None)

	# create a dict of the existing tags for this process_type that will be used to mark tags for removal
	allTags = Tag.objects.filter(team_id=teamId)
	if patchType == 'process':
		allTags = allTags.filter(process_types=pk).values('name')
	elif patchType == 'product':
		allTags = allTags.filter(product_types=pk).values('name')

	tagsToRemove = {}
	for t in allTags:
		name = t['name']
		tagsToRemove[name] = True

	# Add tags to database or update existing tags
	for tagData in tagsData:
		tag, created = Tag.objects.update_or_create(team_id=teamId, name=tagData['name'])

		# If tag is in tagsData then mark it to not be removed
		if tag.name in tagsToRemove:
			tagsToRemove[tag.name] = False

		# If the tag was just created or it does not exist for this process/product type,
		# add the process/product type to its tag
		if patchType == 'process' and \
		(created or not tag.process_types.filter(pk=pk).exists()):
			tag.process_types.add(pk)

		if patchType == 'product' and \
		(created or not tag.product_types.filter(pk=pk).exists()):
			tag.product_types.add(pk)

	# remove tags
	for key in tagsToRemove:
		if tagsToRemove[key]:
			tagToRemove = Tag.objects.get(team_id=teamId, name=key)
			if patchType == 'process':
				tagToRemove.process_types.remove(pk)
			elif patchType == 'product':
				tagToRemove.product_types.remove(pk)