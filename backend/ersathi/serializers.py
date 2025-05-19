from rest_framework import serializers
from .models import BuildingConstructionData, EngineeringConsultingData, PostConstructionMaintenanceData, SafetyTrainingData, Service, Company, Product, ServiceCategory, CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ['id', 'name']

class ServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)  # Nested serializer for category
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ServiceCategory.objects.all(), source='category', write_only=True
    )  # For writing (e.g., when creating/updating a service)

    class Meta:
        model = Service
        fields = ['id', 'name', 'category', 'category_id']


class CompanyRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = '__all__'



class CompanySerializer(serializers.ModelSerializer):
    registration_certificate = serializers.FileField(required=False, allow_null=True)
    class Meta:
        model = Company
        fields = ['id', 'company_name', 'location', 'company_type','company_email','registration_certificate', ]  # Fields needed by frontend

class ProductSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.company_name', read_only=True)  
    class Meta:
        model = Product
        fields = '__all__'
    def get_image(self, obj):
        request = self.context.get('request')  # Pass `request` context from views
        if obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None
    


from rest_framework import serializers
from .models import RentVerification, VerificationImage

class VerificationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationImage
        fields = ['id', 'image']

class RentVerificationSerializer(serializers.ModelSerializer):
    images = VerificationImageSerializer(many=True, read_only=True)
    uploaded_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = RentVerification
        fields = ['id', 'full_name', 'email', 'phone', 'address', 
                 'status', 'submitted_at', 'images', 'uploaded_images']

    def create(self, validated_data):
        uploaded_images = validated_data.pop('uploaded_images', [])
        verification = RentVerification.objects.create(**validated_data)
        
        for image in uploaded_images:
            VerificationImage.objects.create(verification=verification, image=image)
        
        return verification

    def update(self, instance, validated_data):
        # Remove non-editable fields to prevent accidental updates
        validated_data.pop('full_name', None)
        validated_data.pop('email', None)
        validated_data.pop('phone', None)

        uploaded_images = validated_data.pop('uploaded_images', [])
        
        # Update address only
        instance.address = validated_data.get('address', instance.address)
        instance.status = "pending"  # status will be pending after resubmitting!
        instance.save()
        
        # Delete existing images and add new ones
        instance.images.all().delete()
        for image in uploaded_images:
            VerificationImage.objects.create(verification=instance, image=image)
        
        return instance
    
from rest_framework import serializers
from .models import CompanyInfo, ProjectInfo, TeamMemberInfo

class ProjectInfoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(allow_empty_file=True, required=False)

    class Meta:
        model = ProjectInfo
        fields = ['id', 'name', 'description', 'year', 'image']


class TeamMemberInfoSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(allow_empty_file=True, required=False)

    class Meta:
        model = TeamMemberInfo
        fields = ['id', 'name', 'role', 'avatar']


class CompanyInfoSerializer(serializers.ModelSerializer):
    projects = ProjectInfoSerializer(many=True, required=False)
    team = TeamMemberInfoSerializer(many=True, required=False)

    class Meta:
        model = CompanyInfo
        fields = [
            'id',
            'company',
            'company_name',
            'company_email',
            'phone_number',
            'address',
            'logo',
            'about_us',
            'projects',
            'team'
        ]

    def create(self, validated_data):
        projects_data = validated_data.pop('projects', [])
        team_data = validated_data.pop('team', [])
       

        # CompanyInfo instance
        company_info = CompanyInfo.objects.create(**validated_data)

        # Create nested projects
        for project_data in projects_data:
            ProjectInfo.objects.create(company=company_info, **project_data)

        # Create nested team members
        for member_data in team_data:
            TeamMemberInfo.objects.create(company=company_info, **member_data)

        return company_info

    def update(self, instance, validated_data):
        projects_data = validated_data.pop('projects', [])
        team_data = validated_data.pop('team', [])

        # Update simple fields
        instance.company_name = validated_data.get('company_name', instance.company_name)
        instance.company_email = validated_data.get('company_email', instance.company_email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)
        if 'logo' in validated_data:
            instance.logo = validated_data['logo']
        instance.about_us = validated_data.get('about_us', instance.about_us)
        instance.save()

        # Recreate projects if data is provided
        if projects_data:
            instance.projects.all().delete()
            for project_data in projects_data:
                ProjectInfo.objects.create(company=instance, **project_data)

        # Recreate team if data is provided
        if team_data:
            instance.team_members.all().delete()
            for member_data in team_data:
                TeamMemberInfo.objects.create(company=instance, **member_data)

        return instance


