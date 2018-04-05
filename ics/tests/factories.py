import factory
import ics.models
from django.contrib.auth.models import User


class UserFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = User
		django_get_or_create = ('username',)

	class Params:
		team_name = ''

	username = factory.LazyAttribute(lambda o: 'user_' + o.team_name)


class TeamFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Team
		django_get_or_create = ('name',)

	name = 'team1'


class UserProfileFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.UserProfile
		django_get_or_create = ('user',)

	user = factory.SubFactory(UserFactory)
	team = factory.SubFactory(TeamFactory)


class ProcessTypeFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.ProcessType

	team_created_by = factory.SubFactory(TeamFactory)
	created_by = factory.SubFactory(UserFactory,
	                                team_name=factory.LazyAttribute(lambda o: o.factory_parent.team_created_by.name))


class ProductTypeFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.ProductType

	team_created_by = factory.SubFactory(TeamFactory)
	created_by = factory.SubFactory(UserFactory,
	                                team_name=factory.LazyAttribute(lambda o: o.factory_parent.team_created_by.name))


class TaskFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Task

	process_type = factory.SubFactory(ProcessTypeFactory)
	product_type = factory.SubFactory(ProductTypeFactory)


class ItemFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Item

	creating_task = factory.SubFactory(TaskFactory)
	item_qr = factory.Sequence(lambda n: 'item-qr-{0}'.format(n))


class InputFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Input

	task = factory.SubFactory(TaskFactory)


class AdjustmentFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Adjustment

	userprofile = factory.SubFactory(UserProfileFactory)
	process_type = factory.SubFactory(ProcessTypeFactory)
	product_type = factory.SubFactory(ProductTypeFactory)


class AttributeFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Attribute

	process_type = factory.SubFactory(ProcessTypeFactory)


class GoalFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Goal

	userprofile = factory.SubFactory(UserProfileFactory)
	process_type = factory.SubFactory(ProcessTypeFactory)


class GoalProductTypeFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.GoalProductType

	goal = factory.SubFactory(GoalFactory)
	product_type = factory.SubFactory(ProductTypeFactory)


class GoalWithProductTypeFactory(GoalFactory):
	associated_goal = factory.RelatedFactory(GoalProductTypeFactory, 'goal')

