from ics.v9.serializers import *
from django.db.models import F


# serializes all fields of the task, with nested items, inputs, and attributes
class NestedTaskSerializer(serializers.ModelSerializer):
	items = BasicItemSerializer(many=True)
	inputs = BasicInputSerializer(many=True, read_only=True)
	input_unit = serializers.CharField(read_only=True)
	attribute_values = BasicTaskAttributeSerializer(read_only=True, many=True)

	product_type = ProductTypeWithUserSerializer(many=False, read_only=True)
	process_type = ProcessTypeWithUserSerializer(many=False, read_only=True)
	display = serializers.CharField(source='*')
	total_amount = serializers.CharField(read_only=True)

	task_ingredients = serializers.SerializerMethodField()
	num_flagged_ancestors = serializers.IntegerField(read_only=True)
	recipe_instructions = serializers.SerializerMethodField()

	def get_recipe_instructions(self, task):
		recipe = Recipe.objects.filter(product_type=task.product_type, process_type=task.process_type, is_trashed=False)
		if recipe.count() > 0 and task.task_ingredients.count() > 0:
			return recipe[0].instructions
		else:
			return None

	def get_task_ingredients(self, task):
		return BasicTaskIngredientSerializer(TaskIngredient.objects.filter(task=task), many=True, read_only=True).data


	def getInputUnit(self, task):
		input = task.inputs.first()
		if input is not None:
			return input.input_item.creating_task.process_type.unit
		else: 
			return ''

	def getItems(self, task):
		if self.context.get('team_inventory', None) is not None:
			return BasicItemSerializer(task.items.all().filter(inputs__isnull=True), many=True).data
		else:
			return BasicItemSerializer(task.items.all().annotate(is_used=F('inputs__task')), many=True).data

	class Meta:
		model = Task
		fields = (
			'id', 
			'total_amount', 
			'process_type',
			'product_type',
			'label', 
			'input_unit', 
			'is_open', 
			'is_flagged', 
			'flag_update_time', 
			'created_at', 
			'updated_at', 
			'label_index', 
			'custom_display', 
			'items',
			'inputs',
			'attribute_values',
			'display',
			'is_trashed',
			'task_ingredients',
			'num_flagged_ancestors',
			'recipe_instructions'
		)


# serializes the task, without nested items, inputs, or attributes
class FlatTaskSerializer(serializers.ModelSerializer):
	# product_type = ProductTypeWithUserSerializer(many=False, read_only=True)
	display = serializers.CharField(source='*')
	total_amount = serializers.CharField(read_only=True)
	product_name = serializers.CharField(source='product_type.name')
	product_id = serializers.IntegerField(source='product_type.id')
	process_name = serializers.CharField(source='process_type.name')
	process_id = serializers.IntegerField(source='process_type.id')
	process_icon = serializers.CharField(source='process_type.icon')
	num_flagged_ancestors = serializers.IntegerField(read_only=True)

	class Meta:
		model = Task
		fields = (
			'id', 
			'total_amount',
			'label',
			'is_open', 
			'is_flagged', 
			'flag_update_time', 
			'created_at', 
			'updated_at', 
			'label_index', 
			'custom_display',
			'display',
			'is_trashed',
			'product_name',
			'product_id',
			'process_name',
			'process_id',
			'process_icon',
			'num_flagged_ancestors'
		)


class CreateTaskAttributeSerializer(serializers.ModelSerializer):
	att_name = serializers.CharField(source='attribute.name', read_only=True)
	datatype = serializers.CharField(source='attribute.datatype', read_only=True)

	class Meta:
		model = TaskAttribute
		fields = ('id', 'attribute', 'task', 'value', 'att_name', 'datatype')

	def create(self, validated_data):
		print(validated_data)
		attribute = validated_data.get('attribute')
		task = validated_data.get('task')
		value = validated_data.get('value')

		# create the TaskAttribute object and set its value
		attribute_obj = attribute
		task_obj = task
		new_task_attribute = TaskAttribute.objects.create(attribute=attribute_obj, task=task_obj, value=value)
		return new_task_attribute