# serializers.py
# from rest_framework import serializers
# from .models import Inquiry, Appointment, Company
# class AppointmentSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Appointment
#         fields = ['id', 'appointment_date']
# class InquirySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Inquiry
#         fields = ['id', 'full_name', 'location', 'email', 'phone_number', 'category', 'sub_service', 'status', 'created_at']

# class EngineeringConsultingDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = EngineeringConsultingData
#         fields = '__all__'

# class BuildingConstructionDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = BuildingConstructionData
#         fields = '__all__'

# class PostConstructionMaintenanceDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PostConstructionMaintenanceData
#         fields = '__all__'

# class SafetyTrainingDataSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SafetyTrainingData
#         fields = '__all__'

# class AppointmentSerializer(serializers.ModelSerializer):
#     inquiry = InquirySerializer(read_only=True)
#     company = serializers.CharField(source='company.company_name', read_only=True)
    
#     class Meta:
#         model = Appointment
#         fields = ['id', 'inquiry', 'company', 'appointment_date', 'duration_minutes', 'status', 'created_at']
# serializers.py
from rest_framework import serializers
from .models import Inquiry, Appointment, Company, EngineeringConsultingData, BuildingConstructionData, PostConstructionMaintenanceData, SafetyTrainingData, Comment

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'appointment_date']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'comment_text','company_response', 'created_at']
class EngineeringConsultingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineeringConsultingData
        fields = '__all__'

