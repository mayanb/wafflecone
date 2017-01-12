from django.shortcuts import render

def index(request):
  return render(request, 'dashboard/maincontent1.html')
