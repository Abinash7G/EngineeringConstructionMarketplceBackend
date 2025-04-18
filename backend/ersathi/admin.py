from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import CompanyServices, Service, ServiceCategory, Subscription
from .models import Product
from .models import RentVerification, Agreement, VerificationImage, Plan
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category')
    
admin.site.register(ServiceCategory)
admin.site.register(CompanyServices)
admin.site.register(RentVerification)
admin.site.register(Agreement)
admin.site.register(VerificationImage)
admin.site.register(Subscription)
admin.site.register(Plan)
from .models import CustomUser, Company

# Avoid duplicate registration
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    pass


@admin.register(Company)
class CompanyRegistrationAdmin(admin.ModelAdmin):
    pass


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'price', 'company', 'is_available', 'created_at')  # Ensure 'company' exists in the Product model
    list_filter = ('category', 'is_available')
    search_fields = ('title', 'description', 'company__name')  # If 'company' has a name field
    