class BuildingConstructionDataSerializer(serializers.ModelSerializer):
    # Override file fields to return absolute URLs
    lalpurja = serializers.SerializerMethodField()
    napi_naksa = serializers.SerializerMethodField()
    tax_clearance = serializers.SerializerMethodField()
    approved_building_drawings = serializers.SerializerMethodField()
    soil_test_report = serializers.SerializerMethodField()
    structural_stability_certificate = serializers.SerializerMethodField()
    house_design_approval = serializers.SerializerMethodField()
    neighbour_consent = serializers.SerializerMethodField()
    iee_report = serializers.SerializerMethodField()
    fire_safety_certificate = serializers.SerializerMethodField()
    lift_permit = serializers.SerializerMethodField()
    parking_layout_plan = serializers.SerializerMethodField()
    owner_permission_letter = serializers.SerializerMethodField()
    existing_structure_analysis = serializers.SerializerMethodField()
    renovation_plan = serializers.SerializerMethodField()
    noc_municipality = serializers.SerializerMethodField()
    waste_management_plan = serializers.SerializerMethodField()
    permit_document = serializers.SerializerMethodField()
    completion_certificate = serializers.SerializerMethodField()
    
    # Override JSON fields with file paths to return absolute URLs
    progress_photos = serializers.SerializerMethodField()
    inspection_reports = serializers.SerializerMethodField()

    class Meta:
        model = BuildingConstructionData
        fields = [
            'id', 'inquiry', 'lalpurja', 'napi_naksa', 'tax_clearance', 'approved_building_drawings',
            'soil_test_report', 'structural_stability_certificate', 'house_design_approval', 'neighbour_consent',
            'iee_report', 'fire_safety_certificate', 'lift_permit', 'parking_layout_plan',
            'commercial_special_requirements', 'type_of_building', 'existing_building_details',
            'owner_permission_letter', 'existing_structure_analysis', 'renovation_plan', 'noc_municipality',
            'waste_management_plan', 'area_to_renovate', 'budget_estimate', 'renovation_special_requirements',
            'permit_application_date', 'permit_status', 'permit_document', 'construction_start_date',
            'construction_phase', 'progress_percentage', 'progress_photos', 'inspection_dates',
            'inspection_reports', 'completion_certificate_application_date', 'completion_certificate',
            'handover_date', 'warranty_details'
        ]

    def get_file_url(self, obj, field_name):
        try:
            field = getattr(obj, field_name)
            if field and hasattr(field, 'url'):
                request = self.context.get('request')
                return request.build_absolute_uri(field.url) if request else field.url
            return None
        except Exception as e:
            print(f"Error serializing {field_name} for BuildingConstructionData {obj.id}: {str(e)}")
            return None

    # Define methods for each file field
    def get_lalpurja(self, obj):
        return self.get_file_url(obj, 'lalpurja')

    def get_napi_naksa(self, obj):
        return self.get_file_url(obj, 'napi_naksa')

    def get_tax_clearance(self, obj):
        return self.get_file_url(obj, 'tax_clearance')

    def get_approved_building_drawings(self, obj):
        return self.get_file_url(obj, 'approved_building_drawings')

    def get_soil_test_report(self, obj):
        return self.get_file_url(obj, 'soil_test_report')

    def get_structural_stability_certificate(self, obj):
        return self.get_file_url(obj, 'structural_stability_certificate')

    def get_house_design_approval(self, obj):
        return self.get_file_url(obj, 'house_design_approval')

    def get_neighbour_consent(self, obj):
        return self.get_file_url(obj, 'neighbour_consent')

    def get_iee_report(self, obj):
        return self.get_file_url(obj, 'iee_report')

    def get_fire_safety_certificate(self, obj):
        return self.get_file_url(obj, 'fire_safety_certificate')

    def get_lift_permit(self, obj):
        return self.get_file_url(obj, 'lift_permit')

    def get_parking_layout_plan(self, obj):
        return self.get_file_url(obj, 'parking_layout_plan')

    def get_owner_permission_letter(self, obj):
        return self.get_file_url(obj, 'owner_permission_letter')

    def get_existing_structure_analysis(self, obj):
        return self.get_file_url(obj, 'existing_structure_analysis')

    def get_renovation_plan(self, obj):
        return self.get_file_url(obj, 'renovation_plan')

    def get_noc_municipality(self, obj):
        return self.get_file_url(obj, 'noc_municipality')

    def get_waste_management_plan(self, obj):
        return self.get_file_url(obj, 'waste_management_plan')

    def get_permit_document(self, obj):
        return self.get_file_url(obj, 'permit_document')

    def get_completion_certificate(self, obj):
        return self.get_file_url(obj, 'completion_certificate')

    # Handle JSON fields with file paths
    def get_progress_photos(self, obj):
        try:
            photos = obj.progress_photos or []
            request = self.context.get('request')
            return [
                request.build_absolute_uri(f"/media/{path}") if request else f"/media/{path}"
                for path in photos
            ] if photos else []
        except Exception as e:
            print(f"Error serializing progress_photos for BuildingConstructionData {obj.id}: {str(e)}")
            return []

    def get_inspection_reports(self, obj):
        try:
            reports = obj.inspection_reports or []
            request = self.context.get('request')
            return [
                request.build_absolute_uri(f"/media/{path}") if request else f"/media/{path}"
                for path in reports
            ] if reports else []
        except Exception as e:
            print(f"Error serializing inspection_reports for BuildingConstructionData {obj.id}: {str(e)}")
            return []

class PostConstructionMaintenanceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostConstructionMaintenanceData
        fields = '__all__'

class SafetyTrainingDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SafetyTrainingData
        fields = '__all__'


from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'purpose', 'created_at']

# class InquirySerializer(serializers.ModelSerializer):
#     service_data = serializers.SerializerMethodField()
#     certificate = serializers.SerializerMethodField()
#     comments = CommentSerializer(many=True, read_only=True)
#     class Meta:
#         model = Inquiry
#         fields = [
#             'id', 'full_name', 'location', 'email', 'phone_number',
#             'category', 'sub_service', 'status', 'created_at', 'certificate',
#             'service_data', 'comments'
#         ]

