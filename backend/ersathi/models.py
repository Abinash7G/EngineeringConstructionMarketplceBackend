from decimal import Decimal
from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.forms import ValidationError
from django.conf import settings

from django.core.validators import MinValueValidator, MaxValueValidator



# Define company type choices
COMPANY_TYPE_CHOICES = [
    ('construction', 'Construction Company'),
    ('supplier', 'Material Supplier'),
    # ('service', 'Service Provider'),
]


# Company Registration Model
class Company(models.Model):
    customuser = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="associated_company", null=True, blank=True)
    company_type = models.CharField(max_length=50, choices=COMPANY_TYPE_CHOICES)
    company_name = models.CharField(max_length=255)
    company_email = models.EmailField(unique=True)
    registration_certificate = models.FileField(upload_to='company_certificates/', null=True, blank=True)
    location = models.CharField(max_length=255)
    services_provided = models.JSONField(default=list, blank=True)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_inquiry_check = models.DateTimeField(null=True, blank=True)  # New field to track last inquiry check
    # Stripe Connect fields
    stripe_account_id = models.CharField(max_length=255, null=True, blank=True)  # Store Stripe Connect account ID
    stripe_account_status = models.CharField(
        max_length=20,
        choices=[("pending", "Pending"), ("verified", "Verified"), ("restricted", "Restricted")],
        default="pending"
    )
    def average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(rating.rating for rating in ratings) / ratings.count(), 1)
        return 0.0
    def __str__(self):
        return self.company_name


# Service Model
from django.db import models
from django.conf import settings

class ServiceCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

class Service(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ServiceCategory, on_delete=models.CASCADE, related_name="services")

    def __str__(self):
        return f"{self.name} ({self.category.name})"

class CompanyServices(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="company_services")  # Link to ersathi_company
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name="company_services")  # Link to ersathi_service
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Price in Nepali Rupees
    status = models.CharField(max_length=20, default="Available", choices=[("Available", "Available"), ("Unavailable", "Unavailable")])  # Availability status
    created_at = models.DateTimeField(auto_now_add=True)  # Timestamp for creation
    updated_at = models.DateTimeField(auto_now=True)  # Timestamp for updates

    def __str__(self):
        return f"{self.company.company_name}'s {self.service.name} - Rs.{self.price} ({self.status})"

    class Meta:
        unique_together = ('company', 'service') # Ensure a company can't add the same service twice

    
# Define CustomUser Model
class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    is_verified = models.BooleanField(default=False)  # Field to track email verification
    company = models.ForeignKey(Company, on_delete=models.CASCADE, blank = True, null= True, related_name="company_users") #if company delet, the user will delete
    stripe_customer_id = models.CharField(max_length=255, null=True, blank=True)  # Store Stripe Customer ID  NEW
    address = models.TextField(blank=True, null=True)  # Add address field
    class Meta:
        verbose_name = "Custom User"
        verbose_name_plural = "Custom Users"

    def __str__(self):
        return self.username
#rating
class CompanyRating(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('company', 'user')  # Ensures a user can only rate a company once

    def __str__(self):
        return f"{self.user} rated {self.company} - {self.rating}"  

#product model
from django.db import models
class Product(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=[('selling', 'Selling'), ('renting', 'Renting')])
    per_day_rent = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Field for per day rent
    image = models.ImageField(upload_to='product_images/', null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Discount percentage
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    is_available = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=0)  # New field for stock quantity
    threshold =models.PositiveIntegerField(default=2)
    rating = models.FloatField(default=0.0)  # New field for average rating
    num_reviews = models.PositiveIntegerField(default=0)  # New field for number of reviews
    created_at = models.DateTimeField(auto_now_add=True)
    


    def save(self, *args, **kwargs):
        """Automatically set the location from the associated company."""
        if self.company:
            self.location = self.company.location
        super().save(*args, **kwargs)

    def final_rent_price(self):
        """Calculate the final rent price after applying discount."""
        if self.per_day_rent and self.discount_percentage:
            discount_amount = (self.per_day_rent * self.discount_percentage) / 100
            return self.per_day_rent - discount_amount
        return self.per_day_rent

    def __str__(self):
        return self.title


# models.py
class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.FloatField()  # Rating value (e.g., 1 to 5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')  # Ensure a user can rate a product only once

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update product's average rating and num_reviews
        product = self.product
        ratings = product.ratings.all()
        product.num_reviews = ratings.count()
        product.rating = sum(r.rating for r in ratings) / product.num_reviews if product.num_reviews > 0 else 0.0
        product.save()

#####################
##COMPANY_INFO####
#####################

from django.db import models
from django.conf import settings

class CompanyInfo(models.Model):
    customuser = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use settings.AUTH_USER_MODEL instead of User
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='company_infos'
    )

    company = models.ForeignKey(
        Company,  # Make sure Company model is imported
        on_delete=models.CASCADE, 
        related_name='company_info'
    )
    
    # Rest of your existing fields remain the same
    company_name = models.CharField(max_length=255) 
    company_email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    about_us = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_name

