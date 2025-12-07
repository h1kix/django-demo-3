from django.test import TestCase
from django.urls import reverse
from .models import Category, Product, Supplier, Manufacturer, Unit


class ShopModelsTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='TestCat')
        man = Manufacturer.objects.create(name='M')
        sup = Supplier.objects.create(name='S')
        unit = Unit.objects.create(name='шт.')
        Product.objects.create(name='P1', category=cat, manufacturer=man, supplier=sup, unit=unit, price=10.0, discount=0, quantity=5)

    def test_product_created(self):
        p = Product.objects.get(name='P1')
        self.assertEqual(p.quantity, 5)


class ShopViewsTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name='TestCat')
        man = Manufacturer.objects.create(name='M')
        sup = Supplier.objects.create(name='S')
        unit = Unit.objects.create(name='шт.')
        Product.objects.create(name='P1', category=cat, manufacturer=man, supplier=sup, unit=unit, price=10.0, discount=0, quantity=5)

    def test_product_list(self):
        resp = self.client.get(reverse('product_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'P1')
