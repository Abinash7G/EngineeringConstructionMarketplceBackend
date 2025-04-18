from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import EWallet, CustomUser


@receiver(post_save, sender=CustomUser)
def create_user_ewallet(sender, instance, created, **kwargs):
    """Automatically create an E-Wallet with a default balance when a new user is created."""
    if created:
        # Create the EWallet with a default balance of 3000
        EWallet.objects.create(user=instance, balance=3000.00)

@receiver(post_save, sender=CustomUser)
def save_user_ewallet(sender, instance, **kwargs):
    """Save the E-Wallet when the user instance is saved."""
    try:
        instance.ewallet.save()
    except EWallet.DoesNotExist:
        pass

# ersathi/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Inquiry, Verification, DeviceToken
from firebase import send_push_notification  # Import from backend.firebase

@receiver(post_save, sender=Inquiry)
def notify_user_on_inquiry_change(sender, instance, created, **kwargs):
    user = instance.user
    device_tokens = DeviceToken.objects.filter(user=user).values_list('token', flat=True)

    if created:
        # Notify user when a new inquiry is created
        send_push_notification(
            device_tokens=list(device_tokens),
            title="New Inquiry Created",
            body=f"Your inquiry '{instance.title}' has been created.",
            data={"inquiry_id": str(instance.id)}
        )
    else:
        # Notify user when an existing inquiry is updated
        send_push_notification(
            device_tokens=list(device_tokens),
            title="Inquiry Updated",
            body=f"Your inquiry '{instance.title}' has been updated.",
            data={"inquiry_id": str(instance.id)}
        )

@receiver(post_save, sender=Verification)
def notify_admin_on_verification(sender, instance, created, **kwargs):
    if created:
        # Get all admin users (assuming admins are in a group named 'Admins')
        admin_group = Group.objects.get(name='Admins')
        admins = admin_group.user_set.all()
        admin_device_tokens = DeviceToken.objects.filter(user__in=admins).values_list('token', flat=True)

        # Notify admins when a new verification is listed
        send_push_notification(
            device_tokens=list(admin_device_tokens),
            title="New Verification Request",
            body=f"A new verification request for {instance.company.name} has been listed.",
            data={"verification_id": str(instance.id)}
        )