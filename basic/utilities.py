from uuid import uuid4
from datetime import datetime, timedelta, date
import pytz


def generateQR():
	return "dande.li/basic/" + str(uuid4())

def dt(d):
	return pytz.utc.localize(datetime.combine(d, datetime.min.time()))


def last_week_range():
	base = datetime.utcnow() - timedelta(days=7)
	start_date = base - timedelta(days=base.weekday())
	end_date = start_date + timedelta(days=7)
	return dt(start_date), dt(end_date)


def last_month_range():
	end_date = date.today().replace(day=1) - timedelta(days=1)
	start_date = end_date.replace(day=1)
	return dt(start_date), dt(end_date)