#     def get_service_data(self, obj):
#         try:
#             if obj.category == "Engineering Consulting" and hasattr(obj, 'engineering_data') and obj.engineering_data:
#                 return EngineeringConsultingDataSerializer(obj.engineering_data, context=self.context).data
#             elif obj.category == "Building Construction Services" and hasattr(obj, 'building_data') and obj.building_data:
#                 return BuildingConstructionDataSerializer(obj.building_data, context=self.context).data
#             elif obj.category == "Post-Construction Maintenance" and hasattr(obj, 'maintenance_data') and obj.maintenance_data:
#                 return PostConstructionMaintenanceDataSerializer(obj.maintenance_data, context=self.context).data
#             elif obj.category == "Safety and Training Services" and hasattr(obj, 'training_data') and obj.training_data:
#                 return SafetyTrainingDataSerializer(obj.training_data, context=self.context).data
#             return {}
#         except Exception as e:
#             print(f"Error serializing service_data for inquiry {obj.id}: {str(e)}")
#             return {}

#     def get_certificate(self, obj):
#         try:
#             if obj.certificate and hasattr(obj.certificate, 'url'):
#                 request = self.context.get('request')
#                 return request.build_absolute_uri(obj.certificate.url) if request else obj.certificate.url
#             return None
#         except Exception as e:
#             print(f"Error serializing certificate for inquiry {obj.id}: {str(e)}")
#             return None
class InquirySerializer(serializers.ModelSerializer):
    service_data = serializers.SerializerMethodField()
    certificate = serializers.SerializerMethodField()
    comments = CommentSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)  # Add payments field

    class Meta:
        model = Inquiry
        fields = [
            'id', 'full_name', 'location', 'email', 'phone_number',
            'category', 'sub_service', 'status', 'created_at', 'certificate',
            'service_data', 'comments', 'payments'  
        ]

    def get_service_data(self, obj):
        try:
            if obj.category == "Engineering Consulting" and hasattr(obj, 'engineering_data') and obj.engineering_data:
                return EngineeringConsultingDataSerializer(obj.engineering_data, context=self.context).data
            elif obj.category == "Building Construction Services" and hasattr(obj, 'building_data') and obj.building_data:
                return BuildingConstructionDataSerializer(obj.building_data, context=self.context).data
            elif obj.category == "Post-Construction Maintenance" and hasattr(obj, 'maintenance_data') and obj.maintenance_data:
                return PostConstructionMaintenanceDataSerializer(obj.maintenance_data, context=self.context).data
            elif obj.category == "Safety and Training Services" and hasattr(obj, 'training_data') and obj.training_data:
                return SafetyTrainingDataSerializer(obj.training_data, context=self.context).data
            return {}
        except Exception as e:
            print(f"Error serializing service_data for inquiry {obj.id}: {str(e)}")
            return {}

    def get_certificate(self, obj):
        try:
            if obj.certificate and hasattr(obj.certificate, 'url'):
                request = self.context.get('request')
                return request.build_absolute_uri(obj.certificate.url) if request else obj.certificate.url
            return None
        except Exception as e:
            print(f"Error serializing certificate for inquiry {obj.id}: {str(e)}")
            return None  
        
class AppointmentSerializer(serializers.ModelSerializer):
    inquiry = InquirySerializer(read_only=True)
    company = serializers.CharField(source='company.company_name', read_only=True)
    
    class Meta:
        model = Appointment
        fields = ['id', 'inquiry', 'company', 'appointment_date', 'duration_minutes', 'status', 'created_at']


from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'amount', 'payment_method', 'purpose', 'created_at']

# backend/serializers.py
# from rest_framework import serializers
# from .models import Order, OrderItem

# class OrderItemSerializer(serializers.ModelSerializer):
#     product_name = serializers.CharField(source="product.title", read_only=True)
#     company_id = serializers.CharField(source="product.company.id", read_only=True)

#     class Meta:
#         model = OrderItem
#         fields = ['id', 'product', 'product_name', 'quantity', 'price', 'company_id', 'item_type']
# # backend/serializers.py
# class OrderSerializer(serializers.ModelSerializer):
#     buying_items = serializers.SerializerMethodField()
#     renting_items = serializers.SerializerMethodField()
#     company_amounts = serializers.SerializerMethodField()

