from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Product, Supplier
from .forms import ProductForm
from django.template.loader import render_to_string
from django.db import models


class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category', 'manufacturer', 'supplier', 'unit').all()
        q = self.request.GET.get('q')
        supplier = self.request.GET.get('supplier')
        sort = self.request.GET.get('sort')

        if q:
            qs = qs.filter(
                models.Q(name__icontains=q) |
                models.Q(description__icontains=q) |
                models.Q(manufacturer__name__icontains=q) |
                models.Q(supplier__name__icontains=q)
            )

        if supplier:
            qs = qs.filter(supplier__id=supplier)

        if sort == 'quantity_asc':
            qs = qs.order_by('quantity')
        elif sort == 'quantity_desc':
            qs = qs.order_by('-quantity')

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['suppliers'] = Supplier.objects.all()
        ctx['q'] = self.request.GET.get('q', '')
        ctx['supplier_sel'] = self.request.GET.get('supplier', '')
        ctx['sort'] = self.request.GET.get('sort', '')
        ctx['can_edit'] = self.request.user.has_perm('shop.change_product') if self.request.user.is_authenticated else False
        ctx['can_add'] = self.request.user.has_perm('shop.add_product') if self.request.user.is_authenticated else False
        ctx['can_delete'] = self.request.user.has_perm('shop.delete_product') if self.request.user.is_authenticated else False
        return ctx

    def render_to_response(self, context, **response_kwargs):
        # support partial rendering for AJAX dynamic updates
        if self.request.GET.get('partial'):
            html = render_to_string('shop/_product_table.html', context=context, request=self.request)
            return render(self.request, 'shop/_product_table.html', context)
        return super().render_to_response(context, **response_kwargs)


from django.contrib.auth import views as auth_views


class LoginView(auth_views.LoginView):
    template_name = 'registration/login.html'


from django.contrib.auth import logout
from django.shortcuts import redirect


def logout_view(request):
    logout(request)
    return redirect('product_list')


class ProductCreateView(PermissionRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    permission_required = 'shop.add_product'
    success_url = reverse_lazy('product_list')

    def form_valid(self, form):
        messages.success(self.request, 'Товар успешно добавлен')
        return super().form_valid(form)


class ProductUpdateView(PermissionRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'shop/product_form.html'
    permission_required = 'shop.change_product'
    success_url = reverse_lazy('product_list')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Prevent concurrent editing
        if self.object.is_locked and self.object.locked_by != request.user:
            # lock older than 1 hour will be ignored
            if self.object.locked_at and timezone.now() - self.object.locked_at > timezone.timedelta(hours=1):
                self.object.unlock()
            else:
                messages.error(request, 'Товар в данный момент редактируется другим пользователем')
                return redirect('product_list')
        # set lock
        self.object.lock(request.user)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        # if image replaced, delete old file
        old = Product.objects.get(pk=self.object.pk)
        old_image = old.image
        resp = super().form_valid(form)
        new = self.object
        if old_image and old_image != new.image:
            try:
                old_image.delete(save=False)
            except Exception:
                pass
        # release lock
        new.unlock()
        messages.success(self.request, 'Товар успешно обновлён')
        return resp

    def form_invalid(self, form):
        # ensure lock released if invalid
        try:
            self.object.unlock()
        except Exception:
            pass
        return super().form_invalid(form)


class ProductDeleteView(PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'shop/product_confirm_delete.html'
    permission_required = 'shop.delete_product'
    success_url = reverse_lazy('product_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # prevent deletion if product is in any order
        if self.object.orderitem_set.exists():
            messages.error(request, 'Невозможно удалить товар, он присутствует в заказе')
            return redirect('product_list')
        # delete image file
        if self.object.image:
            try:
                self.object.image.delete(save=False)
            except Exception:
                pass
        messages.success(request, 'Товар удалён')
        return super().delete(request, *args, **kwargs)