class ProjectInfo(models.Model):
    company = models.ForeignKey(
        CompanyInfo,
        on_delete=models.CASCADE,
        related_name='projects'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=200)
    year = models.CharField(max_length=20, default="")
    image = models.ImageField(upload_to='project_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class TeamMemberInfo(models.Model):
    company = models.ForeignKey(CompanyInfo, on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to='team_avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



    

#
#
#cart and Wishlist
#
#
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Ensure a product is added only once per user

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Ensure a product is added only once per user

########
##RentVerification Model
#########

from django.db import models

class RentVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ]
    
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.status}"

class VerificationImage(models.Model):
    verification = models.ForeignKey(RentVerification, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='rent_verifications/')
    uploaded_at = models.DateTimeField(auto_now_add=True)



# models.py
from django.db import models
from django.conf import settings
class Inquiry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='inquiries')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='inquiries', db_column='company_id')
    full_name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    category = models.CharField(max_length=100)
    sub_service = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[
            ('Pending', 'Pending'),
            ('Scheduled', 'Scheduled'),
            ('Completed', 'Completed'),
            ('No-Show', 'No-Show'),
            ('Permit Processing', 'Permit Processing'),
            ('Under Construction', 'Under Construction'),
            ('Awaiting Inspection', 'Awaiting Inspection'),
            ('Finishing', 'Finishing'),
            ('Handover Pending', 'Handover Pending'),
        ],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    certificate = models.FileField(upload_to='certificates/', null=True, blank=True)  # For training certificates

    def __str__(self):
        return f"{self.full_name} - {self.company.company_name}"
    
class Comment(models.Model):
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='comments')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='comments')
    comment_text = models.TextField()
    company_response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='comments')

    def __str__(self):
        return f"Comment on Inquiry {self.inquiry.id} by {self.created_by.username if self.created_by else 'Unknown'}"
# Base model for service-specific form data
class ServiceFormData(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True  # This makes it a base class that won't create a table itself

# Engineering Consulting Form Data
class EngineeringConsultingData(ServiceFormData):
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE, related_name='engineering_data')
    type_of_building = models.CharField(max_length=50, blank=True, null=True)
    building_purpose = models.CharField(max_length=200, blank=True, null=True)
    num_floors = models.PositiveIntegerField(blank=True, null=True)
    land_area = models.CharField(max_length=50, blank=True, null=True)
    architectural_style = models.CharField(max_length=100, blank=True, null=True)
    architectural_style_other = models.CharField(max_length=100, blank=True, null=True)
    budget_estimate = models.CharField(max_length=50, blank=True, null=True)
    special_requirements = models.TextField(blank=True, null=True)
    site_plan = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    architectural_plan = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    soil_test_report = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    foundation_design = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    electrical_plan = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    plumbing_plan = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    hvac_plan = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    construction_permit = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    cost_estimation = models.FileField(upload_to='inquiry_files/engineering/', blank=True, null=True)
    structural_design = models.FileField(upload_to='inquiry_files/engineering/structural/', blank=True, null=True)
    structural_report = models.FileField(upload_to='inquiry_files/engineering/structural/', blank=True, null=True)
    architectural_design = models.FileField(upload_to='inquiry_files/engineering/architectural/', blank=True, null=True)
    cost_estimation_files = models.FileField(upload_to='inquiry_files/engineering/cost_estimation/', blank=True, null=True)
    rate_analysis = models.FileField(upload_to='inquiry_files/engineering/rate_analysis/', blank=True, null=True)
    class Meta:
        verbose_name = "Engineering Consulting Data"
        verbose_name_plural = "Engineering Consulting Data"

    def __str__(self):
        return f"Engineering Data for Inquiry #{self.inquiry.id}"