#     class Meta:
#         model = Order
#         fields = [
#             'id', 'order_type', 'buying_items', 'renting_items', 'total_amount',
#             'renting_details', 'billing_details', 'buying_status', 'renting_status',
#             'created_at', 'booking_id', 'company_amounts', 'payment_data'
#         ]

#     def get_buying_items(self, obj):
#         buying_items = obj.items.filter(item_type='buying')
#         return OrderItemSerializer(buying_items, many=True).data

#     def get_renting_items(self, obj):
#         renting_items = obj.items.filter(item_type='renting')
#         return OrderItemSerializer(renting_items, many=True).data

#     def get_company_amounts(self, obj):
#         company_amounts = {}
#         for item in obj.items.all():
#             company_id = item.product.company.id
#             amount = item.price * item.quantity
#             company_amounts[str(company_id)] = company_amounts.get(str(company_id), 0) + float(amount)
#         return company_amounts

from rest_framework import serializers
from .models import Order, OrderItem

class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.title", read_only=True)
    company_id = serializers.CharField(source="product.company.id", read_only=True)
    company_name = serializers.CharField(source="product.company.company_name", read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'quantity', 'price', 'company_id', 'company_name', 'item_type']

# class OrderSerializer(serializers.ModelSerializer):
#     buying_items = serializers.SerializerMethodField()
#     renting_items = serializers.SerializerMethodField()
#     company_amounts = serializers.SerializerMethodField()

#     class Meta:
#         model = Order
#         fields = [
#             'id', 'order_type', 'buying_items', 'renting_items', 'total_amount',
#             'renting_details', 'billing_details', 'buying_status', 'renting_status',
#             'created_at', 'booking_id', 'company_amounts', 'payment_data'
#         ]

#     def get_buying_items(self, obj):
#         # Get the company_id from the context (passed from the view)
#         company_id = self.context.get('company_id')
#         buying_items = obj.items.filter(item_type='buying')
#         # Filter items to include only those belonging to the logged-in company
#         if company_id:
#             buying_items = buying_items.filter(product__company__id=company_id)
#         return OrderItemSerializer(buying_items, many=True).data

#     def get_renting_items(self, obj):
#         # Get the company_id from the context
#         company_id = self.context.get('company_id')
#         renting_items = obj.items.filter(item_type='renting')
#         # Filter items to include only those belonging to the logged-in company
#         if company_id:
#             renting_items = renting_items.filter(product__company__id=company_id)
#         return OrderItemSerializer(renting_items, many=True).data

#     def get_company_amounts(self, obj):
#         # Get the company_id from the context
#         company_id = self.context.get('company_id')
#         company_amounts = {}
#         for item in obj.items.all():
#             item_company_id = str(item.product.company.id)
#             # Only include amounts for the logged-in company
#             if company_id and item_company_id != str(company_id):
#                 continue
#             amount = item.price * item.quantity
#             # For renting items, multiply by renting days if applicable
#             if item.item_type == 'renting' and obj.renting_details:
#                 amount *= obj.renting_details.get('rentingDays', 1)
#             company_amounts[item_company_id] = company_amounts.get(item_company_id, 0) + float(amount)
#         return company_amounts
class OrderSerializer(serializers.ModelSerializer):
    buying_items = serializers.SerializerMethodField()
    renting_items = serializers.SerializerMethodField()
    company_amounts = serializers.SerializerMethodField()
    total_amount = serializers.SerializerMethodField()  # Override total_amount

    class Meta:
        model = Order
        fields = [
            'id', 'order_type', 'buying_items', 'renting_items', 'total_amount',
            'renting_details', 'billing_details', 'buying_status', 'renting_status',
            'created_at', 'booking_id', 'company_amounts', 'payment_data'
        ]

    def get_buying_items(self, obj):
        company_id = self.context.get('company_id')
        buying_items = obj.items.filter(item_type='buying')
        if company_id:
            buying_items = buying_items.filter(product__company__id=company_id)
        return OrderItemSerializer(buying_items, many=True).data

    def get_renting_items(self, obj):
        company_id = self.context.get('company_id')
        renting_items = obj.items.filter(item_type='renting')
        if company_id:
            renting_items = renting_items.filter(product__company__id=company_id)
        return OrderItemSerializer(renting_items, many=True).data

    def get_company_amounts(self, obj):
        company_id = self.context.get('company_id')
        company_amounts = {}
        for item in obj.items.all():
            item_company_id = str(item.product.company.id)
            if company_id and item_company_id != str(company_id):
                continue
            amount = item.price * item.quantity
            if item.item_type == 'renting' and obj.renting_details:
                amount *= obj.renting_details.get('rentingDays', 1)
            company_amounts[item_company_id] = company_amounts.get(item_company_id, 0) + float(amount)
        return company_amounts

    def get_total_amount(self, obj):
        # Calculate total_amount based on the filtered items
        buying_items = self.get_buying_items(obj)
        renting_items = self.get_renting_items(obj)

        total = 0.0

        # Sum for buying items
        for item in buying_items:
            total += float(item['quantity']) * float(item['price'])

        # Sum for renting items (considering renting days)
        for item in renting_items:
            renting_days = obj.renting_details.get('rentingDays', 1) if obj.renting_details else 1
            total += float(item['quantity']) * float(item['price']) * renting_days

        return str(total)  # Return as string to match the original format









