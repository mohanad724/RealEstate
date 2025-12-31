from django.contrib import admin
from .models import Category, Property, Purchase
from django.contrib import admin
from .models import Profile

admin.site.register(Profile)

admin.site.register(Category)
admin.site.register(Property)
admin.site.register(Purchase)
