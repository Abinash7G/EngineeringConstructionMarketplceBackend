from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import (
    Inquiry, EngineeringConsultingData, BuildingConstructionData,
    PostConstructionMaintenanceData, SafetyTrainingData, Order,
    Company, RentVerification, Subscription, Notification, CustomUser, Appointment, Agreement, Comment, OrderItem, 
)
# signals.py
from django.dispatch import Signal

@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    """Send notifications for order creation (to companies) and status updates (to client only)."""
    company_users = set()
    
    # Collect unique company users associated with order items
    for item in instance.items.all():
        if item.product.company and item.product.company.customuser:
            company_users.add(item.product.company.customuser)

    if created:
        # Notify company users when order is created
        for company_user in company_users:
            Notification.objects.create(
                recipient=company_user,
                message=f"New order #{instance.id} placed for your products.",
                type="order_new"
            )
    else:
        # Notify only the client (user) when status is updated
        if instance.buying_status:
            Notification.objects.create(
                recipient=instance.user,
                message=f"Your order #{instance.id} (buying) status updated to {instance.buying_status}.",
                type="order_buying_status"
            )
        if instance.renting_status:
            Notification.objects.create(
                recipient=instance.user,
                message=f"Your order #{instance.id} (renting) status updated to {instance.renting_status}.",
                type="order_renting_status"
            )

@receiver(post_save, sender=OrderItem)
def send_orderItem_notification(sender, instance, created, **kwargs):
    """Send notifications for order creation (to companies) and status updates (to client only)."""
    if created:
        # Notify company users when order is created
        Notification.objects.create(
            recipient=instance.product.company.customuser,
            message=f"New order #{instance.id} placed for your products.",
            type="order_new"
            )



import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Order, Notification

# Set up logging
logger = logging.getLogger(__name__)

@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    """Send notifications for order creation (to companies) and status updates (to clients)."""
    logger.info(f"Order signal triggered for order ID: {instance.id}, created: {created}")

    # Step 1: Handle order creation notifications (to companies)
    if created:
        company_users = set()

        # Try PaymentDistribution first (more reliable for company identification)
        logger.info(f"Checking PaymentDistribution for order {instance.id}")
        for payment_distribution in instance.payment_distributions.all():
            try:
                if not payment_distribution.company:
                    logger.warning(f"PaymentDistribution {payment_distribution.id} in order {instance.id} has no company")
                    continue
                if not payment_distribution.company.customuser:
                    logger.warning(f"Company {payment_distribution.company.id} in PaymentDistribution has no customuser")
                    continue
                company_users.add(payment_distribution.company.customuser)
                logger.info(f"Added company user {payment_distribution.company.customuser.email} via PaymentDistribution")
            except Exception as e:
                logger.error(f"Error processing PaymentDistribution {payment_distribution.id}: {str(e)}")
                continue

        # Fallback to OrderItem if no company users found
        if not company_users:
            logger.info(f"No company users found via PaymentDistribution for order {instance.id}, checking OrderItem")
            for item in instance.items.all():
                try:
                    if not item.product:
                        logger.warning(f"Order item {item.id} in order {instance.id} has no product")
                        continue
                    if not item.product.company:
                        logger.warning(f"Product {item.product.id} in order {instance.id} has no company")
                        continue
                    if not item.product.company.customuser:
                        logger.warning(f"Company {item.product.company.id} for product {item.product.id} has no customuser")
                        continue
                    company_users.add(item.product.company.customuser)
                    logger.info(f"Added company user {item.product.company.customuser.email} via OrderItem")
                except Exception as e:
                    logger.error(f"Error processing order item {item.id} in order {instance.id}: {str(e)}")
                    continue

        # Send notifications to company users
        if not company_users:
            logger.error(f"No company users found to notify for order {instance.id}")
        else:
            for company_user in company_users:
                try:
                    notification = Notification.objects.create(
                        recipient=company_user,
                        message=f"New order #{instance.id} placed for your products.",
                        type="order_new"
                    )
                    logger.info(f"Notification created for {company_user.email}, order {instance.id}, notification ID: {notification.id}")
                except Exception as e:
                    logger.error(f"Failed to create notification for {company_user.email}, order {instance.id}: {str(e)}")

    # Step 2: Handle status update notifications (to client)
    else:
        try:
            if instance.buying_status:
                notification = Notification.objects.create(
                    recipient=instance.user,
                    message=f"Your order #{instance.id} (buying) status updated to {instance.buying_status}.",
                    type="order_buying_status"
                )
                logger.info(f"Buying status notification for {instance.user.email}, order {instance.id}, notification ID: {notification.id}")
            if instance.renting_status:
                notification = Notification.objects.create(
                    recipient=instance.user,
                    message=f"Your order #{instance.id} (renting) status updated to {instance.renting_status}.",
                    type="order_renting_status"
                )
                logger.info(f"Renting status notification for {instance.user.email}, order {instance.id}, notification ID: {notification.id}")
        except Exception as e:
            logger.error(f"Failed to create status notification for {instance.user.email}, order {instance.id}: {str(e)}")