#aggrement
from rest_framework import serializers
from .models import Agreement

class AgreementSerializer(serializers.ModelSerializer):
    document = serializers.SerializerMethodField()
    signed_document = serializers.SerializerMethodField()

    class Meta:
        model = Agreement
        fields = ['id', 'inquiry', 'company', 'user', 'service', 'company_representative_name', 'service_charge', 'document', 'signed_document', 'status', 'created_at', 'signed_at']
        read_only_fields = ['created_at', 'signed_at']

    def get_document(self, obj):
        if obj.document:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.document.url)
        return None

    def get_signed_document(self, obj):
        if obj.signed_document:
            request = self.context.get('request')
            return request.build_absolute_uri(obj.signed_document.url)
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Include nested fields for inquiry and service
        representation['inquiry'] = {'full_name': instance.inquiry.full_name}
        representation['service'] = {'name': instance.service.name}
        return representation
    

from rest_framework import serializers
from .models import Subscription
class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'plan', 'amount', 'start_date', 'end_date', 'trial_end_date', 'grace_end_date', 'is_active', 'payment_data', 'has_used_trial']

from .models import Plan
class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['name', 'price', 'duration', 'days']




# api/serializers.py
from rest_framework import serializers
from .models import Company, CompanyServices

class FeaturedCompanySerializer(serializers.ModelSerializer):
    description = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    service_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['company_name', 'description', 'average_rating', 'service_count', 'company_type']

    def get_description(self, obj):
        # Generate a description based on services provided
        services = obj.company_services.filter(status="Available").select_related('service')
        if services.exists():
            service_names = [cs.service.name for cs in services]
            return f"Specializing in {', '.join(service_names[:2])}.{'..' if len(service_names) > 2 else ''}"
        return "Providing a range of construction services."

    def get_average_rating(self, obj):
        return obj.average_rating()

    def get_service_count(self, obj):
        return obj.company_services.filter(status="Available").count()

# from rest_framework import serializers
# from .models import ChatChannel

# class ChatChannelSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ChatChannel
#         fields = ['channel_id', 'channel_type', 'user', 'company', 'admin', 'created_at', 'is_active']



# class ChatMessageSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = ChatMessage
#         fields = ['sender', 'message', 'created_at']


# serializers.py
from rest_framework import serializers
from .models import Rating, Product

class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ['id', 'product', 'user', 'rating', 'created_at']
        read_only_fields = ['user', 'created_at']


    

from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    inquiry_id = serializers.IntegerField(write_only=True)
    payment_method = serializers.CharField(required=False)

    class Meta:
        model = Payment
        fields = ['id', 'inquiry_id', 'amount', 'payment_method', 'purpose', 'created_at']
        read_only_fields = ['id', 'created_at']