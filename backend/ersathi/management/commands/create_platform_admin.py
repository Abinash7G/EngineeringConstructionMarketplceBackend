from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

class Command(BaseCommand):
    help = 'Create a new user interactively and add to the "Platformadmin" group'

    def handle(self, *args, **kwargs):
        self.stdout.write("Enter user details:")

        # Get the custom user model
        User = get_user_model()

        # Prompt for username
        username = input("Username: ").strip()
        if User.objects.filter(username=username).exists():
            self.stderr.write(f"Error: Username '{username}' already exists.")
            return

        # Prompt for email
        email = input("Email: ").strip()
        if User.objects.filter(email=email).exists():
            self.stderr.write(f"Error: Email '{email}' already exists.")
            return

        # Prompt for password
        password = input("Password: ").strip()
        confirm_password = input("Confirm Password: ").strip()
        if password != confirm_password:
            self.stderr.write("Error: Passwords do not match.")
            return

        # Create the user
        user = User.objects.create_user(username=username, email=email)
        user.set_password(password)
        user.save()

        # Check if the group "Platformadmin" exists
        group, created = Group.objects.get_or_create(name='Platformadmin')
        if created:
            self.stdout.write(f"Group 'Platformadmin' created.")

        # Add the user to the group
        user.groups.add(group)
        user.save()

        self.stdout.write(f"User '{username}' created successfully and added to the 'Platformadmin' group!")
