from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from shop.models import Product, Order


class Command(BaseCommand):
    help = 'Create default groups and assign basic permissions (client, manager, admin)'

    def handle(self, *args, **options):
        # groups and permissions
        groups = {
            'client': [],
            'manager': ['view_product', 'view_order'],
            'admin': ['add_product', 'change_product', 'delete_product', 'view_product', 'add_order', 'change_order', 'delete_order', 'view_order'],
        }

        for name, perms in groups.items():
            g, created = Group.objects.get_or_create(name=name)
            for perm_codename in perms:
                # try product permissions first then order
                try:
                    ct = ContentType.objects.get_for_model(Product)
                    p = Permission.objects.get(content_type=ct, codename=perm_codename)
                except Permission.DoesNotExist:
                    try:
                        ct = ContentType.objects.get_for_model(Order)
                        p = Permission.objects.get(content_type=ct, codename=perm_codename)
                    except Permission.DoesNotExist:
                        p = None
                if p:
                    g.permissions.add(p)
            self.stdout.write(self.style.SUCCESS(f'Group {name} ready'))

        self.stdout.write(self.style.SUCCESS('Default groups initialized'))