class BuildingConstructionData(ServiceFormData):
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE, related_name='building_data')
    # Existing Common fields
    lalpurja = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    napi_naksa = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    tax_clearance = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    approved_building_drawings = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    
    # Existing Residential fields
    soil_test_report = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    structural_stability_certificate = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    house_design_approval = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    neighbour_consent = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    
    # Existing Commercial fields
    iee_report = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    fire_safety_certificate = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    lift_permit = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    parking_layout_plan = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    commercial_special_requirements = models.TextField(blank=True, null=True)
    
    # Existing Renovation fields
    type_of_building = models.CharField(max_length=50, blank=True, null=True)
    existing_building_details = models.TextField(blank=True, null=True)
    owner_permission_letter = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    existing_structure_analysis = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    renovation_plan = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    noc_municipality = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    waste_management_plan = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    area_to_renovate = models.CharField(max_length=50, blank=True, null=True)
    budget_estimate = models.CharField(max_length=50, blank=True, null=True)
    renovation_special_requirements = models.TextField(blank=True, null=True)

    # New fields for Residential Construction process
    permit_application_date = models.DateField(blank=True, null=True)
    permit_status = models.CharField(max_length=50, choices=[
        ('Submitted', 'Submitted'),
        ('Under Review', 'Under Review'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ], blank=True, null=True)
    permit_document = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    construction_start_date = models.DateField(blank=True, null=True)
    construction_phase = models.CharField(max_length=50, choices=[
        ('Foundation', 'Foundation'),
        ('Walls', 'Walls'),
        ('Finishing', 'Finishing'),
        ('Excavation', 'Excavation '),
        ('Columns Casting', 'Columns Casting'),
        ('Beams Casting', 'Beams Casting'),
        ('Slab Casting', 'Slab Casting'),
        ('Roofing', 'Roofing'),
        ('Electrical & Plumbing', 'Electrical & Plumbing'),
        ('Plastering', 'Plastering'),
        ('Finishing', 'Finishing'),
    ], blank=True, null=True)
    progress_percentage = models.PositiveIntegerField(blank=True, null=True)
    progress_photos = models.JSONField(default=list, blank=True, null=True)  # Array of file paths
    inspection_dates = models.JSONField(default=list, blank=True, null=True)  # Array of dates
    inspection_reports = models.JSONField(default=list, blank=True, null=True)  # Array of file paths
    completion_certificate_application_date = models.DateField(blank=True, null=True)
    completion_certificate = models.FileField(upload_to='inquiry_files/building/', blank=True, null=True)
    handover_date = models.DateField(blank=True, null=True)
    warranty_details = models.TextField(blank=True, null=True)

# Post Construction Maintenance Form Data
class PostConstructionMaintenanceData(ServiceFormData):
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE, related_name='maintenance_data')
    maintenance_type = models.CharField(max_length=100, blank=True, null=True)
    maintenance_details = models.TextField(blank=True, null=True)
    maintenance_photos = models.FileField(upload_to='inquiry_files/maintenance/', blank=True, null=True)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.CharField(max_length=50, blank=True, null=True)
    payment_agreed = models.BooleanField(default=False)

# Safety Training Form Data
class SafetyTrainingData(ServiceFormData):
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE, related_name='training_data')
    language_preference = models.CharField(max_length=50, blank=True, null=True)
    language_preference_other = models.CharField(max_length=100, blank=True, null=True)
    training_date = models.DateField(blank=True, null=True)
    training_time = models.CharField(max_length=50, blank=True, null=True)
    training_agreement = models.BooleanField(default=False)





