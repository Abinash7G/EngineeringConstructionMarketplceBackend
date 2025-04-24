from ast import Load
import token
from typing import Generic
from django.contrib.auth.models import Group
from django.forms import ValidationError
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils.crypto import get_random_string


from .models import Company, CompanyRating, Plan 
from .serializers import CommentSerializer, CompanyRegistrationSerializer, OrderSerializer, PlanSerializer, SubscriptionSerializer
from rest_framework.decorators import api_view

from .models import Service  # Import your Service model
from .serializers import ServiceSerializer

from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils.timezone import now


from rest_framework.decorators import api_view , permission_classes

from itsdangerous import URLSafeTimedSerializer

import os
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from dotenv import load_dotenv

# Configure a secret key (use a strong, unique key)
SECRET_KEY = "2e14a6352c97c2fe33315af6804d89d474432d4d5835326005d55695fd8a4274"
SALT = "c3d00104b56828f98d4592e81dba0ece"

def generate_verification_token(email):
    """
    Generate a token for email verification.
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=SALT)

def verify_verification_token(token, expiration=3600):
    """
    Verify the token and return the email if valid.
    :param token: The token to verify.
    :param expiration: Expiry time in seconds.
    """
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(token, salt=SALT, max_age=expiration)
        return email
    except Exception as e:
        return None  # Token is invalid or expired










# class ServiceList(APIView):
#     def get(self, request):
#         return Response({"message": "Service List View is working!"})



from django.http import JsonResponse
from .models import ServiceCategory, Service, CompanyServices
from django.core.exceptions import ObjectDoesNotExist

@csrf_exempt
def get_services(request):
    """Returns all service categories and their sub-services"""
    try:
        categories = ServiceCategory.objects.all().prefetch_related('services')
        data = [
            {
                "category": category.name,
                "services": [
                    {"id": service.id, "name": service.name}
                    for service in category.services.all()
                ]
            }
            for category in categories
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Error in get_services: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
###
# #
# #
# #compayadded service
##
##from django.http import JsonResponse
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.exceptions import ObjectDoesNotExist
from .models import CompanyServices, Service
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Company  # Import the Company model
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
def get_company_services(request):
    """Returns all services added by the company"""
    try:
        auth = JWTAuthentication()
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith('Bearer '):
            return JsonResponse({"error": "Invalid authorization header"}, status=401)
        
        token = header.split(' ')[1]
        validated_token = auth.get_validated_token(token)
        user = auth.get_user(validated_token)

        if not user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        # Get the company associated with the user
        try:
            company = Company.objects.get(id=user.company_id)  # Use company_id from ersathi_customuser
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Company not found for this user"}, status=404)

        services = CompanyServices.objects.filter(company=company).select_related('service__category')
        data = [
            {
                "id": service.id,
                "category": service.service.category.name,
                "sub_service": service.service.name,
                "price": float(service.price),
                "status": service.status,
                "company_id": service.company.id,
                "service_id": service.service.id
            }
            for service in services
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Error in get_company_services: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)

@csrf_exempt
def create_company_service(request):
    """Create a new service for the company"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.debug(f"Received data: {data}")
            auth = JWTAuthentication()
            header = request.META.get('HTTP_AUTHORIZATION', '')
            if not header.startswith('Bearer '):
                return JsonResponse({"error": "Invalid authorization header"}, status=401)
            
            token = header.split(' ')[1]
            validated_token = auth.get_validated_token(token)
            user = auth.get_user(validated_token)

            if not user.is_authenticated:
                return JsonResponse({"error": "Authentication required"}, status=401)

            service_id = data.get('service_id')
            if not service_id:
                return JsonResponse({"error": "Service ID is required"}, status=400)

            try:
                service = Service.objects.get(id=service_id)
                logger.debug(f"Found service: {service.name}, ID: {service.id}, Category: {service.category.name}")
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Service not found"}, status=404)

            # Get the company associated with the user using company_id from ersathi_customuser
            try:
                company = Company.objects.get(id=user.company_id)  # Use company_id from the user
                if not company:
                    return JsonResponse({"error": "Company not found for this user"}, status=404)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Company not found for this user"}, status=404)

            try:
                company_service, created = CompanyServices.objects.get_or_create(
                    company=company,  # Use the Company instance
                    service=service,
                    defaults={
                        'price': data['price'],
                        'status': data['status']
                    }
                )
                if not created:
                    company_service.price = data['price']
                    company_service.status = data['status']
                    company_service.save()
                    logger.info(f"Updated existing service for company {company.id}, service {service.id}")
                else:
                    logger.info(f"Created new service for company {company.id}, service {service.id}")

                return JsonResponse({
                    "id": company_service.id,
                    "category": company_service.service.category.name,
                    "sub_service": company_service.service.name,
                    "price": float(company_service.price),
                    "status": company_service.status,
                    "company_id": company_service.company.id,  # Return the actual company_id
                    "service_id": company_service.service.id
                }, status=201)  # Use 201 for created
            except Exception as e:
                logger.error(f"Database error details: {str(e)}")
                return JsonResponse({"error": f"Database error: {str(e)}"}, status=400)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Service or company not found"}, status=404)
        except KeyError as e:
            return JsonResponse({"error": f"Missing required field: {str(e)}"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def update_company_service(request, service_id):
    """Update an existing service for the company"""
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            auth = JWTAuthentication()
            header = request.META.get('HTTP_AUTHORIZATION', '')
            if not header.startswith('Bearer '):
                return JsonResponse({"error": "Invalid authorization header"}, status=401)
            
            token = header.split(' ')[1]
            validated_token = auth.get_validated_token(token)
            user = auth.get_user(validated_token)

            if not user.is_authenticated:
                return JsonResponse({"error": "Authentication required"}, status=401)

            # Get the company associated with the user
            try:
                company = Company.objects.get(id=user.company_id)  # Use company_id from ersathi_customuser
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Company not found for this user"}, status=404)

            try:
                company_service = CompanyServices.objects.get(id=service_id, company=company)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Service not found or unauthorized"}, status=404)

            if 'service_id' in data:
                try:
                    new_service = Service.objects.get(id=data['service_id'])
                    company_service.service = new_service
                except ObjectDoesNotExist:
                    return JsonResponse({"error": "New service not found"}, status=404)

            company_service.price = data.get('price', company_service.price)
            company_service.status = data.get('status', company_service.status)
            company_service.save()

            return JsonResponse({
                "id": company_service.id,
                "category": company_service.service.category.name,
                "sub_service": company_service.service.name,
                "price": float(company_service.price),
                "status": company_service.status,
                "company_id": company_service.company.id,
                "service_id": company_service.service.id
            })
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Service not found or unauthorized"}, status=404)
        except Exception as e:
            logger.error(f"Error updating service: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def delete_company_service(request, service_id):
    """Delete a service for the company"""
    if request.method == 'DELETE':
        try:
            auth = JWTAuthentication()
            header = request.META.get('HTTP_AUTHORIZATION', '')
            if not header.startswith('Bearer '):
                return JsonResponse({"error": "Invalid authorization header"}, status=401)
            
            token = header.split(' ')[1]
            validated_token = auth.get_validated_token(token)
            user = auth.get_user(validated_token)

            if not user.is_authenticated:
                return JsonResponse({"error": "Authentication required"}, status=401)

            # Get the company associated with the user
            try:
                company = Company.objects.get(id=user.company_id)  # Use company_id from ersathi_customuser
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Company not found for this user"}, status=404)

            try:
                company_service = CompanyServices.objects.get(id=service_id, company=company)
                company_service.delete()
                return JsonResponse({"message": "Service deleted successfully"})
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Service not found or unauthorized"}, status=404)
        except Exception as e:
            logger.error(f"Error deleting service: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


    #companyservice view
@csrf_exempt
def get_company_services_basic(request):
    """Returns only category and sub_service for services"""
    try:
        auth = JWTAuthentication()
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith('Bearer '):
            return JsonResponse({"error": "Invalid authorization header"}, status=401)
        
        token = header.split(' ')[1]
        validated_token = auth.get_validated_token(token)
        user = auth.get_user(validated_token)

        if not user.is_authenticated:
            return JsonResponse({"error": "Authentication required"}, status=401)

        try:
            company = Company.objects.get(id=user.company_id)
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Company not found for this user"}, status=404)

        services = CompanyServices.objects.filter(company=company).select_related('service__category')
        data = [
            {
                "category": service.service.category.name,
                "sub_service": service.service.name,
            }
            for service in services
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Error in get_company_services_basic: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)




# Dynamically get the user model
CustomUser = get_user_model()

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data

        if CustomUser.objects.filter(username=data.get('username')).exists():
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(email=data.get('email')).exists():
            return Response({'error': 'Email already in use'}, status=status.HTTP_400_BAD_REQUEST)

        user = CustomUser.objects.create_user(
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            password=data.get('password'),
            phone_number=data.get('phoneNumber'),
        )
        user.is_active = False  # Disable login until email is verified
        user.save()

        

        # Send confirmation email
        confirmation_link = f"http://localhost:3001/confirm-email/{generate_verification_token(email=user.email)}"
        send_mail(
            subject="Email Confirmation",
            message=f"Hi {user.username},\n\nPlease confirm your email by clicking the link below:\n{confirmation_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
        )

        return Response({'message': 'Signup successful! Check your email to confirm your account.'}, status=status.HTTP_201_CREATED)

#email confirmation endpoint
class ConfirmEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
            # First check if the user is already verified
            email = verify_verification_token(token)
            if not email: 
                return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
            user = CustomUser.objects.filter(email=email).first()
            if user and user.is_verified:
                return Response({
                    'message': 'Your email has already been verified. You can now login.',
                    'status': 'already_verified'
                }, status=status.HTTP_200_OK)

            # Confirm the user
            user.is_active = True
            user.is_verified = True
            # Check if the group "Platformadmin" exists
            group, created = Group.objects.get_or_create(name='User')
            # Add the user to the group
            user.groups.add(group)
            user.save()

            

            # Send success response before deleting the token
            response = Response({
                'message': 'Email successfully confirmed! You can now login.',
                'status': 'verified'
            }, status=status.HTTP_200_OK)

            # Delete the token after sending the response
            #confirmation_token.delete()
            return response
        



#LOGIN LOGIC
from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        
        if user:
            groups = user.groups.first()
               

            # Include company_id in the response
            company_id = user.company.id if user.company else None
            company_type = user.company.company_type if user.company else None
            
            # Generate tokens
            
            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": groups.name if groups else None,
                "company_id": company_id,  # Add company_id to the response
                "company_type": company_type,
                "id": user.id  # Add user_id to the response
                
            }, status=status.HTTP_200_OK)
        
        return Response({"message": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        
class ForgotPasswordView(APIView):
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')  # Extract the email from the request
        User = get_user_model()  # Dynamically retrieve the custom user model

        try:
            user = User.objects.get(email=email)  # Get the user by email
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=400)
        
        reset_url = f"http://localhost:3001/restpasswordview/{generate_verification_token(email=user.email)}/"

        send_mail(
                subject="Password Reset Request",
                message=f"Click the link below to reset your password://\n{reset_url}",
                from_email="noreply@yourdomain.com",  # Replace with your sender email
                recipient_list=[email],
                fail_silently=False,
            )
        # Logic for sending the password reset email goes here
        return Response({"success": "Password reset email sent successfully."}, status=200)
        
    
class ResetPasswordView(APIView):
    def post(self, request, token, *args, **kwargs):
        email = verify_verification_token(token)
        if not email: 
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        if password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        print(password)

        User = get_user_model()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User with this email does not exist."}, status=400)
        print(user.email)
        user.set_password(password)
        user.save()
        return Response({"success": "Password reset Sucessfull."}, status=200)
    
    
        
        





class CompanyRegistrationView(APIView):
    def post(self, request):
        serializer = CompanyRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Company registration submitted successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


@api_view(['GET'])
def get_company_registrations(request):
    companies = Company.objects.all()  # Fetch all companies from the database
    serializer = CompanyRegistrationSerializer(companies, many=True)  # Serialize the data
    return Response(serializer.data)  # Send the data as a response

# Function to generate username and password
def generate_credentials(company_name):
    random_digits = get_random_string(length=4, allowed_chars='0123456789')
    username = ''.join(e for e in company_name if e.isalnum())[:8] + random_digits
    password = get_random_string(length=12)
    return username.lower(), password

from django.contrib.auth.hashers import make_password  # Import for password hashing


#function to send comany user/password
@api_view(['POST'])
def approve_company(request, pk):
    try:
        company = Company.objects.get(pk=pk)  # Fetch the company using the primary key
        if company.is_approved:
            return Response({'message': 'Company is already approved!'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate username and password
        username, password = generate_credentials(company.company_name)

        # Save the credentials and mark the company as approved
        company.is_approved = True
        company.is_rejected = False
        #company.username = username
        #company.password = make_password(password)  # Save hashed password
        company.save()
        User = get_user_model()
        user = User.objects.create_user(username=username, email=company.company_email )  #f"{username}@yopmail.com")
        user.set_password(password)
        user.is_verified = True
        user.company = company
        user.save()
        company.customuser = user
        company.save()
        

        # Check if the group "admin" exists
        group, created = Group.objects.get_or_create(name='Admin')

        # Add the user to the group
        user.groups.add(group)
        user.save()


        # Send email to the company with credentials
        send_mail(
            subject="Your Company Login Credentials",
            message=f"""
            Dear {company.company_name},

            Your company has been approved. Below are your login credentials:

            Username: {username}
            Password: {password}

            Please log in and change your password immediately.

            Regards,
            Admin Team
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[company.company_email],
        )

        return Response({'message': 'Company approved successfully!', 'username': username}, status=status.HTTP_200_OK)

    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def reject_company(request, pk):
    try:
        company = Company.objects.get(pk=pk)
        if company.is_rejected:
            return Response({'message': 'Company is  rejected!'}, status=status.HTTP_400_BAD_REQUEST)

        # Mark as rejected
        company.is_approved = False
        company.is_rejected = True
        company.save()

        # Send rejection email
        send_mail(
            subject="Company Registration Rejected",
            message=f"""
            Dear {company.company_name},

            We regret to inform you that your company registration has been rejected. If you have any questions, feel free to contact us.

            Regards,
            Admin Team
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[company.company_email],
        )

        return Response({'message': 'Company rejected successfully!'}, status=status.HTTP_200_OK)

    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)


# @api_view(['GET'])
# def get_company_details(request, pk):
#     try:
#         # Fetch the company details using the primary key (id)
#         company = Company.objects.get(id=pk)
#         serializer = CompanyRegistrationSerializer(company)  # Serialize the company object
#         return Response(serializer.data, status=status.HTTP_200_OK)  # Return serialized data
#     except Company.DoesNotExist:
#         return Response({'error': 'Company not found'}, status=404)  # Handle company not found
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.http import JsonResponse
from .models import Company  

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_details(request, pk):
    try:
        company = Company.objects.get(id=pk)  # Fetch company by ID
        return JsonResponse({
            'company_name': company.company_name,
            'company_email': company.company_email,
            'location': company.location,
        }, status=200)
    except Company.DoesNotExist:
        return JsonResponse({'error': 'Company not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class ServiceList(APIView):
    def get(self, request):
        # Query all services from the database
        services = Service.objects.all()
        # Serialize the data
        serializer = ServiceSerializer(services, many=True)
        # Return serialized data as a response
        return Response(serializer.data)


#Userprofile 
from rest_framework.permissions import IsAuthenticated

CustomUser = get_user_model()

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def get_user_profile(request):
    user = request.user

    # GET Request: Return the user's profile data
    if request.method == 'GET':
        return Response({
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,  # Ensure phone_number is included
            "address": user.profile.address if hasattr(user, "profile") else "",
        })

    # PUT Request: Update the user's profile data
    elif request.method == 'PUT':
        data = request.data
        user.first_name = data.get("first_name", user.first_name)
        user.last_name = data.get("last_name", user.last_name)
        user.phone_number = data.get("phone_number", user.phone_number)
        if hasattr(user, "profile"):
            user.profile.address = data.get("address", user.profile.address)
            user.profile.save()
        user.save()

        return Response({"message": "Profile updated successfully!"})
        
    #client profile password change
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def change_password(request):
    user = request.user
    data = request.data
    print(f"Request Data: {request.data}")
    print(f"User: {request.user}")

    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not user.check_password(current_password):
        return Response({"error": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

    if new_password:
        user.set_password(new_password)
        user.save()
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

    return Response({"error": "New password is required."}, status=status.HTTP_400_BAD_REQUEST)



#fetching product
from .models import Product
from .serializers import ProductSerializer
@api_view(['GET'])
def get_all_products(request):
    try:
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_products_by_category(request, category):
    products = Product.objects.filter(category=category, is_available=True)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_company_products(request):
    user = request.user
    products = Product.objects.filter(company=user)
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

#update admindashboard user count and company count
# In your Django backend (e.g., in views.py or a dedicated API view)

from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Company

CustomUser = get_user_model()

@api_view(['GET'])
def dashboard_stats(request):
    total_users = CustomUser.objects.count()  # Count all users
    total_approved_companies = Company.objects.filter(is_approved=True).count()  # Count only approved companies

    return Response({
        "total_users": total_users,
        "total_approved_companies": total_approved_companies,
    })

# #post Product from from company 
# class CreateProduct(APIView):
#     permission_classes = [AllowAny]
#     def post(self, request):
#         user = request.user
#         data = request.data
#         try:
#             # Assign company dynamically
#             company = user.company
#             category = "Renting" if "Construction" in company.company_type else "Selling"

#             # Create a new product
#             product = Product.objects.create(
#                 title=data['title'],
#                 description=data['description'],
#                 price=data['price'],
#                 per_day_rent=data['per_day_rent'],
#                 image=data.get('image'),
#                 discount_percentage=data['discount_percentage'],
#                 category=category,
#                 company=company,
#                 is_available=data['is_available'],
#             )
#             serializer = ProductSerializer(product)
#             return Response(serializer.data, status=201)
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Product
from django.shortcuts import get_object_or_404
class Test(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = request.query_params.get('company_id')
        if not company_id:
            return Response({"error": "Company ID is required."}, status=400)

        try:
            company_id = int(company_id)  # Ensure it's an integer
            products = Product.objects.filter(company_id=company_id)
            # Serialize the data (you may need a serializer like ProductSerializer)
            data = [{
                'id': product.id,
                'title': product.title,
                'description': product.description,
                'price': str(product.price),  # Convert Decimal to string for JSON
                'category': product.category,
                'perDayRent': str(product.per_day_rent) if product.per_day_rent else None,
                'discountPercentage': str(product.discount_percentage) if product.discount_percentage else None,
                'company': product.company_id,
                'isAvailable': product.is_available,
                'createdAt': product.created_at.isoformat(),
            } for product in products]
            return Response(data, status=200)
        except ValueError:
            return Response({"error": "Invalid company ID format."}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    def post(self, request):
        user = request.user

        # 1) Check if user has a company
        company = getattr(user, "company", None)
        if company is None:
            return Response({"error": "This user has no associated company."}, status=400)

        # 2) Read category from request instead of forcing it
        data = request.data
        category = data.get("category", "").lower()  # Ensure lowercase consistency

        # 3) Validate category
        if category not in ["selling", "renting"]:
            return Response({"error": "Invalid category. Must be 'Selling' or 'Renting'."}, status=400)

        # 4) Read the uploaded file (if any)
        image_file = request.FILES.get("image")

        # 5) Convert 'discountPercentage' to Decimal (handle empty case)
        discount_value = Decimal(data.get("discountPercentage", "0"))  # Default to 0

        # 6) Convert 'isAvailable' string to boolean
        is_available = data.get("isAvailable", "false").lower() == "true"

        # 7) Handle per_day_rent properly
        per_day_rent = None
        if category == "renting":
            try:
                per_day_rent = Decimal(data.get("perDayRent", "0"))  # Default to 0 if missing
            except:
                return Response({"error": "Invalid perDayRent value."}, status=400)

        # 8) Create the new product
        product = Product.objects.create(
            title=data["title"],
            description=data["description"],
            price=Decimal(data["price"]),
            category=category,
            per_day_rent=per_day_rent,  # Allow NULL for "Selling"
            discount_percentage=discount_value,
            image=image_file,  # Handle file
            company=company,
            is_available=is_available,
        )

        return Response({"message": "Product created successfully", "id": product.id}, status=201)

    def put(self, request, pk):
        # Handle updating an existing product (similar logic to POST, but update instead of create)
        product = get_object_or_404(Product, pk=pk)
        if product.company_id != request.user.company_id:
            return Response({"error": "You can only edit products belonging to your company."}, status=403)

        data = request.data
        category = data.get("category", "").lower()

        if category not in ["selling", "renting"]:
            return Response({"error": "Invalid category. Must be 'Selling' or 'Renting'."}, status=400)

        image_file = request.FILES.get("image")

        discount_value = Decimal(data.get("discountPercentage", "0"))
        is_available = data.get("isAvailable", "false").lower() == "true"

        per_day_rent = None
        if category == "renting":
            try:
                per_day_rent = Decimal(data.get("perDayRent", "0"))
            except:
                return Response({"error": "Invalid perDayRent value."}, status=400)

        product.title = data["title"]
        product.description = data["description"]
        product.price = Decimal(data["price"])
        product.category = category
        product.per_day_rent = per_day_rent
        product.discount_percentage = discount_value
        product.is_available = is_available

        if image_file:
            product.image = image_file

        product.save()
        return Response({"message": "Product updated successfully"}, status=200)

    def delete(self, request, pk):
        product = get_object_or_404(Product, pk=pk)
        if product.company_id != request.user.company_id:
            return Response({"error": "You can only delete products belonging to your company."}, status=403)

        product.delete()
        return Response({"message": "Product deleted successfully"}, status=204)
            
# ########
# ##RentVerification view
# #########        
# # views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.mail import send_mail
from django.conf import settings
from .models import RentVerification
from .serializers import RentVerificationSerializer

class RentVerificationCreateView(generics.CreateAPIView):
    queryset = RentVerification.objects.all()
    serializer_class = RentVerificationSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        # Prepare the data including multiple images
        data = {
            'full_name': request.data.get('full_name'),
            'email': request.data.get('email'),
            'phone': request.data.get('phone'),
            'address': request.data.get('address'),
            'uploaded_images': request.FILES.getlist('images')
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class RentVerificationAdminView(generics.UpdateAPIView):
    queryset = RentVerification.objects.all()
    serializer_class = RentVerificationSerializer

    def update(self, request, *args, **kwargs):
        verification = self.get_object()
        new_status = request.data.get('status')
        admin_notes = request.data.get('admin_notes', '')
        
        if new_status not in ['verified', 'rejected']:
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        verification.status = new_status
        verification.admin_notes = admin_notes
        verification.save()
        
        # Send email notification
        subject = f'Rent Verification {new_status.title()}'
        message = f"""
        Dear {verification.full_name},
        
        Your rent verification request has been {new_status}.
        
        {f'Admin Notes: {admin_notes}' if admin_notes else ''}
        
        {'You may submit a new verification request if needed.' if new_status == 'rejected' else 'Thank you for using our service.'}
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [verification.email],
            fail_silently=False,
        )
        
        return Response(self.get_serializer(verification).data)

#  ADD THIS NEW VIEW FOR FETCHING PENDING REQUESTS
class RentVerificationListView(generics.ListAPIView):
    serializer_class = RentVerificationSerializer

    def get_queryset(self):
        status_filter = self.request.query_params.get("status", None)
        if status_filter:
            return RentVerification.objects.filter(status=status_filter)
        return RentVerification.objects.all()

class RentVerificationUserUpdateView(generics.UpdateAPIView):
    queryset = RentVerification.objects.all()
    serializer_class = RentVerificationSerializer
    parser_classes = (MultiPartParser, FormParser)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        uploaded_images = request.FILES.getlist('images')
        
        # Construct data manually to avoid deepcopy errors
        data = {
            "address": request.data.get("address", instance.address),
            "uploaded_images": uploaded_images
        }
        
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Ensures only authenticated users can access this
def user_verification_status(request):
    """
    Fetches the verification status of the currently logged-in user.
    """
    try:
        verification = RentVerification.objects.get(email=request.user.email)
        serializer = RentVerificationSerializer(verification)
        return Response(serializer.data)
    except RentVerification.DoesNotExist:
        return Response({"status": "not_found"}, status=404)


####################################
#Django Views for Cart and Wishlist
####################################
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, Wishlist, Product
from django.contrib.auth import get_user_model

User = get_user_model()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    data = [{'image':item.product.image.url, 'company_name': item.product.company.company_name, 'category':item.product.category, 'product_id': item.product.id, 'name': item.product.title, 'price': str(item.product.price), 'quantity': item.quantity, 'company': item.product.company.id } for item in cart_items]
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    user = request.user
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)

    product = get_object_or_404(Product, id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=user, product=product, defaults={'quantity': quantity})
    if not created:
        cart_item.quantity += quantity
        cart_item.save()

    return Response({'message': 'Item added to cart'}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, product_id):
    user = request.user
    cart_item = get_object_or_404(Cart, user=user, product_id=product_id)
    cart_item.delete()
    return Response({'message': 'Item removed from cart'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wishlist(request):
    user = request.user
    wishlist_items = Wishlist.objects.filter(user=user)
    data = [{'product_id': item.product.id, 'name': item.product.title, 'price': str(item.product.price)} for item in wishlist_items]
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_to_wishlist(request):
    user = request.user
    product_id = request.data.get('product_id')

    product = get_object_or_404(Product, id=product_id)
    Wishlist.objects.get_or_create(user=user, product=product)
    return Response({'message': 'Item added to wishlist'}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_wishlist(request, product_id):
    user = request.user
    wishlist_item = get_object_or_404(Wishlist, user=user, product_id=product_id)
    wishlist_item.delete()
    return Response({'message': 'Item removed from wishlist'}, status=status.HTTP_204_NO_CONTENT)


##payment##
'''''''''''''''''

class TransactionCreateAPIView(APIView):

    def post(self, request):
        data = request.data
        
        # Get payer and payee IDs
        payer_id = data.get('payer')
        payee_id = data.get('payee')
        amount = data.get('amount')
        description = data.get('description', '')  # Optional description

        # Validate if payer and payee are valid users
        try:
            payer = CustomUser.objects.get(id=payer_id)
        except CustomUser.DoesNotExist:
            raise ValidationError("Payer does not exist.")

        try:
            payee = CustomUser.objects.get(id=payee_id)
        except CustomUser.DoesNotExist:
            raise ValidationError("Payee does not exist.")

        # Create the transaction
        transaction = Transaction.objects.create(
            payer=payer,
            payee=payee,
            amount=amount,
            description=description
        )

        # Serialize and return the transaction data
        serializer = TransactionSerializer(transaction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

        
class TransactionAPIView(APIView):
    def get(self, request):
        transactions = Transaction.objects.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    def delete(self, request, transaction_id):
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            transaction.delete()
            return Response({"message": "Transaction deleted successfully"}, 
                          status=status.HTTP_204_NO_CONTENT)
        except Transaction.DoesNotExist:
            return Response({"error": "Transaction not found"}, 
                          status=status.HTTP_404_NOT_FOUND)    
'''''''''''''''''
# import os
# import json
# import requests
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from dotenv import load_dotenv

# # Load API keys from .env file
# load_dotenv()

# KHALTI_SECRET_KEY = os.getenv("KHALTI_SECRET_KEY", "test_secret_key_b6f287aab3874adf880ba3ef82f4471c")

# @csrf_exempt
# def verify_khalti_payment(request):
#     if request.method == "POST":
#         try:
#             data = json.loads(request.body)
#             print("Received data:", data)  # Debug log
#             token = data.get("token")
#             amount = data.get("amount")  # Correct key

#             if not token or not amount:
#                 print("Missing token or amount:", {"token": token, "amount": amount})  # Debug log
#                 return JsonResponse({"status": "failed", "message": "Missing token or amount"}, status=400)

#             # Use test mode URL for Khalti
#             url = "https://a.khalti.com/api/v2/payment/verify/"  # Test mode URL
#             headers = {"Authorization": f"Key {KHALTI_SECRET_KEY}"}
#             payload = {"token": token, "amount": amount}

#             print("Sending to Khalti:", payload)  # Debug log
#             response = requests.post(url, json=payload, headers=headers)
#             response_data = response.json()
#             print("Khalti Response:", response_data)  # Debug log

#             if response.status_code == 200:
#                 return JsonResponse({"status": "success", "message": "Payment Verified!", "data": response_data})
#             else:
#                 return JsonResponse({"status": "failed", "message": "Payment Verification Failed!", "data": response_data}, status=400)

#         except json.JSONDecodeError as e:
#             print("JSON Decode Error:", str(e))  # Debug log
#             return JsonResponse({"status": "failed", "message": "Invalid JSON data"}, status=400)

#     return JsonResponse({"status": "failed", "message": "Invalid request method"}, status=405)

# import stripe
# from django.conf import settings
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.views.decorators.http import require_POST
# import json

# stripe.api_key = settings.STRIPE_SECRET_KEY

# @csrf_exempt
# @require_POST
# def create_payment_intent(request):
#     try:
#         data = json.loads(request.body)
#         amount = data.get("amount")  # Amount in cents

#         if not amount or not isinstance(amount, int):
#             return JsonResponse({"error": "Invalid amount provided"}, status=400)

#         # Create a PaymentIntent with the order amount and currency
#         intent = stripe.PaymentIntent.create(
#             amount=amount,  # Amount in cents (e.g., Rs. 1000 = 100000 cents)
#             currency="npr",  # Nepalese Rupees
#             payment_method_types=["card"],
#         )

#         return JsonResponse({
#             "client_secret": intent["client_secret"]
#         })
#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)
# backend/views.py
import stripe
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Company, Order, OrderItem, PaymentDistribution
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY  # Your secret key: sk_test_51QnOg8HFXrh998KlLdTxh4bVatiAoAVCKbtUU5jSUzUcULjFznLuI7sRivfgc38kbsG2JQ5UqMArdbHZSJbwBFXH00AviwVSFp
class CreatePaymentIntentView(APIView):
    def post(self, request):
        try:
            amount = request.data.get("amount")  # In cents
            booking_id = request.data.get("booking_id")
            company_ids = request.data.get("company_id", [])  # List of company IDs for distribution

            if not amount or not booking_id:
                return Response({"error": "Amount and booking_id are required"}, status=status.HTTP_400_BAD_REQUEST)

            # Create Payment Intent (without transfers for now)
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="inr",  # Changed to INR since the frontend shows Rs.
                metadata={"booking_id": booking_id},
                automatic_payment_methods={"enabled": True},
            )

            # For now, we won't distribute to companies since we're using a default account
            # All payments will go to the platform's Stripe account (DEFAULT_STRIPE_ACCOUNT_ID)
            # You can log the company_ids and amounts for manual distribution later if needed

            return Response({"client_secret": payment_intent.client_secret}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# core/views.py
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem, Company, CustomUser
from .serializers import OrderSerializer


class OrderCreateView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            order_type = request.data.get("order_type")
            total_amount = request.data.get("total_amount")
            buying_items = request.data.get("buying_items", [])
            renting_items = request.data.get("renting_items", [])
            billing_details = request.data.get("billing_details")
            renting_details = request.data.get("renting_details")
            booking_id = request.data.get("booking_id")
            transaction_uuid = request.data.get("transaction_uuid")

            if not user_id or not order_type or not total_amount or not booking_id:
                return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

            if not buying_items and not renting_items:
                return Response({"error": "At least one buying or renting item is required"}, status=status.HTTP_400_BAD_REQUEST)

            # all_items = buying_items + renting_items
            # company_ids = set(item["company_id"] for item in all_items if "company_id" in item)

            # if len(company_ids) != 1:
            #     return Response({"error": "All items must belong to the same company for a single order"}, status=status.HTTP_400_BAD_REQUEST)

            # company_id = company_ids.pop()
            # company = Company.objects.get(id=company_id)
            user = CustomUser.objects.get(id=user_id)

            order = Order.objects.create(
                user=user,
                # company=company,
                order_type=order_type,
                total_amount=total_amount,
                billing_details=billing_details,
                renting_details=renting_details,
                booking_id=booking_id,
                buying_status=None if order_type == "renting" else "pending",
                renting_status=None if order_type == "buying" else "pending",
            )
            # order_status_updated.send(
            # sender=Order,
            # instance=order,
            # created=False,
            # raw=False,
            # using='default',
            # update_fields=None,
            # user=request.user  # <--- extra data here
            # )
            for item in buying_items:
                OrderItem.objects.create(
                    order=order,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"],
                    item_type="buying",
                )

            for item in renting_items:
                OrderItem.objects.create(
                    order=order,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"],
                    item_type="renting",
                )

            serializer = OrderSerializer(order)
            return Response({
                "invoices": {
                    "order_id": order.id,
                    "booking_id": booking_id,
                    "transaction_uuid": transaction_uuid,
                    "order_type": order_type,
                },
                "order": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError as e:
            return Response({"error": f"Database error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateOrderPaymentView(APIView):
    def post(self, request):
        try:
            user_id = request.data.get("user_id")
            booking_id = request.data.get("booking_id")
            payment_data = request.data.get("payment_data")
            order_type = request.data.get("order_type")
            invoices = request.data.get("invoices", {})

            if not booking_id or not payment_data:
                return Response(
                    {"error": "Missing bookingId or payment_data"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not user_id:
                return Response(
                    {"error": "Missing user_id"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not order_type:
                return Response(
                    {"error": "Missing order_type"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order = Order.objects.get(booking_id=booking_id, user_id=user_id)

            # Set statuses based on order_type
            if order_type == "buying":
                order.buying_status = "Paid"
            elif order_type == "renting":
                order.renting_status = "Booked"
            else:  # mixed
                order.buying_status = "Paid"
                order.renting_status = "Booked"

            order.payment_data = payment_data
            order.save()

            for company_id, amount in invoices.get("company_amounts", {}).items():
                try:
                    company = Company.objects.get(id=company_id)
                except Company.DoesNotExist:
                    return Response(
                        {"error": f"Company with ID {company_id} not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

                try:
                    PaymentDistribution.objects.create(
                        order=order,
                        company=company,
                        amount=amount,
                        payment_status="pending",
                        booking_id=booking_id,
                    )
                except Exception as e:
                    return Response(
                        {"error": f"Failed to create PaymentDistribution: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            return Response({"message": "Order updated successfully"}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Order.MultipleObjectsReturned:
            return Response(
                {"error": f"Multiple orders found for booking_id {booking_id} and user_id {user_id}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# core/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order
from .serializers import OrderSerializer
from rest_framework.permissions import IsAuthenticated

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request):
        try:
            # Fetch orders for the authenticated user
            user = request.user
            orders = Order.objects.filter(user=user).order_by('-created_at')  # Order by most recent first
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

from django.db.models import Q 
class CompanyOrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            # Get filter parameter from query string
            filter_status = request.query_params.get('filter_status', None)

            # Base query: fetch orders with items belonging to the user's company
            orders = Order.objects.filter(
                items__product__company=user.company
            ).distinct().order_by('-created_at')

            # Define status categories
            buying_statuses = ["Paid", "Processing", "Delivered", "Cancelled"]
            renting_statuses = ["Booked", "Picked Up", "Returned", "Cancelled"]

            # Apply filter based on filter_status
            if filter_status:
                if filter_status.lower() == "all_except_delivered_returned":
                    # Exclude orders with buying_status: "Delivered" and renting_status: "Returned"
                    orders = orders.filter(
                        ~Q(order_type__in=['buying', 'mixed'], buying_status="Delivered") &
                        ~Q(order_type__in=['renting', 'mixed'], renting_status="Returned")
                    )
                elif filter_status in buying_statuses:
                    orders = orders.filter(
                        Q(order_type__in=['buying', 'mixed']) & Q(buying_status=filter_status)
                    )
                elif filter_status in renting_statuses:
                    orders = orders.filter(
                        Q(order_type__in=['renting', 'mixed']) & Q(renting_status=filter_status)
                    )

            # Pass the company_id to the serializer context
            serializer = OrderSerializer(
                orders,
                many=True,
                context={'company_id': str(user.company.id)}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Order, OrderItem, Company, CustomUser, PaymentDistribution
from .serializers import OrderSerializer
from rest_framework.permissions import IsAuthenticated
# from .signals import order_status_updated
class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)

            new_buying_status = request.data.get("buying_status")
            new_renting_status = request.data.get("renting_status")

            # Validate and update buying_status for buying or mixed orders
            if new_buying_status and order.order_type in ["buying", "mixed"]:
                valid_buying_statuses = ["Paid", "Processing", "Delivered", "Cancelled"]
                if new_buying_status not in valid_buying_statuses:
                    return Response(
                        {"error": f"Invalid buying status. Must be one of {valid_buying_statuses}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                order.buying_status = new_buying_status

            # Validate and update renting_status for renting or mixed orders
            if new_renting_status and order.order_type in ["renting", "mixed"]:
                valid_renting_statuses = ["Booked", "Picked Up", "Returned", "Cancelled"]
                if new_renting_status not in valid_renting_statuses:
                    return Response(
                        {"error": f"Invalid renting status. Must be one of {valid_renting_statuses}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                order.renting_status = new_renting_status

            # Ensure at least one status is being updated
            if not new_buying_status and not new_renting_status:
                return Response(
                    {"error": "At least one of buying_status or renting_status must be provided"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            order.save()
            # order_status_updated.send(
            # sender=Order,
            # instance=order,
            # created=True,
            # raw=False,
            # using='default',
            # update_fields=None,
            # user=request.user  # <--- extra data here
            # )
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

##############
##companyinfo##

# ersathi/views.py
# ersathi/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action

from .models import CompanyInfo, Company, ProjectInfo, TeamMemberInfo
from .serializers import CompanyInfoSerializer



@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def company_info_detail(request, company_id):
    """
    Handle GET and PUT requests for company information.
    GET: Retrieve company info (phone_number, logo, about_us editable).
    PUT: Update only phone_number, logo, and about_us.
    """
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)

        if request.method == 'GET':
            serializer = CompanyInfoSerializer(company_info)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'PUT':
            # Prepare data for update, only allowing specific fields
            mutable_data = {
                'phone_number': request.data.get('phone_number', company_info.phone_number),
                'logo': request.data.get('logo', company_info.logo),
                'about_us': request.data.get('about_us', company_info.about_us),
            }
            
            serializer = CompanyInfoSerializer(company_info, data=mutable_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def company_info(request):
    company_id = request.data.get('company')
    if not company_id:
        return Response({"error": "Company ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Validate that this user really owns or is associated with that Company
        # (Check if the ID is valid and do whatever validation you need, if any)
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        return Response({"error": "Invalid company ID or unauthorized"}, status=status.HTTP_400_BAD_REQUEST)

    serializer = CompanyInfoSerializer(data=request.data)
    if serializer.is_valid():
        # Save with the matched Company and the current user
        serializer.save(company=company, customuser=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



from .serializers import ProjectInfoSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def project_list_create(request, company_id):
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)

        if request.method == 'GET':
            projects = ProjectInfo.objects.filter(company=company_info)
            serializer = ProjectInfoSerializer(projects, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            serializer = ProjectInfoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(company=company_info)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_project(request, company_id, project_id):
    """
    Update an existing project for a specific company ID and project ID.
    """
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)
        project = get_object_or_404(ProjectInfo, id=project_id, company=company_info)
        
        serializer = ProjectInfoSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_project(request, company_id, project_id):
    print(f"Attempting to delete project {project_id} for company {company_id}")
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)
        project = get_object_or_404(ProjectInfo, id=project_id, company=company_info)
        project.delete()
        return Response({"message": "Project deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        print(f"Error deleting project: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    




#teaminfo

from .serializers import TeamMemberInfoSerializer

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def team_member_list_create(request, company_id):
    """
    List all team members for a company or create a new team member.
    """
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)

        if request.method == 'GET':
            team_members = TeamMemberInfo.objects.filter(company=company_info)
            serializer = TeamMemberInfoSerializer(team_members, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            serializer = TeamMemberInfoSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(company=company_info)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_team_member(request, company_id, member_id):
    """
    Update an existing team member for a specific company ID and member ID.
    """
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)
        team_member = get_object_or_404(TeamMemberInfo, id=member_id, company=company_info)
        
        serializer = TeamMemberInfoSerializer(team_member, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_team_member(request, company_id, member_id):
    """
    Delete a team member for a specific company ID and member ID.
    """
    try:
        company_info = get_object_or_404(CompanyInfo, company_id=company_id, customuser=request.user)
        team_member = get_object_or_404(TeamMemberInfo, id=member_id, company=company_info)
        team_member.delete()
        return Response({"message": "Team member deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


##client side view
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny  # Changed to AllowAny for public access
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Company, CompanyInfo, ProjectInfo, TeamMemberInfo
from .serializers import CompanyInfoSerializer, ProjectInfoSerializer, TeamMemberInfoSerializer
import logging

logger = logging.getLogger(__name__)

# View for fetching company info
@api_view(['GET'])
@permission_classes([AllowAny])  # Public access
def get_company_info(request, company_id):
    """
    Retrieve company information for client viewing based on Company model's ID.
    """
    try:
        logger.info(f"Fetching company info for company_id={company_id}")
        # Step 1: Fetch the Company record
        company = get_object_or_404(Company, id=company_id)
        logger.info(f"Found company: {company}")
        # Step 2: Fetch the CompanyInfo record linked to this Company
        company_info = get_object_or_404(CompanyInfo, company=company)  # Removed customuser check
        logger.info(f"Found company info: {company_info}")
        serializer = CompanyInfoSerializer(company_info)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in get_company_info: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# View for fetching projects
@api_view(['GET'])
@permission_classes([AllowAny])  # Public access
def get_company_projects(request, company_id):
    """
    Retrieve projects for a specific company for client viewing based on Company model's ID.
    """
    try:
        logger.info(f"Fetching projects for company_id={company_id}")
        # Step 1: Fetch the Company record
        company = get_object_or_404(Company, id=company_id)
        logger.info(f"Found company: {company}")
        # Step 2: Fetch the CompanyInfo record linked to this Company
        company_info = get_object_or_404(CompanyInfo, company=company)  # Removed customuser check
        logger.info(f"Found company info: {company_info}")
        # Step 3: Fetch ProjectInfo records linked to this Company
        projects = ProjectInfo.objects.filter(company=company_info)
        serializer = ProjectInfoSerializer(projects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in get_company_projects: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

# View for fetching team members
@api_view(['GET'])
@permission_classes([AllowAny])  # Public access
def get_company_team_members(request, company_id):
    """
    Retrieve team members for a specific company for client viewing based on Company model's ID.
    """
    try:
        logger.info(f"Fetching team members for company_id={company_id}")
        # Step 1: Fetch the Company record
        company = get_object_or_404(Company, id=company_id)
        logger.info(f"Found company: {company}")
        # Step 2: Fetch the CompanyInfo record linked to this Company
        company_info = get_object_or_404(CompanyInfo, company=company)  # Removed customuser check
        logger.info(f"Found company info: {company_info}")
        # Step 3: Fetch TeamMemberInfo records linked to this Company
        team_members = TeamMemberInfo.objects.filter(company=company_info)
        serializer = TeamMemberInfoSerializer(team_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in get_company_team_members: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    




from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Company, CompanyServices

@csrf_exempt
def get_company_services_by_id(request, company_id):
    """Returns category and sub_service for a given company_id without authentication"""
    try:
        # Fetch the company by company_id
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            return JsonResponse({"error": "Company not found"}, status=404)

        # Fetch services for the company
        services = CompanyServices.objects.filter(company=company).select_related('service__category')
        data = [
            {
                "category": service.service.category.name,
                "sub_service": service.service.name,
            }
            for service in services
        ]
        return JsonResponse(data, safe=False)
    except Exception as e:
        logger.error(f"Error in get_company_services_by_id: {str(e)}")
        return JsonResponse({"error": str(e)}, status=400)
    
#4/22
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from .models import Inquiry, Appointment, Company, EngineeringConsultingData, BuildingConstructionData, PostConstructionMaintenanceData, SafetyTrainingData
# from .serializers import InquirySerializer
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from datetime import datetime, timedelta
# from django.core.mail import send_mail

# class SubmitInquiryView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, company_id):
#         try:
#             user = request.user
#             company = get_object_or_404(Company, id=company_id)
            
#             # Handle num_floors safely
#             num_floors_value = request.POST.get('num_floors', None)
#             num_floors = None
#             if num_floors_value and num_floors_value.strip() and num_floors_value != 'null':
#                 try:
#                     num_floors = int(num_floors_value)
#                     if num_floors < 1:  # Ensure positive integer
#                         num_floors = None
#                 except ValueError:
#                     num_floors = None

#             # Create Inquiry
#             inquiry_data = {
#                 'user': user,
#                 'company': company,
#                 'full_name': request.POST.get('full_name', ''),
#                 'location': request.POST.get('location', ''),
#                 'email': request.POST.get('email', ''),
#                 'phone_number': request.POST.get('phone_number', ''),
#                 'category': request.POST.get('category', ''),
#                 'sub_service': request.POST.get('sub_service', ''),
#                 'status': 'Pending',
#             }
#             inquiry = Inquiry(**inquiry_data)
#             inquiry.save()

#             # Create service-specific data based on category
#             if inquiry.category == "Engineering Consulting":
#                 service_data = EngineeringConsultingData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()
#             elif inquiry.category == "Building Construction Services":
#                 service_data = BuildingConstructionData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()
#             elif inquiry.category == "Post-Construction Maintenance":
#                 service_data = PostConstructionMaintenanceData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()
#             elif inquiry.category == "Safety and Training Services":
#                 service_data = SafetyTrainingData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()

#             # Schedule appointment only for Engineering Consulting and Building Construction Services
#             if inquiry.category in ["Engineering Consulting", "Building Construction Services"]:
#                 # Define time constraints
#                 start_hour = 10  # 10:00 AM
#                 end_hour = 17   # 5:00 PM
#                 slot_duration = 21  # Duration in minutes per appointment
#                 max_slots_per_day = ((end_hour - start_hour) * 60) // slot_duration  # Total slots between 10 AM and 5 PM

#                 # Start checking from tomorrow
#                 current_date = timezone.now().date() + timedelta(days=1)
#                 while True:
#                     daily_appointments = Appointment.objects.filter(
#                         company=company,
#                         appointment_date__date=current_date
#                     ).count()

#                     if daily_appointments < max_slots_per_day:
#                         # Calculate the appointment time
#                         start_time = datetime.combine(current_date, datetime.strptime(f'{start_hour}:00', '%H:%M').time())
#                         minutes_offset = daily_appointments * slot_duration
#                         appointment_time = start_time + timedelta(minutes=minutes_offset)

#                         # Ensure the appointment doesn't exceed 5:00 PM
#                         end_time = appointment_time + timedelta(minutes=slot_duration)
#                         if end_time.time() <= datetime.strptime('17:00', '%H:%M').time():
#                             appointment = Appointment(
#                                 inquiry=inquiry,
#                                 company=company,
#                                 appointment_date=appointment_time
#                             )
#                             appointment.save()

#                             inquiry.status = 'Scheduled'
#                             inquiry.save()

#                             # Send email
#                             send_mail(
#                                 'Appointment Confirmation',
#                                 f'Your appointment is scheduled for {appointment_time.strftime("%Y-%m-%d %I:%M %p")} with {company.company_name}',
#                                 'fybproject6@gmail.com',
#                                 [inquiry.email],
#                                 fail_silently=True,
#                             )

#                             serializer = InquirySerializer(inquiry)
#                             return Response({
#                                 'message': 'Inquiry submitted successfully',
#                                 'appointment': appointment_time.strftime('%Y-%m-%d %I:%M %p'),
#                                 'data': serializer.data
#                             }, status=status.HTTP_201_CREATED)
#                     # If the day is full, move to the next day
#                     current_date += timedelta(days=1)
#             else:
#                 # For other categories, just return success without scheduling an appointment
#                 serializer = InquirySerializer(inquiry)
#                 return Response({
#                     'message': 'Inquiry submitted successfully. No appointment required for this service.',
#                     'data': serializer.data
#                 }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def _populate_service_data(self, service_data, request):
#         for field in service_data._meta.fields:
#             field_name = field.name
#             if field_name in request.POST:
#                 setattr(service_data, field_name, request.POST[field_name])
#             elif field_name in request.FILES:
#                 setattr(service_data, field_name, request.FILES[field_name])
#4/22
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework import status
# from .models import Inquiry, Appointment, Company, EngineeringConsultingData, BuildingConstructionData, PostConstructionMaintenanceData, SafetyTrainingData
# from .serializers import InquirySerializer
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from datetime import datetime, timedelta
# import logging

# logger = logging.getLogger(__name__)

# class SubmitInquiryView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, company_id):
#         try:
#             user = request.user
#             company = get_object_or_404(Company, id=company_id)
            
#             # Handle num_floors safely
#             num_floors_value = request.POST.get('num_floors', None)
#             num_floors = None
#             if num_floors_value and num_floors_value.strip() and num_floors_value != 'null':
#                 try:
#                     num_floors = int(num_floors_value)
#                     if num_floors < 1:  # Ensure positive integer
#                         num_floors = None
#                 except ValueError:
#                     num_floors = None

#             # Create Inquiry
#             inquiry_data = {
#                 'user': user,
#                 'company': company,
#                 'full_name': request.POST.get('full_name', ''),
#                 'location': request.POST.get('location', ''),
#                 'email': request.POST.get('email', ''),
#                 'phone_number': request.POST.get('phone_number', ''),
#                 'category': request.POST.get('category', ''),
#                 'sub_service': request.POST.get('sub_service', ''),
#                 'status': 'Pending',
#             }
#             inquiry = Inquiry(**inquiry_data)
#             inquiry.save()

#             # Create service-specific data based on category
#             if inquiry.category == "Engineering Consulting":
#                 service_data = EngineeringConsultingData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()
#             elif inquiry.category == "Building Construction Services":
#                 service_data = BuildingConstructionData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()
#             elif inquiry.category == "Post-Construction Maintenance":
#                 service_data = PostConstructionMaintenanceData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()
#             elif inquiry.category == "Safety and Training Services":
#                 service_data = SafetyTrainingData(inquiry=inquiry)
#                 self._populate_service_data(service_data, request)
#                 service_data.save()

#             # Schedule appointment only for Engineering Consulting and Building Construction Services
#             if inquiry.category in ["Engineering Consulting", "Building Construction Services"]:
#                 # Define time constraints
#                 start_hour = 10  # 10:00 AM
#                 end_hour = 17   # 5:00 PM
#                 slot_duration = 21  # Duration in minutes per appointment
#                 max_slots_per_day = ((end_hour - start_hour) * 60) // slot_duration  # Total slots between 10 AM and 5 PM

#                 # Start checking from tomorrow
#                 current_date = timezone.now().date() + timedelta(days=1)
#                 while True:
#                     daily_appointments = Appointment.objects.filter(
#                         company=company,
#                         appointment_date__date=current_date
#                     ).count()

#                     if daily_appointments < max_slots_per_day:
#                         # Calculate the appointment time
#                         start_time = datetime.datetime.combine(current_date, datetime.strptime(f'{start_hour}:00', '%H:%M').time())
#                         minutes_offset = daily_appointments * slot_duration
#                         appointment_time = start_time + timedelta(minutes=minutes_offset)

#                         # Ensure the appointment doesn't exceed 5:00 PM
#                         end_time = appointment_time + timedelta(minutes=slot_duration)
#                         if end_time.time() <= datetime.strptime('17:00', '%H:%M').time():
#                             appointment = Appointment(
#                                 inquiry=inquiry,
#                                 company=company,
#                                 appointment_date=appointment_time
#                             )
#                             appointment.save()

#                             inquiry.status = 'Scheduled'
#                             inquiry.save()

#                             # Send email
#                             send_mail(
#                                 'Appointment Confirmation',
#                                 f'Your appointment is scheduled for {appointment_time.strftime("%Y-%m-%d %I:%M %p")} with {company.company_name}',
#                                 'fybproject6@gmail.com',
#                                 [inquiry.email],
#                                 fail_silently=True,
#                             )

#                             serializer = InquirySerializer(inquiry)
#                             return Response({
#                                 'message': 'Inquiry submitted successfully',
#                                 'appointment': appointment_time.strftime('%Y-%m-%d %I:%M %p'),
#                                 'data': serializer.data
#                             }, status=status.HTTP_201_CREATED)
#                     # If the day is full, move to the next day
#                     current_date += timedelta(days=1)
#             else:
#                 # For other categories, just return success without scheduling an appointment
#                 serializer = InquirySerializer(inquiry)
#                 return Response({
#                     'message': 'Inquiry submitted successfully. No appointment required for this service.',
#                     'data': serializer.data
#                 }, status=status.HTTP_201_CREATED)

#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def _populate_service_data(self, service_data, request):
#         for field in service_data._meta.fields:
#             field_name = field.name
#             if field_name in request.POST:
#                 setattr(service_data, field_name, request.POST[field_name])
#             elif field_name in request.FILES:
#                 setattr(service_data, field_name, request.FILES[field_name])

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Inquiry, Appointment, Company, EngineeringConsultingData, BuildingConstructionData, PostConstructionMaintenanceData, SafetyTrainingData
from .serializers import InquirySerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SubmitInquiryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        try:
            logger.info(f"Starting inquiry submission for company_id: {company_id}, user: {request.user.id}")
            user = request.user
            company = get_object_or_404(Company, id=company_id)
            logger.info(f"Company found: {company.id} - {company.company_name}")

            # Handle num_floors safely
            num_floors_value = request.POST.get('num_floors', None)
            num_floors = None
            if num_floors_value and num_floors_value.strip() and num_floors_value != 'null':
                try:
                    num_floors = int(num_floors_value)
                    if num_floors < 1:  # Ensure positive integer
                        num_floors = None
                except ValueError:
                    num_floors = None
                    logger.warning(f"Invalid num_floors value: {num_floors_value}")

            # Create Inquiry
            inquiry_data = {
                'user': user,
                'company': company,
                'full_name': request.POST.get('full_name', ''),
                'location': request.POST.get('location', ''),
                'email': request.POST.get('email', ''),
                'phone_number': request.POST.get('phone_number', ''),
                'category': request.POST.get('category', ''),
                'sub_service': request.POST.get('sub_service', ''),
                'status': 'Pending',
            }
            inquiry = Inquiry(**inquiry_data)
            inquiry.save()
            logger.info(f"Inquiry created: {inquiry.id}, category: {inquiry.category}, sub_service: {inquiry.sub_service}")

            # Create service-specific data based on category
            if inquiry.category == "Engineering Consulting":
                service_data = EngineeringConsultingData(inquiry=inquiry)
                self._populate_service_data(service_data, request)
                service_data.save()
                logger.info(f"EngineeringConsultingData created: {service_data.id}")
            elif inquiry.category == "Building Construction Services":
                service_data = BuildingConstructionData(inquiry=inquiry)
                self._populate_service_data(service_data, request)
                service_data.save()
                logger.info(f"BuildingConstructionData created: {service_data.id}")
            elif inquiry.category == "Post-Construction Maintenance":
                service_data = PostConstructionMaintenanceData(inquiry=inquiry)
                self._populate_service_data(service_data, request)
                service_data.save()
                logger.info(f"PostConstructionMaintenanceData created: {service_data.id}")
            elif inquiry.category == "Safety and Training Services":
                service_data = SafetyTrainingData(inquiry=inquiry)
                self._populate_service_data(service_data, request)
                service_data.save()
                logger.info(f"SafetyTrainingData created: {service_data.id}")

            # Schedule appointment only for Engineering Consulting and Building Construction Services
            appointment_time = None
            if inquiry.category in ["Engineering Consulting", "Building Construction Services"]:
                logger.info("Scheduling appointment...")
                # Define time constraints
                start_hour = 10  # 10:00 AM
                end_hour = 17   # 5:00 PM
                slot_duration = 21  # Duration in minutes per appointment
                max_slots_per_day = ((end_hour - start_hour) * 60) // slot_duration  # Total slots between 10 AM and 5 PM

                # Start checking from tomorrow
                current_date = timezone.now().date() + timedelta(days=1)
                while True:
                    daily_appointments = Appointment.objects.filter(
                        company=company,
                        appointment_date__date=current_date
                    ).count()
                    logger.info(f"Checking date {current_date}: {daily_appointments} appointments found")

                    if daily_appointments < max_slots_per_day:
                        # Calculate the appointment time (ensure timezone awareness)
                        start_time = timezone.make_aware(
                            datetime.datetime.combine(
                                current_date,
                                datetime.datetime.strptime(f'{start_hour}:00', '%H:%M').time()
                            )
                        )
                        minutes_offset = daily_appointments * slot_duration
                        appointment_time = start_time + timedelta(minutes=minutes_offset)

                        # Ensure the appointment doesn't exceed 5:00 PM
                        end_time = appointment_time + timedelta(minutes=slot_duration)
                        end_time_limit = timezone.make_aware(
                            datetime.datetime.combine(
                                current_date,
                                datetime.datetime.strptime('17:00', '%H:%M').time()
                            )
                        )
                        if end_time <= end_time_limit:
                            appointment = Appointment(
                                inquiry=inquiry,
                                company=company,
                                appointment_date=appointment_time
                            )
                            appointment.save()
                            logger.info(f"Appointment created: {appointment.id} at {appointment_time}")

                            inquiry.status = 'Scheduled'
                            inquiry.save()
                            logger.info(f"Inquiry status updated to Scheduled: {inquiry.id}")

                            # Send email
                            try:
                                send_mail(
                                    'Appointment Confirmation',
                                    f'Your appointment is scheduled for {appointment_time.strftime("%Y-%m-%d %I:%M %p")} with {company.company_name}',
                                    'fybproject6@gmail.com',
                                    [inquiry.email],
                                    fail_silently=False,  # Set to False to catch email errors
                                )
                                logger.info(f"Email sent to {inquiry.email}")
                            except Exception as email_error:
                                logger.error(f"Failed to send email: {str(email_error)}")
                                # Continue even if email fails

                            break
                    # If the day is full, move to the next day
                    current_date += timedelta(days=1)

            # Serialize the inquiry for response
            try:
                serializer = InquirySerializer(inquiry, context={'request': request})
                logger.info("Inquiry serialized successfully")
            except Exception as serialize_error:
                logger.error(f"Serialization error: {str(serialize_error)}")
                raise

            # Prepare response
            response_data = {
                'message': 'Inquiry submitted successfully',
                'data': serializer.data
            }
            if appointment_time:
                response_data['appointment'] = appointment_time.strftime('%Y-%m-%d %I:%M %p')
            else:
                response_data['message'] = 'Inquiry submitted successfully. No appointment required for this service.'

            logger.info("Inquiry submission completed successfully")
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Error in SubmitInquiryView: {str(e)}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _populate_service_data(self, service_data, request):
        try:
            for field in service_data._meta.fields:
                field_name = field.name
                if field_name in request.POST:
                    setattr(service_data, field_name, request.POST[field_name])
                elif field_name in request.FILES:
                    setattr(service_data, field_name, request.FILES[field_name])
            logger.info(f"Populated service data for {service_data.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error in _populate_service_data: {str(e)}")
            raise

# ersathi/views.py
# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Inquiry, Appointment, Company
from .serializers import InquirySerializer, AppointmentSerializer
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

class CompanyInquiriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Ensure the user has a related company
            if not hasattr(request.user, 'company'):
                return Response({"error": "Company not associated with this user"}, status=status.HTTP_400_BAD_REQUEST)

            company = request.user.company
            company_id = company.id
            print(f"Company ID from user: {company_id}")

            # Fetch inquiries and prefetch related service-specific data
            inquiries = Inquiry.objects.filter(company_id=company_id).select_related(
                'engineering_data', 'building_data', 'maintenance_data', 'training_data'
            )
            print(f"Inquiries found: {inquiries.count()}")  # Debug log
            if not inquiries.exists():
                return Response([], status=status.HTTP_200_OK)

            serializer = InquirySerializer(inquiries, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in CompanyInquiriesView: {str(e)}")
            return Response({"error": "Failed to load inquiries"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateInquiryStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, inquiry_id):
        try:
            inquiry = get_object_or_404(Inquiry, id=inquiry_id, company=request.user.company)
            new_status = request.data.get('status')
            valid_statuses = [choice[0] for choice in Inquiry._meta.get_field('status').choices]
            
            if new_status not in valid_statuses:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            old_status = inquiry.status
            inquiry.status = new_status
            inquiry.save()

            # Send email only when changing to Scheduled
            if new_status == 'Scheduled':
                if hasattr(inquiry, 'appointment'):
                    appointment = inquiry.appointment
                    send_mail(
                        'Appointment Rescheduled' if old_status == 'Scheduled' else 'Appointment Scheduled',
                        f'Your appointment is now scheduled for {appointment.appointment_date.strftime("%Y-%m-%d %I:%M %p")}',
                        'fybproject6@gmail.com',
                        [inquiry.email],
                        fail_silently=True,
                    )
                else:
                    logger.warning(f"No appointment found for inquiry {inquiry_id}")

            return Response({"message": "Status updated"}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"UpdateInquiryStatusView error: {str(e)}")
            return Response({"error": "Failed to update status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# views.py
#client site
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Inquiry, EngineeringConsultingData, BuildingConstructionData, PostConstructionMaintenanceData, SafetyTrainingData
from .serializers import InquirySerializer  # You'll need to update the serializer
class ClientInquiriesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            print(f"Fetching inquiries for user: {user.id} ({user.username})")
            
            # Get all inquiries for the user
            inquiries = Inquiry.objects.filter(user=user).select_related(
                'engineering_data', 'building_data', 'maintenance_data', 'training_data'
            ).order_by('-created_at')
            
            print(f"Found {inquiries.count()} inquiries")
            for inquiry in inquiries:
                print(f"Inquiry ID: {inquiry.id}")
                print(f"Category: {inquiry.category}")
                print(f"Sub-Service: {inquiry.sub_service}")
                print(f"Status: {inquiry.status}")
                print(f"Created At: {inquiry.created_at}")
                print("------")
            
            serializer = InquirySerializer(inquiries, many=True, context={'request': request})
            return Response(serializer.data, status=200)
        except Exception as e:
            print(f"Error fetching inquiries: {str(e)}")
            return Response({"error": str(e)}, status=500)


class CompanyAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            company_id = getattr(request.user, 'company_id', None)
            if not company_id:
                return Response({"error": "Company not associated with this user"}, status=status.HTTP_400_BAD_REQUEST)

            company = Company.objects.get(id=company_id)
            appointments = Appointment.objects.filter(company=company).select_related('inquiry')
            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Company.DoesNotExist:
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in CompanyAppointmentsView: {str(e)}")
            return Response({"error": "Failed to fetch appointments"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateAppointmentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, company=request.user.company)
            new_status = request.data.get('status')
            valid_statuses = [choice[0] for choice in Appointment._meta.get_field('status').choices]

            if new_status not in valid_statuses:
                return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)

            appointment.status = new_status
            appointment.save()

            # Update the inquiry status based on the appointment status
            inquiry = appointment.inquiry
            if new_status == "No-Show":
                inquiry.status = "Pending"  # Client didn't show up, set inquiry back to Pending
            elif new_status == "Completed":
                inquiry.status = "Completed"  # Consultation done, set inquiry to Completed
            inquiry.save()

            return Response({"message": "Appointment status updated"}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in UpdateAppointmentStatusView: {str(e)}")
            return Response({"error": "Failed to update status"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# class CheckNewInquiriesView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             company = request.user.company
#             if not company:
#                 return Response({"error": "Company not associated with this user"}, status=400)
            
#             last_check = company.last_inquiry_check or timezone.datetime(1970, 1, 1)
#             new_inquiries = Inquiry.objects.filter(company=company, created_at__gt=last_check).exists()
#             return Response({"has_new_inquiries": new_inquiries}, status=200)
#         except Exception as e:
#             logger.error(f"Error in CheckNewInquiriesView: {str(e)}")
#             return Response({"error": str(e)}, status=500)

# class GetLastInquiryCheckView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             company = request.user.company
#             last_check = company.last_inquiry_check or datetime(1970, 1, 1, tzinfo=timezone.utc)
#             return Response({"last_inquiry_check": last_check}, status=200)
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

# class MarkInquiriesCheckedView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         try:
#             company = request.user.company
#             company.last_inquiry_check = timezone.now()
#             company.save()
#             return Response({"status": "success"}, status=200)
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

# class GetLastInquiryCheckView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         try:
#             company = request.user.company
#             last_check = company.last_inquiry_check or datetime(1970, 1, 1, tzinfo=timezone.utc)
#             return Response({"last_inquiry_check": last_check}, status=200)
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)



#appointment

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

class UpdateAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, company=request.user.company)
            new_date = request.data.get('appointment_date')
            new_status = request.data.get('status')
            if new_date:
                appointment.appointment_date = new_date
            if new_status:
                valid_statuses = [choice[0] for choice in Appointment._meta.get_field('status').choices]
                if new_status not in valid_statuses:
                    return Response({"error": "Invalid status"}, status=status.HTTP_400_BAD_REQUEST)
                appointment.status = new_status
            appointment.save()
            return Response({"message": "Appointment updated"}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in UpdateAppointmentView: {str(e)}")
            return Response({"error": "Failed to update appointment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DeleteAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, appointment_id):
        try:
            appointment = get_object_or_404(Appointment, id=appointment_id, company=request.user.company)
            inquiry = appointment.inquiry
            appointment.delete()
            inquiry.status = 'Pending'  # Reset inquiry status
            inquiry.save()
            return Response({"message": "Appointment deleted"}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            logger.error(f"Error in DeleteAppointmentView: {str(e)}")
            return Response({"error": "Failed to delete appointment"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)











from django.core.files import File
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings
from weasyprint import HTML
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Appointment, Inquiry, Company, Service, Agreement, CompanyServices

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_agreement(request, appointment_id):
    try:
        # Fetch the appointment and related objects
        appointment = get_object_or_404(Appointment, id=appointment_id)
        inquiry = appointment.inquiry
        company = appointment.company

        # Get the service from the inquiry
        if hasattr(inquiry, 'service'):
            service = inquiry.service
        else:
            # If Inquiry doesn't have a direct 'service' field, try to get it via sub_service or CompanyServices
            service = Service.objects.filter(name=inquiry.sub_service).first()
            if not service:
                company_service = CompanyServices.objects.filter(company=company, service__name=inquiry.sub_service).first()
                if company_service:
                    service = company_service.service
                else:
                    return Response({'error': 'Service not found for this inquiry'}, status=status.HTTP_400_BAD_REQUEST)

        # Get data from the request
        service_charge = request.data.get('service_charge')
        if not service_charge:
            return Response({'error': 'Service charge is required'}, status=status.HTTP_400_BAD_REQUEST)
        additional_terms = request.data.get('additional_terms', '')
        company_representative_name = request.data.get('company_representative_name')
        if not company_representative_name:
            return Response({'error': 'Company representative name is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare context for the template
        context = {
            'inquiry': inquiry,
            'company': company,
            'service': service,
            'company_representative_name': company_representative_name,
            'service_charge': service_charge,
            'additional_terms': additional_terms,
        }

        # Render the template to HTML
        html_string = render_to_string('agreement_template.html', context)

        # Generate PDF
        pdf_file_path = os.path.join(settings.MEDIA_ROOT, 'agreements', f'agreement_{appointment.id}.pdf')
        HTML(string=html_string).write_pdf(pdf_file_path)

        # Save the agreement in the database
        with open(pdf_file_path, 'rb') as pdf_file:
            agreement = Agreement.objects.create(
                inquiry=inquiry,
                company=company,
                user=inquiry.user,  # Assuming Inquiry has a 'client' field
                service=service,
                company_representative_name=company_representative_name,
                service_charge=service_charge,
                document=File(pdf_file, name=os.path.basename(pdf_file_path)),
                status='Sent',
            )

        # Send email to the client
        email = EmailMessage(
            subject=f'Construction Agreement for {service.name}',
            body='Please find the attached agreement for your service.',
            from_email=settings.EMAIL_HOST_USER,
            to=[inquiry.email],
        )
        email.attach_file(pdf_file_path)
        email.send()

        return Response({'message': 'Agreement generated and sent successfully'}, status=status.HTTP_200_OK)

    except Exception as e:
        print(f"Error in generate_agreement: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


#aggrement

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Agreement
from .serializers import AgreementSerializer
from django.utils import timezone

class CompanyAgreementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = request.user.company.id
        agreements = Agreement.objects.filter(company_id=company_id)
        serializer = AgreementSerializer(agreements, many=True, context={'request': request})
        return Response(serializer.data)

class ClientAgreementsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        agreements = Agreement.objects.filter(user=request.user)
        serializer = AgreementSerializer(agreements, many=True, context={'request': request})
        return Response(serializer.data)

class UpdateAgreementView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, agreement_id):
        agreement = get_object_or_404(Agreement, id=agreement_id)
        signed_document = request.FILES.get('signed_document')
        status = request.data.get('status')

        if signed_document:
            agreement.signed_document = signed_document
        if status:
            agreement.status = status
            if status == 'Signed':
                agreement.signed_at = timezone.now()

        agreement.save()
        serializer = AgreementSerializer(agreement, context={'request': request})
        return Response(serializer.data)


# # #Safety Tranning 
from django.core.mail import send_mail
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Inquiry
from django.core.files.storage import default_storage

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_training_email(request):
    try:
        data = request.data
        to_email = data.get('to_email')
        full_name = data.get('full_name')
        email_body = data.get('email_body')
        inquiry_id = data.get('inquiry_id')  # Add inquiry_id to the request data

        if not to_email or not email_body or not inquiry_id:
            return JsonResponse({'error': 'Missing required fields'}, status=400)

        # Update the inquiry status to "Scheduled"
        inquiry = Inquiry.objects.get(id=inquiry_id)
        if inquiry.status != 'Pending':
            return JsonResponse({'error': 'Inquiry must be in Pending status to send email'}, status=400)
        inquiry.status = 'Scheduled'
        inquiry.save()

        subject = f"Training Schedule Confirmation for {full_name}"
        message = email_body
        from_email = 'fybproject6@gmail.com'
        recipient_list = [to_email]

        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        return JsonResponse({'message': 'Email sent successfully'}, status=200)
    except Inquiry.DoesNotExist:
        return JsonResponse({'error': 'Inquiry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_certificate(request, inquiry_id):
    try:
        inquiry = Inquiry.objects.get(id=inquiry_id)
        if inquiry.status != 'Completed':
            return JsonResponse({'error': 'Training must be marked as Completed to upload a certificate'}, status=400)

        if 'certificate' not in request.FILES:
            return JsonResponse({'error': 'No certificate file provided'}, status=400)

        certificate_file = request.FILES['certificate']
        inquiry.certificate = certificate_file
        inquiry.save()

        return JsonResponse({'message': 'Certificate uploaded successfully', 'certificate_url': inquiry.certificate.url}, status=200)
    except Inquiry.DoesNotExist:
        return JsonResponse({'error': 'Inquiry not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


#construction 
# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Inquiry, BuildingConstructionData
from django.core.files.storage import default_storage
import os
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Inquiry, BuildingConstructionData
from django.core.files.storage import default_storage

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_progress_photos(request, inquiry_id):
    try:
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, company=request.user.company)
        building_data = inquiry.building_data
        photos = request.FILES.getlist('photos')
        if not photos:
            return Response({'error': 'Please select photos to upload'}, status=400)
        
        photo_paths = building_data.progress_photos or []
        for photo in photos:
            file_path = f'inquiry_files/building/{inquiry_id}_{photo.name}'
            default_storage.save(file_path, photo)
            photo_paths.append(file_path)
        building_data.progress_photos = photo_paths
        building_data.save()
        return Response({'message': 'Progress photos uploaded successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_inspection_reports(request, inquiry_id):
    try:
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, company=request.user.company)
        building_data = inquiry.building_data
        reports = request.FILES.getlist('reports')
        if not reports:
            return Response({'error': 'Please select reports to upload'}, status=400)
        
        report_paths = building_data.inspection_reports or []
        for report in reports:
            file_path = f'inquiry_files/building/{inquiry_id}_{report.name}'
            default_storage.save(file_path, report)
            report_paths.append(file_path)
        building_data.inspection_reports = report_paths
        building_data.save()
        return Response({'message': 'Inspection reports uploaded successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_completion_certificate(request, inquiry_id):
    try:
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, company=request.user.company)
        building_data = inquiry.building_data
        certificate = request.FILES.get('completion_certificate')
        if not certificate:
            return Response({'error': 'Please select a certificate to upload'}, status=400)
        
        file_path = f'inquiry_files/building/{inquiry_id}_{certificate.name}'
        default_storage.save(file_path, certificate)
        building_data.completion_certificate = file_path
        building_data.save()
        return Response({'message': 'Completion certificate uploaded successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_inquiry_status(request, inquiry_id):
    try:
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, company=request.user.company)
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status is required'}, status=400)
        old_status = inquiry.status
        inquiry.status = new_status
        inquiry.save()
        try:
            if inquiry.email:
                send_mail(
                    f"Status Update for Your Inquiry #{inquiry.id} - {inquiry.category}",
                    f"""
Dear {inquiry.full_name},
The status of your inquiry for {inquiry.sub_service} has been updated:
Previous Status: {old_status}
New Status: {new_status}
Please feel free to reach out with any questions.
Best regards,
{inquiry.company.company_name}
                    """,
                    'fybproject6@gmail.com',
                    [inquiry.email],
                    fail_silently=True,
                )
        except Exception as email_error:
            print(f"Error sending status update email for inquiry {inquiry_id}: {str(email_error)}")
        return Response({'message': 'Status updated successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_construction_progress(request, inquiry_id):
    try:
        inquiry = get_object_or_404(Inquiry, id=inquiry_id, company=request.user.company)
        building_data = inquiry.building_data
        data = request.data
        changes = []

        if 'permit_application_date' in data:
            building_data.permit_application_date = data['permit_application_date']
            changes.append(f"Permit Application Date: {data['permit_application_date']}")
        if 'permit_status' in data:
            valid_statuses = ['Submitted', 'Under Review', 'Approved', 'Rejected']
            if data['permit_status'] not in valid_statuses:
                return Response({'error': 'Invalid permit status'}, status=400)
            changes.append(f"Permit Status: {data['permit_status']}")
            building_data.permit_status = data['permit_status']
        if 'construction_start_date' in data:
            building_data.construction_start_date = data['construction_start_date']
            changes.append(f"Construction Start Date: {data['construction_start_date']}")
        if 'construction_phase' in data:
            valid_phases = ['Foundation', 'Walls', 'Roofing', 'Finishing', 'Excavation','Columns Casting','Beams Casting','Slab Casting', 'Electrical & Plumbing','Plastering']
            if data['construction_phase'] not in valid_phases:
                return Response({'error': 'Invalid construction phase'}, status=400)
            changes.append(f"Construction Phase: {data['construction_phase']}")
            building_data.construction_phase = data['construction_phase']
        if 'progress_percentage' in data:
            try:
                percentage = int(data['progress_percentage'])
                if not 0 <= percentage <= 100:
                    return Response({'error': 'Progress percentage must be between 0 and 100'}, status=400)
                changes.append(f"Progress Percentage: {percentage}%")
                building_data.progress_percentage = percentage
            except ValueError:
                return Response({'error': 'Progress percentage must be a number'}, status=400)
        if 'inspection_dates' in data:
            building_data.inspection_dates = data['inspection_dates']
            changes.append(f"Inspection Dates: {', '.join(data['inspection_dates'])}")
        if 'completion_certificate_application_date' in data:
            building_data.completion_certificate_application_date = data['completion_certificate_application_date']
            changes.append(f"Completion Certificate Application Date: {data['completion_certificate_application_date']}")
        if 'handover_date' in data:
            building_data.handover_date = data['handover_date']
            changes.append(f"Handover Date: {data['handover_date']}")
        if 'warranty_details' in data:
            building_data.warranty_details = data['warranty_details']
            changes.append(f"Warranty Details: {data['warranty_details']}")

        building_data.save()

        try:
            if changes and inquiry.email:
                send_mail(
                    f"Progress Update for Your Inquiry #{inquiry.id} - {inquiry.category}",
                    f"""
Dear {inquiry.full_name},
The progress of your inquiry for {inquiry.sub_service} has been updated:
Changes:
{chr(10).join(f"- {change}" for change in changes)}
Please feel free to reach out with any questions.
Best regards,
{inquiry.company.company_name}
                    """,
                    'fybproject6@gmail.com',
                    [inquiry.email],
                    fail_silently=True,
                )
        except Exception as email_error:
            print(f"Error sending progress update email for inquiry {inquiry_id}: {str(email_error)}")

        return Response({'message': 'Construction progress updated'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)   


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_comment_response(request, comment_id):
    try:
        comment = get_object_or_404(Comment, id=comment_id, company=request.user.company)
        company_response = request.data.get('company_response')
        if not company_response:
            return Response({'error': 'Company response is required'}, status=400)
        
        comment.company_response = company_response
        comment.save()

        # Optionally send email to user
        send_mail(
            f'Update on Your Inquiry #{comment.inquiry.id}',
            f"""
Dear {comment.inquiry.full_name},

We have responded to your comment:
Original Comment: "{comment.comment_text}"
Our Response: "{company_response}"

Best regards,
{request.user.company.company_name}
""",
            'fybproject6@gmail.com',
            [comment.inquiry.email],
            fail_silently=True,
        )

        return Response({'message': 'Comment response updated successfully'}, status=200)
    except Exception as e:
        return Response({'error': str(e)}, status=500)
    
# views.py
from .models import Inquiry, Comment, Company
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_comment(request, inquiry_id):
    try:
        # Get the inquiry
        inquiry = get_object_or_404(Inquiry, id=inquiry_id)
        user = request.user

        # Check permissions: user must be part of the company
        company = getattr(user, 'company', None)
        if not (company and inquiry.company == company):
            return Response({"error": "You do not have permission to comment on this inquiry"}, status=403)

        # Validate comment text
        comment_text = request.data.get('comment_text')
        if not comment_text:
            return Response({"error": "Comment text is required"}, status=400)

        # Create the comment
        comment = Comment.objects.create(
            inquiry=inquiry,
            company=inquiry.company,
            comment_text=comment_text,
            created_by=user
        )

        # Send email notification (optional)
        try:
            if inquiry.email:
                send_mail(
                    f"Update on Your Inquiry #{inquiry.id} - {inquiry.category}",
                    f"""
Dear {inquiry.full_name},
We have an update regarding your inquiry for {inquiry.sub_service}:
Comment from {company.company_name}:
"{comment_text}"
Please feel free to reach out if you have any questions.
Best regards,
{company.company_name}
                    """,
                    'fybproject6@gmail.com',
                    [inquiry.email],
                    fail_silently=True,
                )
        except Exception as email_error:
            print(f"Error sending email for comment on inquiry {inquiry_id}: {str(email_error)}")

        serializer = CommentSerializer(comment)
        return Response({
            "message": "Comment added successfully",
            "comment": serializer.data
        }, status=200)
    except Inquiry.DoesNotExist:
        return Response({"error": "No Inquiry matches the given query"}, status=404)
    except Exception as e:
        print(f"Error adding comment for inquiry {inquiry_id}: {str(e)}")
        return Response({"error": "Failed to add comment due to an internal error"}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_client_comment(request, inquiry_id):
    try:
        # Get the inquiry
        inquiry = get_object_or_404(Inquiry, id=inquiry_id)
        user = request.user

        # Check permissions: user must be the inquiry owner
        if inquiry.user != user:
            return Response({"error": "You do not have permission to comment on this inquiry"}, status=403)

        # Validate comment text
        comment_text = request.data.get('comment_text')
        if not comment_text:
            return Response({"error": "Comment text is required"}, status=400)

        # Create the comment
        comment = Comment.objects.create(
            inquiry=inquiry,
            company=inquiry.company,
            comment_text=comment_text,
            created_by=user
        )

        # Send email notification to company (optional)
        try:
            if inquiry.company and inquiry.company.email:
                send_mail(
                    f"New Client Comment on Inquiry #{inquiry.id} - {inquiry.category}",
                    f"""
Dear {inquiry.company.company_name},
You have a new comment on your inquiry for {inquiry.sub_service}:
Comment from {inquiry.full_name}:
"{comment_text}"
Please feel free to respond via the platform.
Best regards,
{inquiry.full_name}
                    """,
                    'fybproject6@gmail.com',
                    [inquiry.company.email],
                    fail_silently=True,
                )
        except Exception as email_error:
            print(f"Error sending email for client comment on inquiry {inquiry_id}: {str(email_error)}")

        serializer = CommentSerializer(comment)
        return Response({
            "message": "Comment added successfully",
            "comment": serializer.data
        }, status=200)
    except Inquiry.DoesNotExist:
        return Response({"error": "No Inquiry matches the given query"}, status=404)
    except Exception as e:
        print(f"Error adding client comment for inquiry {inquiry_id}: {str(e)}")
        return Response({"error": "Failed to add comment due to an internal error"}, status=500)



#ADMIN
@csrf_exempt
def service_categories(request):
    """Handle GET and POST requests for service categories"""
    if request.method == 'GET':
        """Returns all service categories"""
        try:
            categories = ServiceCategory.objects.all()
            data = [
                {
                    "id": category.id,
                    "name": category.name
                }
                for category in categories
            ]
            return JsonResponse(data, safe=False)
        except Exception as e:
            logger.error(f"Error in get_service_categories: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'POST':
        """Create a new service category"""
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({"error": "Category name is required"}, status=400)

            # Check if category already exists
            if ServiceCategory.objects.filter(name=name).exists():
                return JsonResponse({"error": "Category with this name already exists"}, status=400)

            category = ServiceCategory.objects.create(name=name)
            return JsonResponse({
                "id": category.id,
                "name": category.name
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating service category: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Method not allowed"}, status=405)
@csrf_exempt
def create_service_category(request):
    """Create a new service category"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({"error": "Category name is required"}, status=400)

            # Check if category already exists
            if ServiceCategory.objects.filter(name=name).exists():
                return JsonResponse({"error": "Category with this name already exists"}, status=400)

            category = ServiceCategory.objects.create(name=name)
            return JsonResponse({
                "id": category.id,
                "name": category.name
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating service category: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def update_service_category(request, category_id):
    """Update an existing service category"""
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            if not name:
                return JsonResponse({"error": "Category name is required"}, status=400)

            try:
                category = ServiceCategory.objects.get(id=category_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Category not found"}, status=404)

            # Check if the new name already exists (excluding the current category)
            if ServiceCategory.objects.filter(name=name).exclude(id=category_id).exists():
                return JsonResponse({"error": "Category with this name already exists"}, status=400)

            category.name = name
            category.save()
            return JsonResponse({
                "id": category.id,
                "name": category.name
            })
        except Exception as e:
            logger.error(f"Error updating service category: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def delete_service_category(request, category_id):
    """Delete a service category"""
    if request.method == 'DELETE':
        try:
            try:
                category = ServiceCategory.objects.get(id=category_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Category not found"}, status=404)

            # Check if the category has associated services
            if category.services.exists():
                return JsonResponse({"error": "Cannot delete category with associated services"}, status=400)

            category.delete()
            return JsonResponse({"message": "Category deleted successfully"})
        except Exception as e:
            logger.error(f"Error deleting service category: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def create_service(request):
    """Create a new service"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            category_id = data.get('category_id')

            if not name:
                return JsonResponse({"error": "Service name is required"}, status=400)
            if not category_id:
                return JsonResponse({"error": "Category ID is required"}, status=400)

            try:
                category = ServiceCategory.objects.get(id=category_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Category not found"}, status=404)

            # Check if service with this name already exists in the category
            if Service.objects.filter(name=name, category=category).exists():
                return JsonResponse({"error": "Service with this name already exists in this category"}, status=400)

            service = Service.objects.create(name=name, category=category)
            return JsonResponse({
                "id": service.id,
                "name": service.name,
                "category_id": service.category.id,
                "category": service.category.name
            }, status=201)
        except Exception as e:
            logger.error(f"Error creating service: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def update_service(request, service_id):
    """Update an existing service"""
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            category_id = data.get('category_id')

            if not name:
                return JsonResponse({"error": "Service name is required"}, status=400)
            if not category_id:
                return JsonResponse({"error": "Category ID is required"}, status=400)

            try:
                service = Service.objects.get(id=service_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Service not found"}, status=404)

            try:
                category = ServiceCategory.objects.get(id=category_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Category not found"}, status=404)

            # Check if another service with this name already exists in the category
            if Service.objects.filter(name=name, category=category).exclude(id=service_id).exists():
                return JsonResponse({"error": "Service with this name already exists in this category"}, status=400)

            service.name = name
            service.category = category
            service.save()
            return JsonResponse({
                "id": service.id,
                "name": service.name,
                "category_id": service.category.id,
                "category": service.category.name
            })
        except Exception as e:
            logger.error(f"Error updating service: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def delete_service(request, service_id):
    """Delete a service"""
    if request.method == 'DELETE':
        try:
            try:
                service = Service.objects.get(id=service_id)
            except ObjectDoesNotExist:
                return JsonResponse({"error": "Service not found"}, status=404)

            # Check if the service is used in CompanyServices
            if CompanyServices.objects.filter(service=service).exists():
                return JsonResponse({"error": "Cannot delete service that is used by a company"}, status=400)

            service.delete()
            return JsonResponse({"message": "Service deleted successfully"})
        except Exception as e:
            logger.error(f"Error deleting service: {str(e)}")
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Method not allowed"}, status=405)


#subscription
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.utils import timezone
# from datetime import timedelta
# from .models import Subscription, Company
# from .serializers import SubscriptionSerializer
# class SubscriptionPaymentIntentView(APIView):
#     def post(self, request, company_id):
#         logger.debug(f"Received request to create payment intent for company {company_id}")
#         try:
#             company = Company.objects.get(id=company_id)
#             if not request.user.is_authenticated:
#                 return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
#             if request.user.company_id != company.id and not request.user.is_staff:
#                 return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

#             plan = request.data.get('plan')
#             price = request.data.get('price')
#             if plan == 'trial':
#                 return Response({'error': 'Trial plan does not require payment'}, status=status.HTTP_400_BAD_REQUEST)

#             if plan not in ['monthly', 'quarterly', 'yearly']:
#                 return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

#             plan_prices = {
#                 'monthly': 500,
#                 'quarterly': 1200,
#                 'yearly': 4500,
#             }
#             amount = plan_prices[plan]

#             payment_intent = stripe.PaymentIntent.create(
#                 amount=amount,
#                 currency="usd",
#                 metadata={
#                     "company_id": company_id,
#                     "plan": plan,
#                 },
#                 automatic_payment_methods={"enabled": True},
#             )

#             if company.stripe_account_id:
#                 stripe.PaymentIntent.modify(
#                     payment_intent.id,
#                     transfer_group=f"subscription_{company_id}_{plan}",
#                     transfer_data={
#                         "destination": company.stripe_account_id,
#                     },
#                 )

#             return Response({
#                 "client_secret": payment_intent.client_secret,
#             }, status=status.HTTP_200_OK)
#         except Company.DoesNotExist:
#             return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
#         except stripe.error.StripeError as e:
#             logger.error(f"Stripe error: {str(e)}")
#             return Response({"error": "Payment processing failed: " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             logger.error(f"Unexpected error: {str(e)}")
#             return Response({"error": "An unexpected error occurred: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Subscription, Company, Plan
import stripe
import logging

logger = logging.getLogger(__name__)

class SubscriptionPaymentIntentView(APIView):
    def post(self, request, company_id):
        logger.debug(f"Received request to create payment intent for company {company_id}")
        logger.debug(f"Request data: {request.data}")  # Log the incoming request data
        try:
            company = Company.objects.get(id=company_id)
            if not request.user.is_authenticated:
                return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
            if request.user.company_id != company.id and not request.user.is_staff:
                return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

            plan = request.data.get('plan')
            price = request.data.get('price')

            if plan == 'trial':
                return Response({'error': 'Trial plan does not require payment'}, status=status.HTTP_400_BAD_REQUEST)

            if plan not in ['monthly', 'quarterly', 'yearly']:
                return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

            if price is None:
                logger.error("Price is missing in request data")
                return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                price = float(price)
                if price <= 0:
                    raise ValueError("Price must be positive")
            except (ValueError, TypeError):
                logger.error(f"Invalid price format: {price}")
                return Response({'error': 'Invalid price'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate price against Plan model
            try:
                plan_obj = Plan.objects.get(name__iexact=plan)
                if abs(float(plan_obj.price) - price) > 0.01:  # Allow minor float differences
                    logger.error(f"Price mismatch: expected {plan_obj.price}, got {price}")
                    return Response({'error': 'Price does not match plan'}, status=status.HTTP_400_BAD_REQUEST)
            except Plan.DoesNotExist:
                return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

            # Convert price to cents for Stripe (assuming RS. is equivalent to USD cents for simplicity)
            amount = int(price * 100)  # e.g., 500.00 -> 50000 cents

            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency="usd",
                metadata={
                    "company_id": company_id,
                    "plan": plan,
                    "price": price,
                },
                automatic_payment_methods={"enabled": True},
            )

            if company.stripe_account_id:
                stripe.PaymentIntent.modify(
                    payment_intent.id,
                    transfer_group=f"subscription_{company_id}_{plan}",
                    transfer_data={
                        "destination": company.stripe_account_id,
                    },
                )

            return Response({
                "client_secret": payment_intent.client_secret,
            }, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return Response({"error": "Payment processing failed: " + str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred: " + str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# import logging

# logger = logging.getLogger(__name__)

# class SubscriptionStatusView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, company_id):
#         try:
#             company = Company.objects.get(id=company_id)
#             if request.user.company_id != company.id and not request.user.is_staff:
#                 return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

#             subscription = Subscription.objects.filter(
#                 company=company
#             ).order_by('-start_date').first()

#             if not subscription:
#                 return Response({
#                     'is_subscribed': False,
#                     'end_date': None,
#                     'trial_end_date': None,
#                     'grace_end_date': None,
#                     'has_used_trial': False,
#                     'is_valid': False
#                 }, status=status.HTTP_200_OK)

#             is_valid = subscription.is_valid()
#             if not is_valid and subscription.is_active:
#                 subscription.is_active = False
#                 subscription.save()

#             return Response({
#                 'is_subscribed': subscription.plan != 'trial' and subscription.end_date > timezone.now(),
#                 'end_date': subscription.end_date,
#                 'trial_end_date': subscription.trial_end_date,
#                 'grace_end_date': subscription.grace_end_date,
#                 'has_used_trial': subscription.has_used_trial,
#                 'is_valid': is_valid
#             }, status=status.HTTP_200_OK)
#         except Company.DoesNotExist:
#             return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.error(f"Error in SubscriptionStatusView: {str(e)}")
#             return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        try:
            company = Company.objects.get(id=company_id)
            if request.user.company_id != company.id and not request.user.is_staff:
                return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

            subscription = Subscription.objects.filter(
                company=company
            ).order_by('-start_date').first()

            if not subscription:
                return Response({
                    'is_subscribed': False,
                    'end_date': None,
                    'trial_end_date': None,
                    'grace_end_date': None,
                    'has_used_trial': False,
                    'is_valid': False
                }, status=status.HTTP_200_OK)

            is_valid = subscription.is_valid()
            if not is_valid and subscription.is_active:
                subscription.is_active = False
                subscription.save()

            return Response({
                'is_subscribed': subscription.plan != 'trial' and subscription.end_date > timezone.now(),
                'end_date': subscription.end_date,
                'trial_end_date': subscription.trial_end_date,
                'grace_end_date': subscription.grace_end_date,
                'has_used_trial': subscription.has_used_trial,
                'is_valid': is_valid
            }, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in SubscriptionStatusView: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone
# from datetime import timedelta
# import logging

# logger = logging.getLogger(__name__)

# class SubscribeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, company_id):
#         try:
#             # Log the incoming request data for debugging
#             logger.debug(f"SubscribeView - Request data: {request.data}")

#             company = Company.objects.get(id=company_id)
#             if request.user.company_id != company.id and not request.user.is_staff:
#                 return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

#             plan = request.data.get('plan')
#             payment_data = request.data.get('payment_data')

#             if plan not in ['trial', 'monthly', 'quarterly', 'yearly']:
#                 return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

#             existing_subscription = Subscription.objects.filter(
#                 company=company
#             ).order_by('-start_date').first()

#             if plan == 'trial':
#                 if existing_subscription and existing_subscription.has_used_trial:
#                     return Response({'error': 'Free trial already used'}, status=status.HTTP_400_BAD_REQUEST)
#                 # Create trial subscription
#                 subscription = Subscription.objects.create(
#                     company=company,
#                     plan='trial',
#                     start_date=timezone.now(),
#                     trial_end_date=timezone.now() + timedelta(days=15),
#                     is_active=True,
#                     has_used_trial=True
#                 )
#                 return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)

#             if not payment_data or not payment_data.get('transaction_id'):
#                 return Response({'error': 'Payment data required'}, status=status.HTTP_400_BAD_REQUEST)

#             start_date = timezone.now()
#             duration_days = {
#                 'monthly': 30,
#                 'quarterly': 90,
#                 'yearly': 365,
#             }
#             total_days = duration_days[plan]

#             if existing_subscription and existing_subscription.is_valid():
#                 remaining_time = max(
#                     existing_subscription.end_date or timezone.now(),
#                     existing_subscription.trial_end_date or timezone.now(),
#                     existing_subscription.grace_end_date or timezone.now()
#                 ) - start_date
#                 remaining_days = remaining_time.days
#                 if remaining_days > 0:
#                     total_days += remaining_days
#                 existing_subscription.is_active = False
#                 existing_subscription.save()

#             end_date = start_date + timedelta(days=total_days)
#             subscription = Subscription.objects.create(
#                 company=company,
#                 plan=plan,
#                 start_date=start_date,
#                 end_date=end_date,
#                 grace_end_date=end_date + timedelta(days=5),
#                 is_active=True,
#                 payment_data=payment_data,
#                 has_used_trial=existing_subscription.has_used_trial if existing_subscription else False
#             )

#             # Log the subscription object before serialization
#             logger.debug(f"Subscription created: {subscription.__dict__}")

#             # Serialize the subscription
#             serializer = SubscriptionSerializer(subscription)
#             logger.debug(f"Serialized data: {serializer.data}")

#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Company.DoesNotExist:
#             logger.error("Company not found for company_id: %s", company_id)
#             return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             # Log the full exception details
#             logger.exception(f"Error in SubscribeView: {str(e)}")
#             return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone
# from datetime import timedelta
# import logging

# logger = logging.getLogger(__name__)

# class SubscribeView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, company_id):
#         try:
#             logger.debug(f"SubscribeView - Request data: {request.data}")

#             company = Company.objects.get(id=company_id)
#             if request.user.company_id != company.id and not request.user.is_staff:
#                 return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

#             plan = request.data.get('plan')
#             price = request.data.get('price')
#             payment_data = request.data.get('payment_data')

            

#             if plan not in ['trial', 'monthly', 'quarterly', 'yearly']:
#                 return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

#             if price is None:
#                 return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

#             try:
#                 price = float(price)
#                 if price < 0:
#                     raise ValueError("Price cannot be negative")
#             except (ValueError, TypeError):
#                 return Response({'error': 'Invalid price'}, status=status.HTTP_400_BAD_REQUEST)

#             # Validate price against Plan model (except for trial)
#             if plan != 'trial':
#                 try:
#                     plan_obj = Plan.objects.get(name__iexact=plan)
#                     if abs(float(plan_obj.price) - price) > 0.01:
#                         return Response({'error': 'Price does not match plan'}, status=status.HTTP_400_BAD_REQUEST)
#                 except Plan.DoesNotExist:
#                     return Response({'error': 'Plan not found'}, status=status.HTTP_400_BAD_REQUEST)
#             else:
#                 if price != 0.00:
#                     return Response({'error': 'Trial plan must have zero price'}, status=status.HTTP_400_BAD_REQUEST)

#             existing_subscription = Subscription.objects.filter(
#                 company=company
#             ).order_by('-start_date').first()

#             if plan == 'trial':
#                 if existing_subscription and existing_subscription.has_used_trial:
#                     return Response({'error': 'Free trial already used'}, status=status.HTTP_400_BAD_REQUEST)
#                 subscription = Subscription.objects.create(
#                     company=company,
#                     plan='trial',
#                     amount=price,  # Store price as amount
#                     start_date=timezone.now(),
#                     trial_end_date=timezone.now() + timedelta(days=15),
#                     is_active=True,
#                     has_used_trial=True
#                 )
#                 return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)

#             if not payment_data or not payment_data.get('transaction_id'):
#                 return Response({'error': 'Payment data required'}, status=status.HTTP_400_BAD_REQUEST)

#             start_date = timezone.now()
#             duration_days = {
#                 'monthly': 30,
#                 'quarterly': 90,
#                 'yearly': 365,
#             }
#             total_days = duration_days[plan]

#             if existing_subscription and existing_subscription.is_valid():
#                 remaining_time = max(
#                     existing_subscription.end_date or timezone.now(),
#                     existing_subscription.trial_end_date or timezone.now(),
#                     existing_subscription.grace_end_date or timezone.now()
#                 ) - start_date
#                 remaining_days = remaining_time.days
#                 if remaining_days > 0:
#                     total_days += remaining_days
#                 existing_subscription.is_active = False
#                 existing_subscription.save()

#             end_date = start_date + timedelta(days=total_days)
#             subscription = Subscription.objects.create(
#                 company=company,
#                 plan=plan,
#                 amount=price,  # Store price as amount
#                 start_date=start_date,
#                 end_date=end_date,
#                 grace_end_date=end_date + timedelta(days=5),
#                 is_active=True,
#                 payment_data=payment_data,
#                 has_used_trial=existing_subscription.has_used_trial if existing_subscription else False
#             )

#             logger.debug(f"Subscription created: {subscription.__dict__}")
#             serializer = SubscriptionSerializer(subscription)
#             logger.debug(f"Serialized data: {serializer.data}")

#             return Response(serializer.data, status=status.HTTP_200_OK)

#         except Company.DoesNotExist:
#             logger.error("Company not found for company_id: %s", company_id)
#             return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
#         except Exception as e:
#             logger.exception(f"Error in SubscribeView: {str(e)}")
#             return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class SubscribeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, company_id):
        try:
            logger.debug(f"SubscribeView - Request data: {request.data}")

            company = Company.objects.get(id=company_id)
            if request.user.company_id != company.id and not request.user.is_staff:
                return Response({"error": "You are not authorized to perform this action"}, status=status.HTTP_403_FORBIDDEN)

            plan = request.data.get('plan')
            price = request.data.get('price')
            payment_data = request.data.get('payment_data')

            if plan not in ['trial', 'monthly', 'quarterly', 'yearly']:
                return Response({'error': 'Invalid plan'}, status=status.HTTP_400_BAD_REQUEST)

            if price is None:
                logger.error("Price is missing in request data")
                return Response({'error': 'Price is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                price = float(price)
                if price < 0:
                    raise ValueError("Price cannot be negative")
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid price format: {price}, error: {str(e)}")
                return Response({'error': 'Invalid price'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate price against Plan model (except for trial)
            if plan != 'trial':
                try:
                    plan_obj = Plan.objects.get(name__iexact=plan)
                    if abs(float(plan_obj.price) - price) > 0.01:
                        logger.error(f"Price mismatch: expected {plan_obj.price}, got {price}")
                        return Response({'error': 'Price does not match plan'}, status=status.HTTP_400_BAD_REQUEST)
                except Plan.DoesNotExist:
                    return Response({'error': 'Plan not found'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                if price != 0.00:
                    return Response({'error': 'Trial plan must have zero price'}, status=status.HTTP_400_BAD_REQUEST)

            existing_subscription = Subscription.objects.filter(
                company=company
            ).order_by('-start_date').first()

            if plan == 'trial':
                if existing_subscription and existing_subscription.has_used_trial:
                    return Response({'error': 'Free trial already used'}, status=status.HTTP_400_BAD_REQUEST)
                subscription = Subscription.objects.create(
                    company=company,
                    plan='trial',
                    amount=price,  # Store price as amount
                    start_date=timezone.now(),
                    trial_end_date=timezone.now() + timedelta(days=15),
                    is_active=True,
                    has_used_trial=True
                )
                return Response(SubscriptionSerializer(subscription).data, status=status.HTTP_200_OK)

            if not payment_data or not payment_data.get('transaction_id'):
                return Response({'error': 'Payment data required'}, status=status.HTTP_400_BAD_REQUEST)

            start_date = timezone.now()
            duration_days = {
                'monthly': 30,
                'quarterly': 90,
                'yearly': 365,
            }
            total_days = duration_days[plan]

            if existing_subscription and existing_subscription.is_valid():
                remaining_time = max(
                    existing_subscription.end_date or timezone.now(),
                    existing_subscription.trial_end_date or timezone.now(),
                    existing_subscription.grace_end_date or timezone.now()
                ) - start_date
                remaining_days = remaining_time.days
                if remaining_days > 0:
                    total_days += remaining_days
                existing_subscription.is_active = False
                existing_subscription.save()

            end_date = start_date + timedelta(days=total_days)
            subscription = Subscription.objects.create(
                company=company,
                plan=plan,
                amount=price,  # Store price as amount
                start_date=start_date,
                end_date=end_date,
                grace_end_date=end_date + timedelta(days=5),
                is_active=True,
                payment_data=payment_data,
                has_used_trial=True  # Set to True for paid subscriptions to block future trials
            )

            logger.debug(f"Subscription created: {subscription.__dict__}")
            serializer = SubscriptionSerializer(subscription)
            logger.debug(f"Serialized data: {serializer.data}")

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Company.DoesNotExist:
            logger.error("Company not found for company_id: %s", company_id)
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.exception(f"Error in SubscribeView: {str(e)}")
            return Response({'error': f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PlanListView(APIView):
    def get(self, request, company_id=None):
        try:
            plans = Plan.objects.all()
            serializer = PlanSerializer(plans, many=True)
            data = serializer.data

            if company_id:
                company = Company.objects.get(id=company_id)
                subscription = Subscription.objects.filter(
                    company=company
                ).order_by('-start_date').first()
                has_used_trial = subscription.has_used_trial if subscription else False
            else:
                has_used_trial = False

            if not has_used_trial:
                trial_plan = {
                    'name': 'Trial',
                    'price': '0.00',
                    'duration': '15 days',
                    'days': 15
                }
                data.insert(0, trial_plan)

            return Response(data, status=status.HTTP_200_OK)
        except Company.DoesNotExist:
            return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in PlanListView: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





from django.db.models import Sum, Count
from .models import CompanyServices, Appointment, PaymentDistribution

class CompanyDashboardDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = request.user.company_id  # Assuming the user has a company_id (adjust based on your auth setup)
        
        # Total Services
        total_services = CompanyServices.objects.filter(company_id=company_id).count()
        
        # Pending Appointments
        pending_appointments = Appointment.objects.filter(
            company_id=company_id,
            status='Pending'
        ).count()
        
        # Total Revenue
        total_revenue = PaymentDistribution.objects.filter(
            company_id=company_id
        ).aggregate(total=Sum('amount'))['total'] or 0.00

        return Response({
            'total_services': total_services,
            'pending_appointments': pending_appointments,
            'total_revenue': float(total_revenue),  # Convert Decimal to float for JSON serialization

        })



from django.db.models.functions import TruncMonth, TruncDay

import datetime

# class RevenueAnalyticsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         company_id = request.user.company_id  # Adjust based on your auth setup
#         # Group revenue by month (you can change to TruncDay for daily data)
#         revenue_data = (
#             PaymentDistribution.objects.filter(company_id=company_id)
#             .annotate(month=TruncMonth('created_at'))
#             .values('month')
#             .annotate(total_revenue=Sum('amount'))
#             .order_by('month')
#         )

#         # Format the data for the frontend
#         revenue_over_time = [
#             {
#                 'month': entry['month'].strftime('%Y-%m'),  # Format as YYYY-MM
#                 'total_revenue': float(entry['total_revenue']),  # Convert Decimal to float
#             }
#             for entry in revenue_data
#         ]

#         return Response(revenue_over_time)           
# class AppointmentAnalyticsView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         company_id = request.user.company_id  # Adjust based on your auth setup
#         # Group appointments by month and status
#         appointment_data = (
#             Appointment.objects.filter(company_id=company_id)
#             .annotate(month=TruncMonth('created_at'))
#             .values('month', 'status')
#             .annotate(count=Count('id'))
#             .order_by('month', 'status')
#         )

#         # Format the data for the frontend
#         appointment_over_time = {}
#         for entry in appointment_data:
#             month = entry['month'].strftime('%Y-%m')
#             if month not in appointment_over_time:
#                 appointment_over_time[month] = {'Pending': 0, 'Confirmed': 0, 'No-Show': 0, 'Completed': 0}
#             appointment_over_time[month][entry['status']] = entry['count']

#         # Convert to list format for easier frontend handling
#         formatted_data = [
#             {'month': month, **statuses}
#             for month, statuses in appointment_over_time.items()
#         ]

#         return Response(formatted_data)

from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth
from .models import PaymentDistribution, Appointment
import datetime

class RevenueAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = request.user.company_id
        time_range = request.query_params.get('time_range', '6m')  # Default to 6 months

        # Calculate the start date based on time_range
        if time_range == '3m':
            start_date = datetime.datetime.now() - datetime.timedelta(days=90)
        elif time_range == '12m':
            start_date = datetime.datetime.now() - datetime.timedelta(days=365)
        elif time_range == 'all':
            start_date = None  # No filter, fetch all data
        else:  # Default to 6 months
            start_date = datetime.datetime.now() - datetime.timedelta(days=180)

        # Fetch revenue data
        query = PaymentDistribution.objects.filter(company_id=company_id)
        if start_date:
            query = query.filter(created_at__gte=start_date)

        revenue_data = (
            query
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total_revenue=Sum('amount'))
            .order_by('month')
        )

        revenue_over_time = [
            {
                'month': entry['month'].strftime('%Y-%m'),
                'total_revenue': float(entry['total_revenue']),
            }
            for entry in revenue_data
        ]

        return Response(revenue_over_time)

class AppointmentAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        company_id = request.user.company_id
        time_range = request.query_params.get('time_range', '6m')

        # Calculate the start date based on time_range
        if time_range == '3m':
            start_date = datetime.datetime.now() - datetime.timedelta(days=90)
        elif time_range == '12m':
            start_date = datetime.datetime.now() - datetime.timedelta(days=365)
        elif time_range == 'all':
            start_date = None
        else:
            start_date = datetime.datetime.now() - datetime.timedelta(days=180)

        # Fetch appointment data
        query = Appointment.objects.filter(company_id=company_id)
        if start_date:
            query = query.filter(created_at__gte=start_date)

        appointment_data = (
            query
            .annotate(month=TruncMonth('created_at'))
            .values('month', 'status')
            .annotate(count=Count('id'))
            .order_by('month', 'status')
        )

        appointment_over_time = {}
        for entry in appointment_data:
            month = entry['month'].strftime('%Y-%m')
            if month not in appointment_over_time:
                appointment_over_time[month] = {'Pending': 0, 'Confirmed': 0, 'No-Show': 0, 'Completed': 0}
            appointment_over_time[month][entry['status']] = entry['count']

        formatted_data = [
            {'month': month, **statuses}
            for month, statuses in appointment_over_time.items()
        ]

        return Response(formatted_data)


# #adminfrom rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import Subscription
import logging

logger = logging.getLogger(__name__)

class SubscriptionAnalyticsView(APIView):
    def get(self, request):
        try:
            # Get the period parameter (monthly, quarterly, yearly)
            period = request.query_params.get('period', 'monthly').lower()
            if period not in ['monthly', 'quarterly', 'yearly']:
                return Response({"error": "Invalid period. Use 'monthly', 'quarterly', or 'yearly'."}, status=status.HTTP_400_BAD_REQUEST)

            # Determine the number of intervals and interval duration
            if period == 'monthly':
                num_intervals = 6  # Last 6 months
                interval_days = 30
            elif period == 'quarterly':
                num_intervals = 4  # Last 4 quarters
                interval_days = 90
            else:  # yearly
                num_intervals = 3  # Last 3 years
                interval_days = 365

            today = timezone.now()
            labels = []
            revenue_by_type = {
                'trial': [],
                'monthly': [],
                'quarterly': [],
                'yearly': [],
            }
            subscriptions_by_type = {
                'trial': [],
                'monthly': [],
                'quarterly': [],
                'yearly': [],
            }
            total_revenue = []
            total_subscriptions = []

            for i in range(num_intervals - 1, -1, -1):  # Count backwards from the most recent interval
                if period == 'monthly':
                    # Monthly: Start of the month
                    interval_start = (today - timedelta(days=interval_days * i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    interval_end = (interval_start + timedelta(days=31)).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
                    label = interval_start.strftime("%B")
                elif period == 'quarterly':
                    # Quarterly: Start of the quarter
                    months_back = i * 3
                    interval_start = (today - timedelta(days=months_back * 30)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    quarter = (interval_start.month - 1) // 3 + 1
                    interval_start = interval_start.replace(month=(quarter - 1) * 3 + 1)
                    interval_end = (interval_start + timedelta(days=interval_days)).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
                    label = f"Q{quarter} {interval_start.year}"
                else:  # yearly
                    # Yearly: Start of the year
                    interval_start = (today - timedelta(days=interval_days * i)).replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    interval_end = (interval_start + timedelta(days=interval_days)) - timedelta(seconds=1)
                    label = interval_start.strftime("%Y")

                # Fetch subscriptions for this interval
                interval_subscriptions = Subscription.objects.filter(
                    start_date__gte=interval_start,
                    start_date__lte=interval_end
                )

                # Calculate revenue and subscription count by type
                type_revenue = {'trial': 0, 'monthly': 0, 'quarterly': 0, 'yearly': 0}
                type_count = {'trial': 0, 'monthly': 0, 'quarterly': 0, 'yearly': 0}

                for sub in interval_subscriptions:
                    plan_type = sub.plan
                    type_revenue[plan_type] += float(sub.amount or 0)
                    type_count[plan_type] += 1

                # Append data for this interval
                labels.append(label)
                for plan_type in type_revenue:
                    revenue_by_type[plan_type].append(type_revenue[plan_type])
                    subscriptions_by_type[plan_type].append(type_count[plan_type])

                # Total revenue and subscriptions for this interval
                total_revenue.append(sum(type_revenue.values()))
                total_subscriptions.append(sum(type_count.values()))

            return Response({
                "labels": labels,
                "revenue_by_type": revenue_by_type,
                "subscriptions_by_type": subscriptions_by_type,
                "total_revenue": total_revenue,
                "total_subscriptions": total_subscriptions
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in SubscriptionAnalyticsView: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class TotalRevenueView(APIView):
    def get(self, request):
        try:
            total_revenue = sum(float(sub.amount or 0) for sub in Subscription.objects.all())
            return Response({"total_revenue": total_revenue}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in TotalRevenueView: {str(e)}")
            return Response({"error": "Failed to calculate total revenue"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#notification 
import json
import time
import logging
from django.http import StreamingHttpResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from django.db import DatabaseError
from .models import Notification

# Set up logging
logger = logging.getLogger(__name__)

def sse_notifications(request):
    # Prefer token from Authorization header
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    token = None
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    else:
        token = request.GET.get('token')  # Fallback to query param

    user = AnonymousUser()
    if token:
        jwt_auth = JWTAuthentication()
        try:
            validated_token = jwt_auth.get_validated_token(token)
            user = jwt_auth.get_user(validated_token)
        except (InvalidToken, AuthenticationFailed) as e:
            logger.error(f"Authentication error: {e}")

    def event_stream():
        if not user.is_authenticated:
            yield "event: error\ndata: Unauthorized\nretry: 10000\n\n"
            return

        last_id = 0
        heartbeat_interval = 15  # Send heartbeat every 15 seconds
        last_heartbeat = time.time()

        while True:
            try:
                # Check for new notifications
                notifications = Notification.objects.filter(
                    recipient=user, 
                    id__gt=last_id, is_read = False
                ).order_by("id")
                
        
                for notification in notifications:
                    data = {
                        "id": notification.id,
                        "message": notification.message,
                        "type": notification.type,
                        "created_at": notification.created_at.isoformat(),
                        "is_read": notification.is_read,
                    }
                    yield f"event: notification\ndata: {json.dumps(data)}\n\n"
                    last_id = notification.id

                # Send heartbeat to keep connection alive
                if time.time() - last_heartbeat >= heartbeat_interval:
                    yield "event: heartbeat\ndata: keepalive\n\n"
                    last_heartbeat = time.time()

                time.sleep(3)  # Polling interval

            except DatabaseError as e:
                logger.error(f"Database error: {e}")
                yield f"event: error\ndata: Database error, retrying...\nretry: 10000\n\n"
                time.sleep(10)  # Back off on DB errors

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                yield f"event: error\ndata: Unexpected error, closing connection\n\n"
                break

    response = StreamingHttpResponse(
        event_stream(),
        content_type="text/event-stream"
    )
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Notification

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mark_notification_read(request):
    notification_id = request.data.get("notification_id")
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return Response({"status": "success"})
    except Notification.DoesNotExist:
        return Response({"status": "error", "message": "Notification not found"}, status=404)



# #rating
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
import logging

# Set up logging
logger = logging.getLogger(__name__)

class CustomUserRateThrottle(UserRateThrottle):
    rate = '5/hour'  # Limit to 5 rating submissions per hour per user

class GetUserRating(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, company_id):
        logger.info(f"Fetching rating for company_id: {company_id}, user: {request.user.id}")
        try:
            # Ensure the company exists
            company = Company.objects.get(id=company_id)
            logger.info(f"Company found: {company.company_name}")
        except Company.DoesNotExist:
            logger.error(f"Company with id {company_id} not found")
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            rating = CompanyRating.objects.get(company=company, user=request.user)
            logger.info(f"Rating found: {rating.rating}")
            return Response({"rating": rating.rating}, status=status.HTTP_200_OK)
        except CompanyRating.DoesNotExist:
            logger.info("No rating found for this user and company")
            return Response({"rating": None}, status=status.HTTP_200_OK)

class SubmitCompanyRating(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [CustomUserRateThrottle]

    def post(self, request, company_id):
        logger.info(f"Submitting rating for company_id: {company_id}, user: {request.user.id}")
        try:
            company = Company.objects.get(id=company_id)
            logger.info(f"Company found: {company.company_name}")
        except Company.DoesNotExist:
            logger.error(f"Company with id {company_id} not found")
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        rating_value = request.data.get("rating")

        if not rating_value or not isinstance(rating_value, (int, float)) or rating_value < 1.0 or rating_value > 5.0:
            logger.error(f"Invalid rating value: {rating_value}")
            return Response({"error": "Invalid rating. Must be between 1.0 and 5.0"}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the user has already rated this company
        rating, created = CompanyRating.objects.update_or_create(
            company=company,
            user=user,
            defaults={"rating": rating_value}
        )
        logger.info(f"Rating {'updated' if not created else 'created'}: {rating.rating}")

        # Recalculate the average rating for the company
        average_rating = company.average_rating()
        logger.info(f"Updated average rating: {average_rating}")

        return Response({
            "message": "Rating submitted successfully",
            "average_rating": average_rating
        }, status=status.HTTP_200_OK)






from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Company, CompanyServices, Service, ServiceCategory
import logging

logger = logging.getLogger(__name__)

class SafetyTrainingCompaniesView(APIView):
    def get(self, request):
        try:
            # Find the "Safety and Training Services" category
            safety_category = ServiceCategory.objects.get(name="Safety and Training Services")
            
            # Find services under this category
            safety_services = Service.objects.filter(category=safety_category)
            
            # Find companies that offer these services and are approved
            safety_company_services = CompanyServices.objects.filter(
                service__in=safety_services,
                company__is_approved=True
            ).select_related('company')

            # Extract unique companies
            companies = list({cs.company for cs in safety_company_services})
            
            # Serialize the company data
            company_data = [
                {
                    "id": company.id,
                    "company_name": company.company_name,
                    "company_email": company.company_email,
                    "location": company.location,
                }
                for company in companies
            ]

            return Response(company_data, status=status.HTTP_200_OK)
        except ServiceCategory.DoesNotExist:
            logger.error("Safety and Training Services category not found")
            return Response({"error": "Safety and Training Services category not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in SafetyTrainingCompaniesView: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import Company, Service, ServiceCategory
import logging

logger = logging.getLogger(__name__)

class RequestSafetyTrainingView(APIView):
    def post(self, request, company_id):
        try:
            # Ensure the company exists and is approved
            company = Company.objects.get(id=company_id, is_approved=True)
            
            # Ensure the "Safety and Training Services" category exists
            safety_category = ServiceCategory.objects.get(name="Safety and Training Services")
            
            # Ensure the company offers a service under this category
            safety_service = CompanyServices.objects.filter(
                company=company,
                service__category=safety_category
            ).first()
            
            if not safety_service:
                return Response(
                    {"error": "This company does not offer Safety and Training Services"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract form data
            language_preference = request.data.get("language_preference", "")
            training_date = request.data.get("training_date", "")
            training_time = request.data.get("training_time", "")
            training_agreement = request.data.get("training_agreement", "False") == "True"

            # Basic validation
            if not language_preference or not training_date or not training_time:
                return Response(
                    {"error": "Language preference, training date, and time are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Here you can create an inquiry or a training request
            # For simplicity, we'll assume there's a model to store training requests
            # You can replace this with your actual logic (e.g., creating an inquiry similar to submit-inquiry/)
            # Example: Creating a notification or saving a request
            # For now, we'll just return a success message
            return Response(
                {
                    "message": f"Safety training request for {company.company_name} submitted successfully!",
                    "details": {
                        "language_preference": language_preference,
                        "training_date": training_date,
                        "training_time": training_time,
                        "training_agreement": training_agreement,
                    }
                },
                status=status.HTTP_200_OK
            )

        except Company.DoesNotExist:
            logger.error(f"Company with id {company_id} not found")
            return Response({"error": "Company not found"}, status=status.HTTP_404_NOT_FOUND)
        except ServiceCategory.DoesNotExist:
            logger.error("Safety and Training Services category not found")
            return Response({"error": "Safety and Training Services category not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in RequestSafetyTrainingView: {str(e)}")
            return Response({"error": "An unexpected error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        




# api/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Company
from .serializers import FeaturedCompanySerializer

class FeaturedCompaniesView(APIView):
    def get(self, request):
        # Fetch approved companies, ordered by average rating (descending), limit to top 3
        companies = Company.objects.filter(
            is_approved=True, is_rejected=False
        ).order_by('-ratings__rating')[:3]  # Assuming ratings are related via a ForeignKey
        serializer = FeaturedCompanySerializer(companies, many=True)
        return Response(serializer.data)