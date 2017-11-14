import csv
from ics.models import *
from django.conf import settings
import os
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
	def handle(self, *args, **options):

		Team.objects.filter(name="mdm").delete()
		User.objects.filter(username="coco_mdm").delete()
		User.objects.filter(username="arely_mdm").delete()
		UserProfile.objects.filter(team__name="mdm").delete()
		ProductType.objects.filter(team_created_by__name="mdm").delete()
		ProcessType.objects.filter(team_created_by__name="mdm").delete()
		Attribute.objects.filter(process_type__team_created_by__name="mdm").delete()
		Contact.objects.filter(account__team__name="mdm").delete()
		Account.objects.filter(team__name="mdm").delete()

		if(Team.objects.filter(name="mdm").count() == 0 ):
			team = Team.objects.create(name="mdm")
		if(User.objects.filter(username="coco_mdm").count() == 0 ):
			user = User.objects.create(username="coco_mdm", password="polymer123")
			userprofile = UserProfile.objects.create(team=team, user=user)
		if(User.objects.filter(username="arely_mdm").count() == 0 ):
			user2 = User.objects.create(username="arely_mdm", password="polymer123")
			userprofile2 = UserProfile.objects.create(team=team, user=user2, account_type='w')


		product_types = [
			{"name": "Black Mission Fig & Apricot", "code": "FA"},
			{"name": "Strawberry & Blackcurrant", "code": "SB"},
			{"name": "Peach & Lavender", "code": "PL"},
			{"name": "Blackberry & Poppy Flower", "code": "BP"},
			{"name": "Raspberry & Violet", "code": "RV"},
			{"name": "Apricot & Hibiscus", "code": "AH"},
			{"name": "Blueberry & Lemon Peel", "code": "BL"},
			{"name": "Orange & Ginger", "code": "OG"},
			{"name": "Mission Fig & Chardonnay", "code": "MFC"},
			{"name": "Strawberry & Pinot Noir", "code": "SPN"},
			{"name": "Blackberry & Cabernet", "code": "BKC"},
			{"name": "Peach & Sauvignon", "code": "PSV"},
			{"name": "Sugar", "code": "SUG"},
			{"name": "Pectin", "code": "PEC"},
			{"name": "Blackcurrant", "code": "BLK"},
			{"name": "Lavender", "code": "LAV"},
			{"name": "Poppyflower", "code": "POP"},
			{"name": "Violet", "code": "VIO"},
			{"name": "Hibiscus", "code": "HIB"},
			{"name": "Lemon Peel", "code": "LPL"},
			{"name": "Ginger", "code": "GGR"},
			{"name": "Chardonnay", "code": "CHR"},
			{"name": "Pinot Noir", "code": "PIN"},
			{"name": "Cabernet", "code": "CBN"},
			{"name": "Sauvignon", "code": "SAU"},
			]


		process_types = [
			{
				"name": "Ingredient",
				"code": "I",
				"icon": "ingredient.png",
				"description": "",
				"output_desc": "Raw Fruit",
				"default_amount": "0",
				"unit": "kg",
			},
			{
				"name": "Cook",
				"code": "C",
				"icon": "cook.png",
				"description": "",
				"output_desc": "Cooked jam",
				"default_amount": "0",
				"unit": "kg",
			},
			{
				"name": "Jar",
				"code": "J",
				"icon": "jar.png",
				"description": "",
				"output_desc": "Jarred jam",
				"default_amount": "0",
				"unit": "jars",
			},
			{
				"name": "Lid",
				"code": "T",
				"icon": "lid.png",
				"description": "",
				"output_desc": "Lidded jars",
				"default_amount": "0",
				"unit": "jars",
			},
			{
				"name": "Pasteurize",
				"code": "P",
				"icon": "pasteurize.png",
				"description": "",
				"output_desc": "Pasteurized jars",
				"default_amount": "0",
				"unit": "jars",
			},
			{
				"name": "Label",
				"code": "L",
				"icon": "label.png",
				"description": "",
				"output_desc": "Labelled jars",
				"default_amount": "0",
				"unit": "jars",
			},
			{
				"name": "Box",
				"code": "B",
				"icon": "box.png",
				"description": "",
				"output_desc": "Cases",
				"default_amount": "0",
				"unit": "cases",
			},
			]

		attributes = [
			{
				"process_type": "Ingredient",
				"name": "Lot Date",
				"rank": "0",
				"datatype": "DATE",
			},
			{
				"process_type": "Ingredient",
				"name": "Lot Number",
				"rank": "1",
				"datatype": "TEXT",
			},
			{
				"process_type": "Cook",
				"name": "Temperature",
				"rank": "0",
				"datatype": "NUMB",
			},
			{
				"process_type": "Cook",
				"name": "pH",
				"rank": "1",
				"datatype": "NUMB",
			},
			{
				"process_type": "Cook",
				"name": "Brix",
				"rank": "2",
				"datatype": "NUMB",
			},
			]


		for product in product_types:
			ProductType.objects.create(created_by=user, team_created_by=team, name=product['name'], code=product['code'])

		for process in process_types:
			ProcessType.objects.create(
					created_by=user, 
					team_created_by=team, 
					name=process['name'], 
					code=process['code'], 
					icon=process['icon'], 
					description=process['description'], 
					output_desc=process['output_desc'], 
					default_amount=process['default_amount'],
					unit=process['unit'],
					)

		for attribute in attributes:
			print( attribute )
			process = ProcessType.objects.filter(name=attribute['process_type'])[0]
			Attribute.objects.create(process_type=process, name=attribute['name'], rank=attribute['rank'], datatype=attribute['datatype'])

		with open(os.path.join(settings.PROJECT_ROOT, 'Customers.csv'), 'rb') as csvfile:
			next(csvfile)
			reader = csv.reader(csvfile, delimiter=',', quotechar='|')
			for row in reader:
				customer_name = row[0]
				street_addr = row[1]
				state = row[2]
				city = row[3]
				zip_code = row[4]
				active = row[5]
				note = row[6]
				state = row[7]
				prospect = row[8]
				location = row[9]

				address = street_addr + " " + city + " " + state + " " + zip_code
				account = Account.objects.create(name=customer_name, team=team)
				customer = Contact.objects.create(account=account, name=customer_name, shipping_addr=address, billing_addr=address)
