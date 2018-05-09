import datetime
from django.utils import timezone
# data types of attributes

TEXT_TYPE = "TEXT"
NUMBER_TYPE = "NUMB"
TIME_TYPE = "TIME"
BOOLEAN_TYPE = "BOOL"
USER_TYPE = "USER"

ATTRIBUTE_DATA_TYPES = (
	(TEXT_TYPE, "text data"), 
	(NUMBER_TYPE, "number data"),
	(BOOLEAN_TYPE, "boolean data"),
	(TIME_TYPE, "time data"),
	(USER_TYPE, "user data")
)

DATE_FORMAT = "%Y-%m-%d-%H-%M-%S-%f"
BEGINNING_OF_TIME = timezone.make_aware(datetime.datetime(1, 1, 1), timezone.utc)
END_OF_TIME = timezone.make_aware(datetime.datetime(3000, 1, 1), timezone.utc)

