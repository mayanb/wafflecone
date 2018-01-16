from django.test import TestCase
from ics.models import *

class FormulaDependencyTestCase(TestCase):
	def setUp(self):

		# create a user
		user = User.objects.create_user(username='testuser', password='ABCD12345*')
		# create a team
		team = Team.objects.create(name="test_team")
		# create a userprofile
		userprofile = UserProfile.objects.create(user=user, team=team)
		# create a processtype
		processtype = ProcessType.objects.create(created_by=user, team_created_by=team, name="testprocess", code="TPC", icon="testicon", default_amount=10.0)
		# create a producttype
		producttype = ProductType.objects.create(created_by=user, team_created_by=team, name="testproduct", code="TPD")
		# create an attribute
		attribute = Attribute.objects.create(process_type=processtype, name="testattribute", datatype="NUMB")
		# create a formulaattribute
		








		Attribute.objects.create()
		FormulaAttribute.objects.create()

	def test_formula_dependencies_created(self):
