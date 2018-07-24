import requests


def make_request(url, headers={}, method='GET', data=None):
	res = None
	if method == 'GET':
		res = requests.get(url, headers=headers)
	elif method == 'POST':
		res = requests.post(url, headers=headers, data=data)

	if res.status_code != requests.codes.ok and res.status_code != 201:
		raise Exception("Get request failed with status %d: %s" % (res.status_code, res.text))
	else:
		print "COMPLETED REQUEST TO: " + url
		return res.json()
