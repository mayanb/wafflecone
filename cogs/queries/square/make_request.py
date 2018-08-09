import requests
from cogs.queries.debug_helpers import debug_print


def make_request(url, headers={}, method='GET', data=None):
	if method == 'POST':
		debug_print("COMPLETED POST TO: " + url)
		return extract_data(requests.post(url, headers=headers, data=data))

	# Assumes GET responses bodies are Arrays which it will aggregate across potentially paginated responses.
	elif method == 'GET':
		data = []
		url_to_next_page_of_data = url
		while url_to_next_page_of_data:
			debug_print('Get URL: ' + url_to_next_page_of_data)
			res = requests.get(url_to_next_page_of_data, headers=headers)
			data += extract_data(res)
			url_to_next_page_of_data = res.links.get('next', {}).get('url', False)
		debug_print("FETCHED ALL (PAGINATED) DATA FROM: " + url)
		return data


def extract_data(res):
	if res.status_code != requests.codes.ok and res.status_code != 201:
		raise Exception("Get request failed with status %d: %s" % (res.status_code, res.text))
	else:
		return res.json()
