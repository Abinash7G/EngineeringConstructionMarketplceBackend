from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import (
    Inquiry, EngineeringConsultingData, BuildingConstructionData,
    PostConstructionMaintenanceData, SafetyTrainingData, Order,
    Company, RentVerification, Subscription, Notification, CustomUser, Appointment, Agreement, Comment
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

# @receiver(post_save, sender=Inquiry)
# def send_inquiry_notification(sender, instance, created, **kwargs):
#     """Send notification to the company when an inquiry is submitted."""
#     logger.info(f"Inquiry signal triggered for inquiry ID: {instance.id}, created: {created}")
    
#     if created:
#         try:
#             company_user = instance.company.customuser
#             if company_user:
#                 logger.info(f"Sending inquiry notification to company user: {company_user.email}")
#                 notification = Notification.objects.create(
#                     recipient=company_user,
#                     message=f"New inquiry from {instance.full_name} for {instance.sub_service}.",
#                     type="inquiry_new"
#                 )
#                 logger.info(f"Inquiry notification created for company: {instance.company.company_name}, notification ID: {notification.id}")
#             else:
#                 logger.warning(f"No company user found for company: {instance.company.company_name}")
#         except Exception as e:
#             logger.error(f"Error creating inquiry notification for company: {instance.company.company_name}, error: {str(e)}")


# @receiver(post_save, sender=Inquiry)
# def send_inquiry_notification(sender, instance, created, **kwargs):
#     """Send notification to the company when an inquiry is submitted."""
#     logger.info(f"Inquiry signal triggered for inquiry ID: {instance.id}, created: {created}")
    
#     if created:
#         try:
#             company_user = instance.company.customuser
#             if company_user:
#                 logger.info(f"Sending inquiry notification to company user: {company_user.email}")
#                 notification = Notification.objects.create(
#                     recipient=company_user,
#                     message=f"New inquiry from {instance.full_name} for {instance.sub_service}.",
#                     type="inquiry_new"
#                 )
#                 logger.info(f"Inquiry notification created for company: {instance.company.company_name}, notification ID: {notification.id}")
#             else:
#                 logger.warning(f"No company user found for company: {instance.company.company_name}")
#         except Exception as e:
#             logger.error(f"Error creating inquiry notification for company: {instance.company.company_name}, error: {str(e)}")

# @receiver(post_save, sender=Appointment)
# def send_appointment_notification(sender, instance, created, **kwargs):
#     """Send notification to the user when an appointment is rescheduled."""
#     logger.info(f"Appointment signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if not created and 'appointment_date' in kwargs.get('update_fields', []):
#         try:
#             user = instance.inquiry.user
#             logger.info(f"Sending reschedule notification to user: {user.email}")
#             notification = Notification.objects.create(
#                 recipient=user,
#                 message="Check your email: Your appointment has been rescheduled.",
#                 type="appointment_rescheduled"
#             )
#             logger.info(f"Reschedule notification created for user: {user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating reschedule notification for user email: {instance.inquiry.email}, error: {str(e)}")

# @receiver(post_save, sender=Comment)
# def send_comment_notification(sender, instance, created, **kwargs):
#     """Send notifications for comments: user to company, company to user."""
#     logger.info(f"Comment signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if created:
#         # User added a comment, notify the company
#         try:
#             company_user = instance.company.customuser
#             if company_user:
#                 logger.info(f"Sending comment notification to company user: {company_user.email}")
#                 notification = Notification.objects.create(
#                     recipient=company_user,
#                     message=f"New comment on inquiry #{instance.inquiry.id} by {instance.created_by.username if instance.created_by else 'Unknown'}.",
#                     type="comment_new"
#                 )
#                 logger.info(f"Comment notification created for company: {instance.company.company_name}, notification ID: {notification.id}")
#             else:
#                 logger.warning(f"No company user found for company: {instance.company.company_name}")
#         except Exception as e:
#             logger.error(f"Error creating comment notification for company: {instance.company.company_name}, error: {str(e)}")
#     else:
#         # Company responded to the comment, notify the user
#         if 'company_response' in kwargs.get('update_fields', []):
#             try:
#                 user = instance.created_by
#                 if user:
#                     logger.info(f"Sending comment response notification to user: {user.email}")
#                     notification = Notification.objects.create(
#                         recipient=user,
#                         message=f"New response to your comment on inquiry #{instance.inquiry.id}.",
#                         type="comment_response"
#                     )
#                     logger.info(f"Comment response notification created for user: {user.email}, notification ID: {notification.id}")
#                 else:
#                     logger.warning(f"No user found for comment on inquiry ID: {instance.inquiry.id}")
#             except Exception as e:
#                 logger.error(f"Error creating comment response notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")

# @receiver(post_save, sender=Agreement)
# def send_agreement_notification(sender, instance, created, **kwargs):
#     """Send notification to the user when the company updates an agreement."""
#     logger.info(f"Agreement signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if not created:
#         try:
#             user = instance.user
#             logger.info(f"Sending agreement update notification to user: {user.email}")
#             notification = Notification.objects.create(
#                 recipient=user,
#                 message=f"New agreement update for inquiry #{instance.inquiry.id}.",
#                 type="agreement_update"
#             )
#             logger.info(f"Agreement update notification created for user: {user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating agreement update notification for user email: {instance.user.email}, error: {str(e)}")

# # Service Data Notifications
# @receiver(post_save, sender=BuildingConstructionData)
# def send_building_construction_notification(sender, instance, created, **kwargs):
#     """Send notification to the user when BuildingConstructionData is updated by the company."""
#     logger.info(f"BuildingConstructionData signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if not created:
#         try:
#             user = instance.inquiry.user
#             logger.info(f"Sending update notification to user: {user.email}")
#             notification = Notification.objects.create(
#                 recipient=user,
#                 message=f"Your Building Construction inquiry #{instance.inquiry.id} has been updated.",
#                 type="building_construction_update"
#             )
#             logger.info(f"BuildingConstructionData update notification created for user: {user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating BuildingConstructionData update notification for user email: {instance.inquiry.email}, error: {str(e)}")

# @receiver(post_save, sender=EngineeringConsultingData)
# def send_engineering_consulting_notification(sender, instance, created, **kwargs):
#     """Send notification to the user when EngineeringConsultingData is updated by the company."""
#     logger.info(f"EngineeringConsultingData signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if not created:
#         try:
#             user = instance.inquiry.user
#             logger.info(f"Sending update notification to user: {user.email}")
#             notification = Notification.objects.create(
#                 recipient=user,
#                 message=f"Your Engineering Consulting inquiry #{instance.inquiry.id} has been updated.",
#                 type="engineering_consulting_update"
#             )
#             logger.info(f"EngineeringConsultingData update notification created for user: {user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating EngineeringConsultingData update notification for user email: {instance.inquiry.email}, error: {str(e)}")

# @receiver(post_save, sender=PostConstructionMaintenanceData)
# def send_maintenance_notification(sender, instance, created, **kwargs):
#     """Send notification to the user when PostConstructionMaintenanceData is updated by the company."""
#     logger.info(f"PostConstructionMaintenanceData signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if not created:
#         try:
#             user = instance.inquiry.user
#             logger.info(f"Sending update notification to user: {user.email}")
#             notification = Notification.objects.create(
#                 recipient=user,
#                 message=f"Your Post-Construction Maintenance inquiry #{instance.inquiry.id} has been updated.",
#                 type="maintenance_update"
#             )
#             logger.info(f"PostConstructionMaintenanceData update notification created for user: {user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating PostConstructionMaintenanceData update notification for user email: {instance.inquiry.email}, error: {str(e)}")

# @receiver(post_save, sender=SafetyTrainingData)
# def send_training_notification(sender, instance, created, **kwargs):
#     """Send notification to the user when SafetyTrainingData is updated by the company."""
#     logger.info(f"SafetyTrainingData signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
#     if not created:
#         try:
#             user = instance.inquiry.user
#             logger.info(f"Sending update notification to user: {user.email}")
#             notification = Notification.objects.create(
#                 recipient=user,
#                 message=f"Your Safety Training inquiry #{instance.inquiry.id} has been updated.",
#                 type="training_update"
#             )
#             logger.info(f"SafetyTrainingData update notification created for user: {user.email}, notification ID: {notification.id}")
#         except Exception as e:
#             logger.error(f"Error creating SafetyTrainingData update notification for user email: {instance.inquiry.email}, error: {str(e)}")