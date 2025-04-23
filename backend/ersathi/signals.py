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


#inquary
@receiver(post_save, sender=Inquiry)
def send_inquiry_notification(sender, instance, created, **kwargs):
    """Send notification to the company when a new inquiry is created."""
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
            update_fields = kwargs.get('update_fields', set())
            if 'company_response' in update_fields and instance.company_response:
                # Company added a response, notify user
                logger.info(f"Sending comment response notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"{inquiry.company.company_name} responded to your comment on inquiry #{inquiry.id}: {instance.company_response[:50]}...",
                    type="comment_response"
                )
                logger.info(f"Comment response notification created for user: {user.email}, notification ID: {notification.id}")
    except Exception as e:
        logger.error(f"Error creating comment notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")

# Notifications for updates to associated models
@receiver(post_save, sender=EngineeringConsultingData)
@receiver(post_save, sender=PostConstructionMaintenanceData)
@receiver(post_save, sender=SafetyTrainingData)
@receiver(post_save, sender=Appointment)
def send_associated_model_update_notification(sender, instance, created, **kwargs):
    """Send notification to user when associated model is created or updated."""
    model_name = sender.__name__
    logger.info(f"{model_name} signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
    try:
        inquiry = instance.inquiry
        user = inquiry.user
        company_user = inquiry.company.customuser

        if not user or not company_user:
            logger.error(f"Missing user or company user for {model_name} update on inquiry ID: {inquiry.id}")
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
    except Exception as e:
        logger.error(f"Error creating {model_name} notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")

# Specific notifications for BuildingConstructionData updates
@receiver(post_save, sender=BuildingConstructionData)
def send_building_construction_notification(sender, instance, created, **kwargs):
    """Send specific notifications for BuildingConstructionData creation and updates."""
    logger.info(f"BuildingConstructionData signal triggered for inquiry ID: {instance.inquiry.id}, created: {created}")
    
    try:
        inquiry = instance.inquiry
        user = inquiry.user
        company_user = inquiry.company.customuser

        if not user or not company_user:
            logger.error(f"Missing user or company user for BuildingConstructionData update on inquiry ID: {inquiry.id}")
            return

        update_fields = kwargs.get('update_fields', set())
        action = "created" if created else "updated"

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
            if 'permit_status' in update_fields and instance.permit_status:
                logger.info(f"Sending permit status update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} permit status updated to {instance.permit_status} by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_permit_status"
                )
                logger.info(f"Permit status notification created for user: {user.email}, notification ID: {notification.id}")

            if 'construction_phase' in update_fields and instance.construction_phase:
                logger.info(f"Sending construction phase update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} construction phase updated to {instance.construction_phase} by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_construction_phase"
                )
                logger.info(f"Construction phase notification created for user: {user.email}, notification ID: {notification.id}")

            if 'progress_percentage' in update_fields and instance.progress_percentage is not None:
                logger.info(f"Sending progress percentage update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} construction progress updated to {instance.progress_percentage}% by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_progress_percentage"
                )
                logger.info(f"Progress percentage notification created for user: {user.email}, notification ID: {notification.id}")

            if 'progress_photos' in update_fields and instance.progress_photos:
                logger.info(f"Sending progress photos update notification to user: {user.email}")
                notification = Notification.objects.create(
                    recipient=user,
                    message=f"Your inquiry #{inquiry.id} has new progress photos uploaded by {inquiry.company.company_name}.",
                    type="buildingconstructiondata_progress_photos"
                )
                logger.info(f"Progress photos notification created for user: {user.email}, notification ID: {notification.id}")

    except Exception as e:
        logger.error(f"Error creating BuildingConstructionData notification for inquiry ID: {instance.inquiry.id}, error: {str(e)}")

