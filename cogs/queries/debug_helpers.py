import os


def debugging():
	try:
		return os.environ['WAFFLE_DEBUG'] == 'True'
	except KeyError as e:
		return False


def debug_print(thing_to_print):
	if debugging():
		print(thing_to_print)