import logging
# Set up logging to debug signal issues
logger = logging.getLogger(__name__)
# Admin Notifications for Company Registration
@receiver(post_save, sender=Company)
def send_company_notification(sender, instance, created, **kwargs):
    """Send notification to all Platform Admins when a new company is registered."""
    logger.info(f"Company signal triggered for company: {instance.company_name}, created: {created}")
    
    if created:
        try:
            platform_admins = CustomUser.objects.filter(is_superuser=True)
            if not platform_admins.exists():
                logger.error(f"No Platform Admin (is_superuser=True) found for company: {instance.company_name}")
                return

            for admin in platform_admins:
                logger.info(f"Sending notification to Platform Admin: {admin.email}")
                notification = Notification.objects.create(
                    recipient=admin,
                    message=f"The registration form for  {instance.company_name} {instance.company_type} has been submitted.",
                    type="company_registration"
                )
                logger.info(f"Notification created for company: {instance.company_name}, admin: {admin.email}, notification ID: {notification.id}")
        except Exception as e:
            logger.error(f"Error creating notification for company: {instance.company_name}, error: {str(e)}")

# # Admin Notifications for  Subscription
@receiver(post_save, sender=Subscription)
def send_subscription_notification(sender, instance, created, **kwargs):
    """Send notification to all Platform Admins when a company creates a subscription."""
    logger.info(f"Subscription signal triggered for company: {instance.company.company_name}, plan: {instance.plan}, created: {created}")
    
    if created:
        try:
            platform_admins = CustomUser.objects.filter(is_superuser=True)
            if not platform_admins.exists():
                logger.error(f"No Platform Admin (is_superuser=True) found for subscription by company: {instance.company.company_name}")
                return

            for admin in platform_admins:
                logger.info(f"Sending subscription notification to Platform Admin: {admin.email}")
                notification = Notification.objects.create(
                    recipient=admin,
                    message=f"{instance.company.company_name} has subscribed to the {instance.plan} plan.",
                    type="subscription_new"
                )
                logger.info(f"Subscription notification created for company: {instance.company.company_name}, admin: {admin.email}, notification ID: {notification.id}")
        except Exception as e:
            logger.error(f"Error creating subscription notification for company: {instance.company.company_name}, error: {str(e)}")


@receiver(post_save, sender=RentVerification)
def send_verification_notification(sender, instance, created, **kwargs):
    """Send notifications for rent verification: to Platform Admins on creation, to user on status update."""
    logger.info(f"Rent verification signal triggered for user: {instance.full_name}, status: {instance.status}, created: {created}")
    
    if created:
        # Notify Platform Admins when a rent verification is submitted
        try:
            platform_admins = CustomUser.objects.filter(is_superuser=True)
            if not platform_admins.exists():
                logger.error(f"No Platform Admin (is_superuser=True) found for rent verification by user: {instance.full_name}")
                return

            for admin in platform_admins:
                logger.info(f"Sending rent verification notification to Platform Admin: {admin.email}")
                notification = Notification.objects.create(
                    recipient=admin,
                    message=f"New rent verification request from {instance.full_name}.",
                    type="rent_verification_new"
                )
                logger.info(f"Rent verification notification created for user: {instance.full_name}, admin: {admin.email}, notification ID: {notification.id}")
        except Exception as e:
            logger.error(f"Error creating rent verification notification for user: {instance.full_name}, error: {str(e)}")
    else:
        # Notify the user when the status is updated
        try:
            user = CustomUser.objects.filter(email=instance.email).first()
            if user and 'status' in kwargs.get('update_fields', []):
                logger.info(f"Sending status update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your rent verification request is now {instance.status}.",
                    type="rent_verification_status"
                )
                logger.info(f"Status update notification created for user: {user.email}, notification ID: {notification.id}")
            elif not user:
                logger.warning(f"No CustomUser found with email: {instance.email} for status update notification")
        except Exception as e:
            logger.error(f"Error creating status update notification for user email: {instance.email}, error: {str(e)}")


