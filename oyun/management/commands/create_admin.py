"""
Django management command to create a superuser.
Usage: python manage.py create_admin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os


class Command(BaseCommand):
    help = 'Creates a superuser from environment variables or default values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=os.environ.get('ADMIN_USERNAME', 'admin'),
            help='Admin username'
        )
        parser.add_argument(
            '--email',
            type=str,
            default=os.environ.get('ADMIN_EMAIL', 'admin@example.com'),
            help='Admin email'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=os.environ.get('ADMIN_PASSWORD', 'admin123'),
            help='Admin password'
        )

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" password updated successfully!')
            )
        else:
            # Create new superuser
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{username}" created successfully!')
            )
        
        self.stdout.write(
            self.style.WARNING(f'\nAdmin Login Info:')
        )
        self.stdout.write(f'  Username: {username}')
        self.stdout.write(f'  Password: {password}')
        self.stdout.write(f'  URL: /admin/')