class Appointment(models.Model):
    inquiry = models.OneToOneField(Inquiry, on_delete=models.CASCADE, related_name='appointment')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='appointments', db_column='company_id')
    appointment_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=21)
    status = models.CharField(
        max_length=20,
        choices=[('Pending', 'Pending'), ('Confirmed', 'Confirmed'), ('No-Show', 'No-Show'), ('Completed', 'Completed')],
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inquiry.full_name} - {self.appointment_date}"
    


# ###order
# # backend/models.py
# class Order(models.Model):
#     STATUS_CHOICES_BUYING = (
#         ('paid', 'Paid'),
#         ('processing', 'Processing'),
#         ('delivered', 'Delivered'),
#         ('cancelled', 'Cancelled'),
#     )
#     STATUS_CHOICES_RENTING = (
#         ('booked', 'Booked'),
#         ('picked up', 'Picked Up'),
#         ('returned', 'Returned'),
#         ('cancelled', 'Cancelled'),
#     )
#     user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
#     company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="orders")
#     order_type = models.CharField(max_length=20, choices=[('buying', 'Buying'), ('renting', 'Renting'), ('mixed', 'Mixed')])
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     renting_details = models.JSONField(null=True, blank=True)
#     billing_details = models.JSONField(null=True, blank=True)
#     buying_status = models.CharField(max_length=20, choices=STATUS_CHOICES_BUYING, null=True, blank=True)
#     renting_status = models.CharField(max_length=20, choices=STATUS_CHOICES_RENTING, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     booking_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
#     payment_data = models.JSONField(null=True, blank=True)

#     def __str__(self):
#         return f"Order {self.id} - {self.order_type} for {self.company.company_name}"

# class OrderItem(models.Model):
#     ITEM_TYPE_CHOICES = (
#         ('buying', 'Buying'),
#         ('renting', 'Renting'),
#     )
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     quantity = models.PositiveIntegerField(default=1)
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, null=True, blank=True)  # Added item_type field

#     def __str__(self):
#         return f"{self.quantity} x {self.product.title} ({self.item_type}) in Order {self.order.id}"

# class PaymentDistribution(models.Model):
#     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_distributions")
#     company = models.ForeignKey(Company, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     payment_status = models.CharField(max_length=20, default='pending')
#     payment_reference = models.CharField(max_length=255, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     booking_id = models.CharField(max_length=255, null=True, blank=True)

#     def __str__(self):
#         return f"Payment of Rs. {self.amount} to {self.company.company_name} for Order {self.order.id}"


