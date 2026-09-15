from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
#I added ignore comments to the code below to avoid type checking errors in my IDE.
# The code is correct and works as expected.
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("AfricaRoute", {"fields": ("role", "phone_number")}),
    ) # type: ignore

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("AfricaRoute", {"fields": ("role", "phone_number")}),
    ) # type: ignore

    list_display = UserAdmin.list_display + ("role", "phone_number") # type: ignore
    list_filter = UserAdmin.list_filter + ("role",) # type: ignore