# #inquary
# @receiver(post_save, sender=Inquiry)
# def send_inquiry_notification(sender, instance, created, **kwargs):
#     """Send notification to the company when a new inquiry is created."""
#     logger.info(f"Inquiry signal triggered for inquiry ID: {instance.id}, company: {instance.company.company_name}, created: {created}")
    
#     if created:
#         try:
#             company_user = instance.company.customuser
#             if not company_user:
#                 logger.error(f"No CustomUser associated with company: {instance.company.company_name} for inquiry ID: {instance.id}")
#                 return

#             logger.info(f"Sending inquiry notification to company user: {company_user.email}")
#             notification = Notification.objects.create(
#                 recipient=company_user,
#                 message=f"New inquiry #{instance.id} from {instance.full_name} for {instance.category} - {instance.sub_service}.",
#                 type="inquiry_new"
#             )
#             logger.info(f"Inquiry notification created for company: {instance.company.company_name}, user: {company_user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating inquiry notification for company: {instance.company.company_name}, error: {str(e)}")

# #111
# # Comment notifications (creation and response)
# @receiver(post_save, sender=Comment)
# def send_comment_notification(sender, instance, created, **kwargs):
#     """Send notifications for comment creation and company response."""
#     logger.info(f"Comment signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     inquiry = instance.inquiry
#     user = inquiry.user
#     company_user = inquiry.company.customuser

#     if not user or not company_user:
#         logger.error(f"Missing user or company user for comment on inquiry ID: {instance.inquiry.id}")
#         return

#     try:
#         if created:
#             # Comment creation
#             if instance.created_by == user:
#                 # User commented, notify company
#                 logger.info(f"Sending comment notification to company user: {company_user.email}")
#                 notification = Notification.objects.create(
#                     recipient=company_user,
#                     message=f"New comment on inquiry #{inquiry.id} from {inquiry.full_name}: {instance.comment_text[:50]}...",
#                     type="comment_user"
#                 )
#                 logger.info(f"Comment notification created for company: {inquiry.company.company_name}, user: {company_user.email}, notification ID: {notification.id}")
#             elif instance.created_by == company_user:
#                 # Company commented, notify user
#                 logger.info(f"Sending comment notification to user: {user.email}")
#                 notification = Notification.objects.create(
#                     recipient=user,
#                     message=f"New comment on your inquiry #{inquiry.id} from {inquiry.company.company_name}: {instance.comment_text[:50]}...",
#                     type="comment_company"
#                 )
#                 logger.info(f"Comment notification created for user: {user.email}, notification ID: {notification.id}")
#             else:
#                 logger.warning(f"Comment creator {instance.created_by} does not match user or company user for inquiry ID: {inquiry.id}")
#         else:
#             # Check for company response update
#             update_fields = kwargs.get('update_fields', set())
#             if 'company_response' in update_fields and instance.company_response:
#                 # Company added a response, notify user
#                 logger.info(f"Sending comment response notification to user: {user.email}")
#                 notification = Notification.objects.create(
#                     recipient=user,
#                     message=f"{inquiry.company.company_name} responded to your comment on inquiry #{inquiry.id}: {instance.company_response[:50]}...",
#                     type="comment_response"
#                 )
#                 logger.info(f"Comment response notification created for user: {user.email}, notification ID: {notification.id}")
#     except Exception as e:
#         logger.error(f"Error creating comment notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")
#         ###11
# ###444
# Dictionary to store previous values of Comment fields
previous_comment_values = {}

