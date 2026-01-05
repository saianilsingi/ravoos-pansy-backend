from django.contrib import admin
from .models import User, Address

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "city", "state", "pincode", "is_default")
    list_filter = ("city", "state", "is_default")
