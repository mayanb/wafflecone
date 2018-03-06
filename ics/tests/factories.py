import factory
import ics.models
from django.contrib.auth.models import User


class User(factory.django.DjangoModelFactory):
	class Meta:
		model = User
		django_get_or_create = ('username',)

	class Params:
		team_name = ''

	username = factory.LazyAttribute(lambda o: 'user_' + o.team_name)


class Team(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Team
		django_get_or_create = ('name',)

	name = 'team1'


class ProcessTypeFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.ProcessType

	team_created_by = factory.SubFactory(Team)
	created_by = factory.SubFactory(User,
	                                team_name=factory.LazyAttribute(lambda o: o.factory_parent.team_created_by.name))


class ProductTypeFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.ProductType

	team_created_by = factory.SubFactory(Team)
	created_by = factory.SubFactory(User,
	                                team_name=factory.LazyAttribute(lambda o: o.factory_parent.team_created_by.name))


class TaskFactory(factory.django.DjangoModelFactory):
	class Meta:
		model = ics.models.Task

	@classmethod
	def _create(cls, target_class, *args, **kwargs):
		created_at = kwargs.pop('created_at', None)
		obj = super(TaskFactory, cls)._create(target_class, *args, **kwargs)
		if created_at is not None:
			obj.created_at = created_at
			obj.save()
		return obj

	process_type = factory.SubFactory(ProcessTypeFactory)
	product_type = factory.SubFactory(ProductTypeFactory)
