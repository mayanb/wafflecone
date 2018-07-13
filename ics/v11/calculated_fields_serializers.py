from ics.v11.serializers import *


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
		if task.recipe:
			return task.recipe.instructions
		return None

	def get_task_ingredients(self, task):
		return BasicTaskIngredientSerializer(task.task_ingredients, many=True, read_only=True).data

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
			'recipe_instructions',
			'cost'
		)


# serializes the task, without nested items, inputs, or attributes
class FlatTaskSerializer(serializers.ModelSerializer):
	items = BasicItemSerializer(many=True)
	display = serializers.CharField(source='*')
	total_amount = serializers.CharField(read_only=True)
	product_type = ProductTypeSerializer(many=False, read_only=True)
	process_type = ProcessTypeSerializer(many=False, read_only=True)
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
			'items',
			'is_trashed',
			'process_type',
			'product_type',
			'num_flagged_ancestors'
		)


class NestedItemSerializer(serializers.ModelSerializer):
	creating_task = FlatTaskSerializer(many=False, read_only=True)

	class Meta:
		model = Item
		fields = ('id', 'item_qr', 'creating_task', 'inventory', 'amount', 'is_virtual', 'team_inventory')
		read_only_fields = ('id', 'item_qr', 'creating_task', 'inventory', 'team_inventory')