@receiver(pre_save, sender=Comment)
def store_previous_comment_values(sender, instance, **kwargs):
    """Store the previous value of company_response before saving."""
    try:
        # Fetch the existing instance from the database
        existing = Comment.objects.get(id=instance.id)
        previous_comment_values[instance.id] = {
            'company_response': existing.company_response,
        }
    except Comment.DoesNotExist:
        # If the instance doesn't exist (i.e., it's being created), set defaults
        previous_comment_values[instance.id] = {
            'company_response': None,
        }
    except Exception as e:
        logger.error(f"Error in pre_save for Comment ID: {instance.id}, error: {str(e)}")

# Comment notifications (creation and response)
@receiver(post_save, sender=Comment)
def send_comment_notification(sender, instance, created, **kwargs):
    """Send notifications for comment creation and company response."""
    logger.info(f"Comment signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
    inquiry = instance.inquiry
    user = inquiry.user
    company_user = inquiry.company.customuser

    if not user or not company_user:
        logger.error(f"Missing user or company user for comment on inquiry ID: {instance.inquiry.id}")
        return

    try:
        if created:
            # Comment creation
            if instance.created_by == user:
                # User commented, notify company
                logger.info(f"Sending comment notification to company user: {company_user.email}")
                notification = Notification.objects.create(
                    recipient=company_user,
                    message=f"New comment on inquiry #{inquiry.id} from {inquiry.full_name}: {instance.comment_text[:50]}...",
                    type="comment_user"
                )
                logger.info(f"Comment notification created for company: {inquiry.company.company_name}, user: {company_user.email}, notification ID: {notification.id}")
            elif instance.created_by == company_user:
                # Company commented, notify user
                logger.info(f"Sending comment notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"New comment on your inquiry #{inquiry.id} from {inquiry.company.company_name}: {instance.comment_text[:50]}...",
                    type="comment_company"
                )
                logger.info(f"Comment notification created for user: {user.email}, notification ID: {notification.id}")
            else:
                logger.warning(f"Comment creator {instance.created_by} does not match user or company user for inquiry ID: {inquiry.id}")
        else:
            # Check for company response update
            previous_values = previous_comment_values.get(instance.id, {'company_response': None})
            previous_company_response = previous_values['company_response']

            if instance.company_response != previous_company_response and instance.company_response:
                # Company added or updated a response, notify user
                logger.info(f"Sending comment response notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"{inquiry.company.company_name} responded to your comment on inquiry #{inquiry.id}: {instance.company_response[:50]}...",
                    type="comment_response"
                )
                logger.info(f"Comment response notification created for user: {user.email}, notification ID: {notification.id}")

        # Clean up the stored previous values
        previous_comment_values.pop(instance.id, None)

    except Exception as e:
        logger.error(f"Error creating comment notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")

# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver
# from django.contrib.auth.models import Group
# from .models import (
#     Inquiry, EngineeringConsultingData, BuildingConstructionData,
#     PostConstructionMaintenanceData, SafetyTrainingData, Order,
#     Company, RentVerification, Subscription, Notification, CustomUser, Appointment, Agreement, Comment
# )
# # signals.py
# from django.dispatch import Signal

# @receiver(post_save, sender=Order)
# def send_order_notification(sender, instance, created, **kwargs):
#     """Send notifications for order creation (to companies) and status updates (to client only)."""
#     company_users = set()
    
#     # Collect unique company users associated with order items
#     for item in instance.items.all():
#         if item.product.company and item.product.company.customuser:
#             company_users.add(item.product.company.customuser)

#     if created:
#         # Notify company users when order is created
#         for company_user in company_users:
#             Notification.objects.create(
#                 recipient=company_user,
#                 message=f"New order #{instance.id} placed for your products.",
#                 type="order_new"
#             )
#     else:
#         # Notify only the client (user) when status is updated
#         if instance.buying_status:
#             Notification.objects.create(
#                 recipient=instance.user,
#                 message=f"Your order #{instance.id} (buying) status updated to {instance.buying_status}.",
#                 type="order_buying_status"
#             )
#         if instance.renting_status:
#             Notification.objects.create(
#                 recipient=instance.user,
#                 message=f"Your order #{instance.id} (renting) status updated to {instance.renting_status}.",
#                 type="order_renting_status"
#             )


# import logging
# # Set up logging to debug signal issues
# logger = logging.getLogger(__name__)
# # Admin Notifications for Company Registration
# @receiver(post_save, sender=Company)
# def send_company_notification(sender, instance, created, **kwargs):
#     """Send notification to all Platform Admins when a new company is registered."""
#     logger.info(f"Company signal triggered for company: {instance.company_name}, created: {created}")
    
#     if created:
#         try:
#             platform_admins = CustomUser.objects.filter(is_superuser=True)
#             if not platform_admins.exists():
#                 logger.error(f"No Platform Admin (is_superuser=True) found for company: {instance.company_name}")
#                 return

#             for admin in platform_admins:
#                 logger.info(f"Sending notification to Platform Admin: {admin.email}")
#                 notification = Notification.objects.create(
#                     recipient=admin,
#                     message=f"The registration form for  {instance.company_name} {instance.company_type} has been submitted.",
#                     type="company_registration"
#                 )
#                 logger.info(f"Notification created for company: {instance.company_name}, admin: {admin.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating notification for company: {instance.company_name}, error: {str(e)}")

# # Admin Notifications for Subscription
# @receiver(post_save, sender=Subscription)
# def send_subscription_notification(sender, instance, created, **kwargs):
#     """Send notification to all Platform Admins when a company creates a subscription."""
#     logger.info(f"Subscription signal triggered for company: {instance.company.company_name}, plan: {instance.plan}, created: {created}")
    
#     if created:
#         try:
#             platform_admins = CustomUser.objects.filter(is_superuser=True)
#             if not platform_admins.exists():
#                 logger.error(f"No Platform Admin (is_superuser=True) found for subscription by company: {instance.company.company_name}")
#                 return

#             for admin in platform_admins:
#                 logger.info(f"Sending subscription notification to Platform Admin: {admin.email}")
#                 notification = Notification.objects.create(
#                     recipient=admin,
#                     message=f"{instance.company.company_name} has subscribed to the {instance.plan} plan.",
#                     type="subscription_new"
#                 )
#                 logger.info(f"Subscription notification created for company: {instance.company.company_name}, admin: {admin.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating subscription notification for company: {instance.company.company_name}, error: {str(e)}")


# @receiver(post_save, sender=RentVerification)
# def send_verification_notification(sender, instance, created, **kwargs):
#     """Send notifications for rent verification: to Platform Admins on creation, to user on status update."""
#     logger.info(f"Rent verification signal triggered for user: {instance.full_name}, status: {instance.status}, created: {created}")
    
#     if created:
#         # Notify Platform Admins when a rent verification is submitted
#         try:
#             platform_admins = CustomUser.objects.filter(is_superuser=True)
#             if not platform_admins.exists():
#                 logger.error(f"No Platform Admin (is_superuser=True) found for rent verification by user: {instance.full_name}")
#                 return

#             for admin in platform_admins:
#                 logger.info(f"Sending rent verification notification to Platform Admin: {admin.email}")
#                 notification = Notification.objects.create(
#                     recipient=admin,
#                     message=f"New rent verification request from {instance.full_name}.",
#                     type="rent_verification_new"
#                 )
#                 logger.info(f"Rent verification notification created for user: {instance.full_name}, admin: {admin.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating rent verification notification for user: {instance.full_name}, error: {str(e)}")
#     else:
#         # Notify the user when the status is updated
#         try:
#             user = CustomUser.objects.filter(email=instance.email).first()
#             if user and 'status' in kwargs.get('update_fields', []):
#                 logger.info(f"Sending status update notification to user: {user.email}")
#                 notification = Notification.objects.create(
#                     recipient=user,
#                     message=f"Your rent verification request is now {instance.status}.",
#                     type="rent_verification_status"
#                 )
#                 logger.info(f"Status update notification created for user: {user.email}, notification ID: {notification.id}")
#             elif not user:
#                 logger.warning(f"No CustomUser found with email: {instance.email} for status update notification")
#         except Exception as e:
#             logger.error(f"Error creating status update notification for user email: {instance.email}, error: {str(e)}")


# Dictionary to store previous values of Inquiry fields
previous_inquiry_values = {}

@receiver(pre_save, sender=Inquiry)
def store_previous_inquiry_values(sender, instance, **kwargs):
    """Store the previous values of status and certificate before saving."""
    try:
        # Fetch the existing instance from the database
        existing = Inquiry.objects.get(id=instance.id)
        previous_inquiry_values[instance.id] = {
            'status': existing.status,
            'certificate': existing.certificate,
        }
    except Inquiry.DoesNotExist:
        # If the instance doesn't exist (i.e., it's being created), set defaults
        previous_inquiry_values[instance.id] = {
            'status': None,
            'certificate': None,
        }
    except Exception as e:
        logger.error(f"Error in pre_save for Inquiry ID: {instance.id}, error: {str(e)}")

# Inquiry Notifications
@receiver(post_save, sender=Inquiry)
def send_inquiry_notification(sender, instance, created, **kwargs):
    """Send notification to the company when a new inquiry is created and handle status/certificate updates."""
    logger.info(f"Inquiry signal triggered for inquiry ID: {instance.id}, company: {instance.company.company_name}, created: {created}")
    
    if created:
        try:
            company_user = instance.company.customuser
            if not company_user:
                logger.error(f"No CustomUser associated with company: {instance.company.company_name} for inquiry ID: {instance.id}")
                return

            logger.info(f"Sending inquiry notification to company user: {company_user.email}")
            notification = Notification.objects.create(
                recipient=company_user,
                message=f"New inquiry #{instance.id} from {instance.full_name} for {instance.category} - {instance.sub_service}.",
                type="inquiry_new"
            )
            logger.info(f"Inquiry notification created for company: {instance.company.company_name}, user: {company_user.email}, notification ID: {notification.id}")
        except Exception as e:
            logger.error(f"Error creating inquiry notification for company: {instance.company.company_name}, error: {str(e)}")
    else:
        # Handle status and certificate updates
        try:
            user = instance.user
            if not user:
                logger.error(f"No user associated with inquiry ID: {instance.id} for status/certificate update notification")
                return

            # Get previous values
            previous_values = previous_inquiry_values.get(instance.id, {'status': None, 'certificate': None})
            previous_status = previous_values['status']
            previous_certificate = previous_values['certificate']

            # Status update notification
            if instance.status != previous_status and instance.status:
                logger.info(f"Sending status update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{instance.id} status updated to {instance.status} by {instance.company.company_name}.",
                    type="inquiry_status"
                )
                logger.info(f"Status update notification created for user: {user.email}, notification ID: {notification.id}")

            # Certificate upload notification for Safety and Training Services
            if instance.category == 'Safety and Training Services' and instance.certificate != previous_certificate and instance.certificate:
                logger.info(f"Sending certificate upload notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"A certificate for your inquiry #{instance.id} has been uploaded by {instance.company.company_name}.",
                    type="inquiry_certificate_upload"
                )
                logger.info(f"Certificate upload notification created for user: {user.email}, notification ID: {notification.id}")

            # Clean up the stored previous values
            previous_inquiry_values.pop(instance.id, None)
        except Exception as e:
            logger.error(f"Error creating status/certificate notification for inquiry ID: {instance.id}, error: {str(e)}")


# # Comment notifications (creation and response)
# @receiver(post_save, sender=Comment)
# def send_comment_notification(sender, instance, created, **kwargs):
#     """Send notifications for comment creation and company response."""
#     logger.info(f"Comment signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     inquiry = instance.inquiry
#     user = inquiry.user
#     company_user = inquiry.company.customuser

#     if not user or not company_user:
#         logger.error(f"Missing user or company user for comment on inquiry ID: {instance.inquiry.id}")
#         return

#     try:
#         if created:
#             # Comment creation
#             if instance.created_by == user:
#                 # User commented, notify company
#                 logger.info(f"Sending comment notification to company user: {company_user.email}")
#                 notification = Notification.objects.create(
#                     recipient=company_user,
#                     message=f"New comment on inquiry #{inquiry.id} from {inquiry.full_name}: {instance.comment_text[:50]}...",
#                     type="comment_user"
#                 )
#                 logger.info(f"Comment notification created for company: {inquiry.company.company_name}, user: {company_user.email}, notification ID: {notification.id}")
#             elif instance.created_by == company_user:
#                 # Company commented, notify user
#                 logger.info(f"Sending comment notification to user: {user.email}")
#                 notification = Notification.objects.create(
#                     recipient=user,
#                     message=f"New comment on your inquiry #{inquiry.id} from {inquiry.company.company_name}: {instance.comment_text[:50]}...",
#                     type="comment_company"
#                 )
#                 logger.info(f"Comment notification created for user: {user.email}, notification ID: {notification.id}")
#             else:
#                 logger.warning(f"Comment creator {instance.created_by} does not match user or company user for inquiry ID: {inquiry.id}")
#         else:
#             # Check for company response update
#             update_fields = kwargs.get('update_fields', set())
#             if 'company_response' in update_fields and instance.company_response:
#                 # Company added a response, notify user
#                 logger.info(f"Sending comment response notification to user: {user.email}")
#                 notification = Notification.objects.create(
#                     recipient=user,
#                     message=f"{inquiry.company.company_name} responded to your comment on inquiry #{inquiry.id}: {instance.company_response[:50]}...",
#                     type="comment_response"
#                 )
#                 logger.info(f"Comment response notification created for user: {user.email}, notification ID: {notification.id}")
#     except Exception as e:
#         logger.error(f"Error creating comment notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")


# Notifications for updates to associated models (EngineeringConsultingData, PostConstructionMaintenanceData, SafetyTrainingData, Appointment)
@receiver(post_save, sender=EngineeringConsultingData)
@receiver(post_save, sender=PostConstructionMaintenanceData)
@receiver(post_save, sender=SafetyTrainingData)
@receiver(post_save, sender=Appointment)
def send_associated_model_update_notification(sender, instance, created, **kwargs):
    """Send notification to user when associated model (EngineeringConsultingData, PostConstructionMaintenanceData, SafetyTrainingData, Appointment) is created or updated."""
    model_name = sender.__name__
    logger.info(f"{model_name} signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
    try:
        inquiry = instance.inquiry
        user = inquiry.user
        company_user = inquiry.company.customuser

        if not user:
            logger.error(f"No user associated with inquiry ID: {inquiry.id} for {model_name} update notification")
            return
        if not company_user:
            logger.error(f"No company user associated with inquiry ID: {inquiry.id} for {model_name} update notification")
            return

        action = "created" if created else "updated"
        message = f"Your inquiry #{inquiry.id} has a new {model_name} {action} by {inquiry.company.company_name}."

        if model_name == "Appointment" and instance.status:
            message += f" Appointment status: {instance.status}."

        logger.info(f"Sending {model_name} {action} notification to user: {user.email}")
        notification = Notification.objects.create(
            recipient=user,
            message=message,
            type=f"{model_name.lower()}_{action}"
        )
        logger.info(f"{model_name} {action} notification created for user: {user.email}, notification ID: {notification.id}")
    except AttributeError as e:
        logger.error(f"AttributeError in {model_name} signal for inquiry ID: {getattr(instance, 'inquiry_id', 'unknown')}, error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating {model_name} notification for inquiry ID: {getattr(instance, 'inquiry_id', 'unknown')}, error: {str(e)}")


# Dictionary to store previous values of BuildingConstructionData fields
previous_building_construction_values = {}

@receiver(pre_save, sender=BuildingConstructionData)
def store_previous_building_construction_values(sender, instance, **kwargs):
    """Store the previous values of relevant BuildingConstructionData fields before saving."""
    try:
        # Fetch the existing instance from the database
        existing = BuildingConstructionData.objects.get(id=instance.id)
        previous_building_construction_values[instance.id] = {
            'permit_status': existing.permit_status,
            'construction_phase': existing.construction_phase,
            'progress_percentage': existing.progress_percentage,
            'progress_photos': existing.progress_photos,
            'inspection_reports': existing.inspection_reports,
            'completion_certificate': existing.completion_certificate,
        }
    except BuildingConstructionData.DoesNotExist:
        # If the instance doesn't exist (i.e., it's being created), set defaults
        previous_building_construction_values[instance.id] = {
            'permit_status': None,
            'construction_phase': None,
            'progress_percentage': None,
            'progress_photos': None,
            'inspection_reports': None,
            'completion_certificate': None,
        }
    except Exception as e:
        logger.error(f"Error in pre_save for BuildingConstructionData ID: {instance.id}, error: {str(e)}")

# Specific notifications for BuildingConstructionData updates
@receiver(post_save, sender=BuildingConstructionData)
def send_building_construction_notification(sender, instance, created, **kwargs):
    """Send specific notifications for BuildingConstructionData creation and updates."""
    logger.info(f"BuildingConstructionData signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
    try:
        inquiry = instance.inquiry
        user = inquiry.user
        company_user = inquiry.company.customuser

        if not user:
            logger.error(f"No user associated with inquiry ID: {inquiry.id} for BuildingConstructionData update notification")
            return
        if not company_user:
            logger.error(f"No company user associated with inquiry ID: {inquiry.id} for BuildingConstructionData update notification")
            return

        # Get previous values
        previous_values = previous_building_construction_values.get(instance.id, {
            'permit_status': None,
            'construction_phase': None,
            'progress_percentage': None,
            'progress_photos': None,
            'inspection_reports': None,
            'completion_certificate': None,
        })
        previous_permit_status = previous_values['permit_status']
        previous_construction_phase = previous_values['construction_phase']
        previous_progress_percentage = previous_values['progress_percentage']
        previous_progress_photos = previous_values['progress_photos']
        previous_inspection_reports = previous_values['inspection_reports']
        previous_completion_certificate = previous_values['completion_certificate']

        if created:
            # Notify user on creation
            logger.info(f"Sending BuildingConstructionData creation notification to user: {user.email}")
            notification = Notification.objects.create(
                recipient=user,
                message=f"Your inquiry #{inquiry.id} has a new BuildingConstructionData created by {inquiry.company.company_name}.",
                type="buildingconstructiondata_created"
            )
            logger.info(f"BuildingConstructionData creation notification created for user: {user.email}, notification ID: {notification.id}")
        else:
            # Specific notifications for updated fields
            if instance.permit_status != previous_permit_status and instance.permit_status:
                logger.info(f"Sending permit status update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} permit status updated to {instance.permit_status} by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_permit_status"
                )
                logger.info(f"Permit status notification created for user: {user.email}, notification ID: {notification.id}")

            if instance.construction_phase != previous_construction_phase and instance.construction_phase:
                logger.info(f"Sending construction phase update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} construction phase updated to {instance.construction_phase} by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_construction_phase"
                )
                logger.info(f"Construction phase notification created for user: {user.email}, notification ID: {notification.id}")

            if instance.progress_percentage != previous_progress_percentage and instance.progress_percentage is not None:
                logger.info(f"Sending progress percentage update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} construction progress updated to {instance.progress_percentage}% by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_progress_percentage"
                )
                logger.info(f"Progress percentage notification created for user: {user.email}, notification ID: {notification.id}")

            if instance.progress_photos != previous_progress_photos and instance.progress_photos:
                logger.info(f"Sending progress photos update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} has new progress photos uploaded by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_progress_photos"
                )
                logger.info(f"Progress photos notification created for user: {user.email}, notification ID: {notification.id}")

            if instance.inspection_reports != previous_inspection_reports and instance.inspection_reports:
                logger.info(f"Sending inspection reports update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} has new inspection reports uploaded by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_inspection_reports"
                )
                logger.info(f"Inspection reports notification created for user: {user.email}, notification ID: {notification.id}")

            if instance.completion_certificate != previous_completion_certificate and instance.completion_certificate:
                logger.info(f"Sending completion certificate update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} has a new completion certificate uploaded by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_completion_certificate"
                )
                logger.info(f"Completion certificate notification created for user: {user.email}, notification ID: {notification.id}")

        # Clean up the stored previous values
        previous_building_construction_values.pop(instance.id, None)

    except AttributeError as e:
        logger.error(f"AttributeError in BuildingConstructionData signal for inquiry ID: {getattr(instance, 'inquiry_id', 'unknown')}, error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating BuildingConstructionData notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")