class Order(models.Model):
    STATUS_CHOICES_BUYING = (
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )
    STATUS_CHOICES_RENTING = (
        ('booked', 'Booked'),
        ('picked up', 'Picked Up'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="orders")
    order_type = models.CharField(max_length=20, choices=[('buying', 'Buying'), ('renting', 'Renting'), ('mixed', 'Mixed')])
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    renting_details = models.JSONField(null=True, blank=True)
    billing_details = models.JSONField(null=True, blank=True)
    buying_status = models.CharField(max_length=20, choices=STATUS_CHOICES_BUYING, null=True, blank=True)
    renting_status = models.CharField(max_length=20, choices=STATUS_CHOICES_RENTING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    booking_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    payment_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Order {self.id} - {self.order_type}"

class OrderItem(models.Model):
    ITEM_TYPE_CHOICES = (
        ('buying', 'Buying'),
        ('renting', 'Renting'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.title} ({self.item_type}) in Order {self.order.id}"

class PaymentDistribution(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payment_distributions")
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, default='pending')
    payment_reference = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    booking_id = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Payment of Rs. {self.amount} to {self.company.company_name} for Order {self.order.id}"


# models.py
from django.db import models
from django.conf import settings

class Agreement(models.Model):
    inquiry = models.ForeignKey('Inquiry', on_delete=models.CASCADE, related_name='agreements')
    company = models.ForeignKey('Company', on_delete=models.CASCADE, related_name='agreements')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='agreements')
    service = models.ForeignKey('Service', on_delete=models.CASCADE)
    company_representative_name = models.CharField(max_length=100, blank=True, null=True)  # Manual input for company rep name
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Service charge in NPR
    document = models.FileField(upload_to='agreements/', blank=True, null=True)  # Generated agreement PDF
    signed_document = models.FileField(upload_to='signed_agreements/', blank=True, null=True)  # Signed agreement uploaded by client/company
    status = models.CharField(
        max_length=20,
        choices=[('Draft', 'Draft'), ('Sent', 'Sent'), ('Signed', 'Signed'), ('Rejected', 'Rejected')],
        default='Draft'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    signed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Agreement for {self.inquiry.full_name} - {self.service.name}"
    


# from django.db import models
# from django.utils import timezone
# from datetime import timedelta

# class Subscription(models.Model):
#     PLAN_CHOICES = (
#         ('monthly', 'Monthly'),
#         ('quarterly', 'Quarterly'),
#         ('yearly', 'Yearly'),
#     )

#     company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscriptions')
#     plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
#     start_date = models.DateTimeField(default=timezone.now)
#     end_date = models.DateTimeField(null=True, blank=True)  # Allow null for trial
#     trial_end_date = models.DateTimeField(null=True, blank=True)  # Track trial period
#     grace_end_date = models.DateTimeField(null=True, blank=True)  # Track grace period
#     is_active = models.BooleanField(default=True)
#     payment_data = models.JSONField(null=True, blank=True)

#     def save(self, *args, **kwargs):
#         # Set end_date based on plan
#         if not self.end_date:
#             duration_days = {
#                 'monthly': 30,
#                 'quarterly': 90,
#                 'yearly': 365,
#             }
#             self.end_date = self.start_date + timedelta(days=duration_days[self.plan])
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return f"{self.company.company_name} - {self.plan} Subscription"
from django.db import models
from django.utils import timezone
from datetime import timedelta

class Subscription(models.Model):
    PLAN_CHOICES = (
        ('trial', 'Trial'),  # trial as a plan type
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)
    grace_end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    payment_data = models.JSONField(null=True, blank=True)
    has_used_trial = models.BooleanField(default=False)  # Track if trial was used

    def save(self, *args, **kwargs):
        # Set end_date based on plan
        if self.plan == 'trial':
            if not self.trial_end_date:
                self.trial_end_date = self.start_date + timedelta(days=15)
                self.has_used_trial = True
                self.amount = 0.00
        else:
            duration_days = {
                'monthly': 30,
                'quarterly': 90,
                'yearly': 365,
            }
            if not self.end_date:
                self.end_date = self.start_date + timedelta(days=duration_days[self.plan])
            # Set grace period to 5 days after subscription end
            self.grace_end_date = self.end_date + timedelta(days=5)

        super().save(*args, **kwargs)

    def is_valid(self):
        now = timezone.now()
        # Check if subscription is within trial, active period, or grace period
        if self.plan == 'trial' and self.trial_end_date and now <= self.trial_end_date:
            return True
        if self.end_date and now <= self.end_date:
            return True
        if self.grace_end_date and now <= self.grace_end_date:
            return True
        return False

    def __str__(self):
        return f"{self.company.company_name} - {self.plan} Subscription"


class Plan(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50)
    days = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['days']


from django.db import models
from django.conf import settings

class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    type = models.CharField(max_length=50)  # e.g., "inquiry_new", "order_status"
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["recipient", "created_at"])]

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"




from django.db import models
from django.core.validators import MinValueValidator

class Payment(models.Model):
    inquiry = models.ForeignKey(
        'Inquiry',  # Adjust to your Inquiry model name
        on_delete=models.CASCADE,
        related_name='payments'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    payment_method = models.CharField(max_length=50)  # e.g., 'stripe'
    purpose = models.CharField(max_length=255, blank=True, null=True)  # New field for payment purpose
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment for Inquiry {self.inquiry.id}"