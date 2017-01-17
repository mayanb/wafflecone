from django.shortcuts import render
from uuid import uuid4
from django.http import HttpResponse

def index(request):
  return render(request, 'qr/index.html')


# generates UUIDs for the QR codes, the number is in the "count" parameter
def codes(request):
	uuids = []
	count = int(request.GET.get('count'))
	for i in range(count):
		uuids.append("dande.li/ics/" + str(uuid4()))
	return HttpResponse('\n'.join(uuids))