from django.contrib import admin

from .models import *

admin.site.register(Task)
admin.site.register(ProcessType)
admin.site.register(ProductType)
admin.site.register(Item)
admin.site.register(Input)
admin.site.register(Attribute)
admin.site.register(User)