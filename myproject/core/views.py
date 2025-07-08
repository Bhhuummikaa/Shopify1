from django.shortcuts import render, redirect, get_object_or_404
from .models import Stores, Customers, Orders, Addresses, LineItems, Rules, FlaggedOrders
from .forms import StoreForm, CustomerForm, OrderForm, AddressForm, LineItemForm, RuleForm, FlaggedOrderForm
import logging
logger = logging.getLogger(__name__)
from django.db.models import Func, Value
from django.db.models.functions import Replace
# from django.http import JsonResponse
# from django.utils.dateparse import parse_datetime
# from django.contrib.auth.forms import AuthenticationForm
# from django.contrib.auth import login as auth_login
# from django.utils import timezone
import pandas as pd
# # from .forms import UploadFileForm
# from django.http import HttpResponse
from django.contrib import messages
# import requests
# from decimal import Decimal, InvalidOperation
import time

# from django.utils.dateparse import parse_datetime
# import datetime

from decimal import Decimal, InvalidOperation
# import csv
# from io import TextIOWrapper
# from datetime import datetime
from django.utils import timezone
from decimal import Decimal



def safe_decimal(val):
    try:
        if pd.isna(val) or val == "nan":
            return Decimal("0.00")
        return Decimal(str(val))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


# def safe_datetime(val):
#     if pd.isna(val) or val in ["", None]:
#         return None
#     if isinstance(val, datetime.datetime):
#         return val
#     try:
#         return parse_datetime(str(val))
#     except Exception:
#         return None


 
# # Stores

def store_list(request):
    stores = Stores.objects.all().order_by('-created_at')
    return render(request, 'stores/store_list.html', {'stores': stores})

def store_create(request):
    form = StoreForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('store_list')
    return render(request, 'stores/store_form.html', {'form': form})

def store_update(request, pk):
    store = get_object_or_404(Stores, pk=pk)
    form = StoreForm(request.POST or None, instance=store)
    if form.is_valid():
        form.save()
        return redirect('store_list')
    return render(request, 'stores/store_form.html', {'form': form})

def store_delete(request, pk):
    store = get_object_or_404(Stores, pk=pk)
    if request.method == 'POST':
        store.delete()
        return redirect('store_list')
    return render(request, 'stores/store_confirm_delete.html', {'store': store})

# Customers

def customer_list(request):
    customers = Customers.objects.all().order_by('-created_at')
    return render(request, 'customers/customer_list.html', {'customers': customers})

def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'customers/customer_form.html', {'form': form})

def customer_update(request, pk):
    customer = get_object_or_404(Customers, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        return redirect('customer_list')
    return render(request, 'customers/customer_form.html', {'form': form})

def customer_delete(request, pk):
    customer = get_object_or_404(Customers, pk=pk)
    if request.method == 'POST':
        customer.delete()
        return redirect('customer_list')
    return render(request, 'customers/customer_confirm_delete.html', {'customer': customer})

# Orders

def order_list(request):
    # 1. Handle status update from file upload (POST request)
    if request.method == 'POST' and 'update_status' in request.POST:
        if 'status_file' in request.FILES:
            uploaded_file = request.FILES['status_file']
            success_count = 0
            error_count = 0
            
            try:
                # Read Excel file
                if uploaded_file.name.endswith('.csv'):
                    import csv
                    reader = csv.DictReader(uploaded_file.read().decode('utf-8').splitlines())
                    rows = list(reader)
                else:
                    df = pd.read_excel(uploaded_file)
                    rows = df.to_dict('records')
                
                # Process each row
                for row in rows:
                    try:
                        phone = str(row.get('Mobile Nos', '')).strip()
                        status = str(row.get('Status', '')).strip().lower()
                        
                        if not phone or len(phone) < 10:
                            continue
                            
                        # Find matching orders by phone number
                        orders = Orders.objects.filter(
                            contact_phone__icontains=phone
                        )
                        
                        for order in orders:
                            # Only update delivery status
                            if status in ['delivered', 'completed']:
                                order.delivery_status = 'delivered'
                            elif status == 'rto':
                                order.delivery_status = 'rto'
                            
                            order.save()
                            success_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error processing row: {e}")
                
                messages.success(request, 
                    f"Updated delivery status for {success_count} orders. " +
                    f"Errors: {error_count}"
                )
                
            except Exception as e:
                messages.error(request, f"File processing failed: {str(e)}")
        return redirect('order_list')

    # 2. Handle order listing (GET request)
    status_filter = request.GET.get('status')
    flag_filter = request.GET.get('flag')
    
    orders = Orders.objects.select_related('customer')\
                         .prefetch_related('addresses', 'lineitems')\
                         .order_by('-created_at')
    
    if status_filter == 'paid':
        orders = orders.filter(financial_status__in=['paid', 'prepaid'])
    elif status_filter == 'pending':
        orders = orders.exclude(financial_status__in=['paid', 'prepaid'])
    
    # Get phone counts using aggregation
    from django.db.models import Count
    phone_counts = dict(
        Orders.objects.exclude(contact_phone__isnull=True)
                     .values_list('contact_phone')
                     .annotate(count=Count('contact_phone'))
    )
    
    combined_data = []
    for order in orders:
        address = order.addresses.first()
        phone_digits = ''.join(c for c in (order.contact_phone or '') if c.isdigit())
        is_flagged = (
            (address and len(address.address1 or '') < 20) or
            (order.contact_phone and len(phone_digits) < 10) or
            (order.contact_phone and phone_counts.get(order.contact_phone, 0) > 1)
        )
        
        combined_data.append({
            'order': order,
            'customer_name': f"{order.customer.first_name} {order.customer.last_name}" if order.customer else "N/A",
            'customer_email': order.customer.email if order.customer else "N/A",
            'customer_phone': order.contact_phone or "N/A",
            'address_details': (
                f"{address.address1}, {address.city}, {address.state}" 
                if address else "N/A"
            ),
            'line_items': order.lineitems.all(),
            'display_total': (
                order.total_price if order.total_price > 0 else
                sum(item.price * item.quantity for item in order.lineitems.all()) - 
                (order.total_discounts or 0)
            ),
            'is_flagged': is_flagged
        })
    
    # Counts (optimized)
    counts = {
        'total': Orders.objects.count(),
        'paid': Orders.objects.filter(financial_status__in=['paid', 'prepaid']).count(),
        'pending': Orders.objects.exclude(financial_status__in=['paid', 'prepaid']).count(),
        'red_flag': sum(1 for item in combined_data if item['is_flagged']),
        'green_flag': sum(1 for item in combined_data if not item['is_flagged'])
    }

    return render(request, 'orders/order_list.html', {
        'combined_data': combined_data,
        'status_filter': status_filter,
        'flag_filter': flag_filter,
        **counts
    })
def order_create(request):
    form = OrderForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('order_list')
    return render(request, 'orders/order_form.html', {'form': form})

def order_update(request, pk):
    order = get_object_or_404(Orders, pk=pk)
    form = OrderForm(request.POST or None, instance=order)
    
    if request.method == 'POST' and form.is_valid():
        order = form.save()
        
        # Handle address update
        address = order.addresses.first()
        if address:
            address.address1 = request.POST.get('address1', '')
            address.address2 = request.POST.get('address2', '')
            address.city = request.POST.get('city', '')
            address.state = request.POST.get('state', '')
            address.country = request.POST.get('country', '')
            address.zip = request.POST.get('zip', '')
            address.phone = request.POST.get('phone', '')
            address.save()
        else:
            # Create new address if none exists
            address = Addresses.objects.create(
                order=order,
                customer=order.customer,
                store=order.store,
                address1=request.POST.get('address1', ''),
                address2=request.POST.get('address2', ''),
                city=request.POST.get('city', ''),
                state=request.POST.get('state', ''),
                country=request.POST.get('country', ''),
                zip=request.POST.get('zip', ''),
                phone=request.POST.get('phone', ''),
                first_name=order.customer.first_name if order.customer else '',
                last_name=order.customer.last_name if order.customer else '',
            )
        
        return redirect('order_list')
    
    return render(request, 'orders/order_form.html', {'form': form})

def order_delete(request, pk):
    order = get_object_or_404(Orders, pk=pk)
    if request.method == 'POST':
        order.delete()
        return redirect('order_list')
    return render(request, 'orders/order_confirm_delete.html', {'order': order})

# Addresses

def address_list(request):
    addresses = Addresses.objects.all().order_by('-created_at')
    return render(request, 'addresses/address_list.html', {'addresses': addresses})

def address_create(request):
    form = AddressForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('address_list')
    return render(request, 'addresses/address_form.html', {'form': form})

def address_update(request, pk):
    address = get_object_or_404(Addresses, pk=pk)
    form = AddressForm(request.POST or None, instance=address)
    if form.is_valid():
        form.save()
        return redirect('address_list')
    return render(request, 'addresses/address_form.html', {'form': form})

def address_delete(request, pk):
    address = get_object_or_404(Addresses, pk=pk)
    if request.method == 'POST':
        address.delete()
        return redirect('address_list')
    return render(request, 'addresses/address_confirm_delete.html', {'address': address})

# Line Items

def lineitem_list(request):
    items = LineItems.objects.all().order_by('-created_at')
    return render(request, 'line_items/lineitem_list.html', {'items': items})

def lineitem_create(request):
    form = LineItemForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('lineitem_list')
    return render(request, 'line_items/lineitem_form.html', {'form': form})

def lineitem_update(request, pk):
    item = get_object_or_404(LineItems, pk=pk)
    form = LineItemForm(request.POST or None, instance=item)
    if form.is_valid():
        form.save()
        return redirect('lineitem_list')
    return render(request, 'line_items/lineitem_form.html', {'form': form})

def lineitem_delete(request, pk):
    item = get_object_or_404(LineItems, pk=pk)
    if request.method == 'POST':
        item.delete()
        return redirect('lineitem_list')
    return render(request, 'line_items/lineitem_confirm_delete.html', {'item': item})

# Rules

def rule_list(request):
    rules = Rules.objects.all().order_by('-created_at')
    return render(request, 'rules/rule_list.html', {'rules': rules})

def rule_create(request):
    form = RuleForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('rule_list')
    return render(request, 'rules/rule_form.html', {'form': form})

def rule_update(request, pk):
    rule = get_object_or_404(Rules, pk=pk)
    form = RuleForm(request.POST or None, instance=rule)
    if form.is_valid():
        form.save()
        return redirect('rule_list')
    return render(request, 'rules/rule_form.html', {'form': form})

def rule_delete(request, pk):
    rule = get_object_or_404(Rules, pk=pk)
    if request.method == 'POST':
        rule.delete()
        return redirect('rule_list')
    return render(request, 'rules/rule_confirm_delete.html', {'rule': rule})

# Flagged Orders

def flaggedorder_list(request):
    flagged = FlaggedOrders.objects.all().order_by('-flagged_at')
    return render(request, 'flagged_orders/flaggedorder_list.html', {'flagged': flagged})

def flaggedorder_create(request):
    form = FlaggedOrderForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('flaggedorder_list')
    return render(request, 'flagged_orders/flaggedorder_form.html', {'form': form})

def flaggedorder_update(request, pk):
    flagged = get_object_or_404(FlaggedOrders, pk=pk)
    form = FlaggedOrderForm(request.POST or None, instance=flagged)
    if form.is_valid():
        form.save()
        return redirect('flaggedorder_list')
    return render(request, 'flagged_orders/flaggedorder_form.html', {'form': form})

def flaggedorder_delete(request, pk):
    flagged = get_object_or_404(FlaggedOrders, pk=pk)
    if request.method == 'POST':
        flagged.delete()
        return redirect('flaggedorder_list')
    return render(request, 'flagged_orders/flaggedorder_confirm_delete.html', {'flagged': flagged})

def order_detail(request, pk):
    order = get_object_or_404(Orders, pk=pk)
    return render(request, 'orders/order_detail.html', {'order': order})
# views.py
def order_import(request):
    if request.method == 'POST':
        # Handle file upload logic here
        pass
    return render(request, 'orders/import.html')

# # def landing_login(request):
# #     if request.method == 'POST':
# #         form = AuthenticationForm(data=request.POST)
# #         if form.is_valid():
# #             user = form.get_user()
# #             auth_login(request, user)
# #             return redirect('store_list') 
# #     else:
# #         form = AuthenticationForm()
# #     return render(request, 'login.html', {'form': form})

# #landing page
# def landing_login(request):
#     form = AuthenticationForm(data=request.POST or None)
#     error_message = None

#     if request.method == 'POST':
#         if form.is_valid():
#             user = form.get_user()
#             auth_login(request, user)
#             return redirect('upload-csv/')
#         else:
#             error_message = "Incorrect username or password."

#     return render(request, 'login.html', {
#         'form': form,
#         'error_message': error_message
#     })

# # def fetch_shopify_orders(request, store_id):
# #     store = get_object_or_404(Stores, id=store_id)
# #     success, message = fetch_and_store_orders(store)

# #     if not success:
# #         return HttpResponse(message, status=500)

# #     return redirect('order_list') 





# # def fetch_all_orders(request):
# #     stores = Stores.objects.all()
# #     for store in stores:
# #         try:
# #             fetch_shopify_orders(store)
# #             messages.success(request, f"Orders fetched from store {store.name}.")
# #         except Exception as e:
# #             messages.error(request, f"Error fetching from {store.name}: {str(e)}")
# #     return redirect('orders_list')

# # def orders_list(request):
# #     orders = Orders.objects.select_related('customer').all().order_by('-created_at')
# #     return render(request, 'core/template/orders/orders_list.html', {'orders': orders})



# # def fetch_shopify_orders(request):

# #     shopify_domain = "0f24c3-4a.myshopify.com"
# #     access_token = "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" 

# #     url = f"https://{shopify_domain}/admin/api/2023-10/orders.json"
# #     headers = {
# #         "X-Shopify-Access-Token": access_token
# #     }

# #     response = requests.get(url, headers=headers)
# #     if response.status_code != 200:
# #         return JsonResponse({"error": "Failed to fetch orders"}, status=response.status_code)

# #     data = response.json().get('orders', [])
# #     for order_data in data:
# #         # Optional: get or create a dummy store to link
# #         store, _ = Stores.objects.get_or_create(
# #             shopify_domain=shopify_domain,
# #             defaults={
# #                 "name": "Kespar Shop 9",
# #                 "access_token": access_token,
# #                 "created_at": parse_datetime(order_data["created_at"]),
# #                 "updated_at": parse_datetime(order_data["updated_at"]),
# #             }
# #         )

# #         customer_data = order_data.get('customer', {})
# #         customer, _ = Customers.objects.get_or_create(
# #             store=store,
# #             remote_id=customer_data['id'],
# #             defaults={
# #                 'email': customer_data.get('email', ''),
# #                 'first_name': customer_data.get('first_name', ''),
# #                 'last_name': customer_data.get('last_name', ''),
# #                 'verified_email': customer_data.get('verified_email'),
# #                 'currency': order_data.get('currency'),
# #                 'created_at': parse_datetime(customer_data['created_at']),
# #                 'updated_at': parse_datetime(customer_data['updated_at']),
# #             }
# #         )

# #         order, _ = Orders.objects.get_or_create(
# #             store=store,
# #             remote_id=order_data['id'],
# #             defaults={
# #                 'order_number': order_data.get('order_number'),
# #                 'name': order_data.get('name'),
# #                 'contact_email': order_data.get('contact_email'),
# #                 'contact_phone': order_data.get('phone'),
# #                 'financial_status': order_data.get('financial_status'),
# #                 'total_price': order_data.get('total_price', 0),
# #                 'subtotal_price': order_data.get('subtotal_price', 0),
# #                 'total_tax': order_data.get('total_tax', 0),
# #                 'total_discounts': order_data.get('total_discounts', 0),
# #                 'currency': order_data.get('currency'),
# #                 'processed_at': safe_datetime(order_data.get('processed_at')) if order_data.get('processed_at') else None,
# #                 'created_at': safe_datetime(order_data.get('created_at')),
# #                 'updated_at': safe_datetime(order_data.get('updated_at')),
# #                 'customer': customer,
# #                 'tags': order_data.get('tags'),
# #                 'payment_gateway': ', '.join(order_data.get('payment_gateway_names', [])),
# #                 'shipping_title': order_data.get('shipping_lines')[0]['title'] if order_data.get('shipping_lines') else '',
# #                 'shipping_code': '',
# #                 'shipping_price': order_data.get('total_shipping_price_set', {}).get('shop_money', {}).get('amount', 0)
# #             }
# #         )

# #         for item in order_data.get('line_items', []):
# #             LineItems.objects.get_or_create(
# #                 order=order,
# #                 remote_id=item['id'],
# #                 defaults={
# #                     'sku': item.get('sku', ''),
# #                     'name': item.get('name'),
# #                     'quantity': item.get('quantity'),
# #                     'price': item.get('price'),
# #                     'fulfillment_status': item.get('fulfillment_status'),
# #                     'created_at': safe_datetime(order_data.get('created_at')),
# #                     'updated_at': safe_datetime(order_data.get('updated_at')),
# #                 }
# #             )

# #         if order_data.get('shipping_address'):
# #             address_data = order_data['shipping_address']
# #             Addresses.objects.get_or_create(
# #                 order=order,
# #                 store=store,
# #                 remote_id=address_data.get('id'),
# #                 defaults={
# #                     'first_name': address_data.get('first_name'),
# #                     'last_name': address_data.get('last_name'),
# #                     'address1': address_data.get('address1'),
# #                     'address2': address_data.get('address2'),
# #                     'city': address_data.get('city'),
# #                     'state': address_data.get('province'),
# #                     'country': address_data.get('country'),
# #                     'zip': address_data.get('zip'),
# #                     'phone': address_data.get('phone'),
# #                     'created_at': parse_datetime(order_data.get('created_at')),
# #                     'updated_at': parse_datetime(order_data.get('updated_at')),
# #                     'customer': customer,
# #                 }
# #             )

# #     return JsonResponse({"message": f"{len(data)} orders fetched and stored successfully."})

# # def upload_file_view(request):
# #     if request.method == 'POST':
# #         form = UploadFileForm(request.POST, request.FILES)
# #         if form.is_valid():
# #             model_name = form.cleaned_data['model_name']
# #             file = request.FILES['file']

# #             try:
# #                 df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
# #             except Exception:
# #                 messages.error(request, "Error reading file.")
# #                 return redirect('upload_file')

# #             try:
# #                 if model_name == 'stores':
# #                     for _, row in df.iterrows():
# #                         Stores.objects.update_or_create(
# #                             shopify_domain=row.get('shopify_domain'),
# #                             defaults={
# #                                 'name': row.get('name'),
# #                                 'access_token': row.get('access_token'),
# #                                 'created_at': row.get('created_at') or timezone.now(),
# #                                 'updated_at': row.get('updated_at') or timezone.now(),
# #                             }
# #                         )

# #                 elif model_name == 'customers':
# #                     for _, row in df.iterrows():
# #                         Customers.objects.update_or_create(
# #                             remote_id=row['remote_id'],
# #                             store_id=row['store_id'],
# #                             defaults={
# #                                 'email': row.get('email'),
# #                                 'first_name': row.get('first_name'),
# #                                 'last_name': row.get('last_name'),
# #                                 'verified_email': row.get('verified_email'),
# #                                 'currency': row.get('currency'),
# #                                 'created_at': row.get('created_at'),
# #                                 'updated_at': row.get('updated_at'),
# #                             }
# #                         )

# #                 elif model_name == 'orders':
# #                     for _, row in df.iterrows():
# #                         Orders.objects.create(
# #                             remote_id=int(time.time() * 1000000) + _, 
# #                             store_id=1,
# #                             name=row.get("Billing Name") or row.get("Name"),
# #                             contact_email=row.get("Email") or row.get("email"),
# #                             contact_phone=str(row.get("Phone")),
# #                             financial_status=row.get("Financial Status"),
# #                             total_price=safe_decimal(row.get("Total")),
# #                             subtotal_price=safe_decimal(row.get("Subtotal")),
# #                             total_tax=safe_decimal(row.get("Tax 5 Value")),
# #                             total_discounts=safe_decimal(row.get("Discount Amount")),
# #                             currency=row.get("Currency"),
# #                             processed_at=safe_datetime(row.get("Paid at")),
# #                             created_at=safe_datetime(row.get("Paid at")) or timezone.now(),
# #                             updated_at=safe_datetime(row.get("Paid at")) or timezone.now(),
# #                             customer=None,
# #                             tags=row.get("Tags", ""),
# #                             payment_gateway=row.get("Payment Method", ""),
# #                             shipping_title=row.get("Shipping Province Name", ""),
# #                             shipping_code=None,
# #                             shipping_price=safe_decimal(row.get("Shipping")),
# #                         )

# #                 elif model_name == 'lineitems':
# #                     for _, row in df.iterrows():
# #                         LineItems.objects.create(
# #                             order_id=row['order_id'],
# #                             sku=row.get('sku'),
# #                             remote_id=row.get('remote_id'),
# #                             name=row.get('name'),
# #                             quantity=row.get('quantity'),
# #                             price=safe_decimal(row.get('price')),
# #                             fulfillment_status=row.get('fulfillment_status'),
# #                             created_at=row.get('created_at'),
# #                             updated_at=row.get('updated_at'),
# #                         )

# #                 elif model_name == 'addresses':
# #                     for _, row in df.iterrows():
# #                         Addresses.objects.create(
# #                             store_id=row.get('store_id'),
# #                             remote_id=row.get('remote_id'),
# #                             customer_id=row.get('customer_id'),
# #                             order_id=row.get('order_id'),
# #                             first_name=row.get('first_name'),
# #                             last_name=row.get('last_name'),
# #                             address1=row.get('address1'),
# #                             address2=row.get('address2'),
# #                             city=row.get('city'),
# #                             state=row.get('state'),
# #                             country=row.get('country'),
# #                             zip=row.get('zip'),
# #                             phone=row.get('phone'),
# #                             created_at=row.get('created_at'),
# #                             updated_at=row.get('updated_at'),
# #                         )

# #                 elif model_name == 'rules':
# #                     for _, row in df.iterrows():
# #                         Rules.objects.create(
# #                             name=row.get('name'),
# #                             description=row.get('description'),
# #                             condition=row.get('condition'),
# #                             scope=row.get('scope'),
# #                             store_id=row.get('store_id'),
# #                             is_enabled=row.get('is_enabled'),
# #                             created_at=row.get('created_at'),
# #                             updated_at=row.get('updated_at'),
# #                         )

# #                 elif model_name == 'flaggedorders':
# #                     for _, row in df.iterrows():
# #                         FlaggedOrders.objects.create(
# #                             order_id=row.get('order_id'),
# #                             rule_id=row.get('rule_id'),
# #                             flagged_at=row.get('flagged_at'),
# #                         )

# #                 messages.success(request, f"{model_name.capitalize()} uploaded and saved.")
# #                 return redirect(f"{model_name}_list")

# #             except Exception as e:
# #                 messages.error(request, f"Upload failed: {str(e)}")
# #                 return redirect('upload_file')

# #     else:
# #         form = UploadFileForm()

# #     return render(request, 'upload.html', {'form': form})
# # views.py - Add these imports at the top
# import csv
# from io import TextIOWrapper
# from datetime import datetime
# from django.utils import timezone
# from decimal import Decimal
# from django.contrib import messages
# from django.shortcuts import render, redirect
# from .forms import UploadForm 
# from .models import Stores, Customers, Orders, LineItems, Addresses

# def upload_csv(request):
#     if request.method == 'POST':
#         form =UploadForm(request.POST, request.FILES)
#         if form.is_valid():
#             uploaded_file = request.FILES['file']
#             success_count = 0
#             duplicate_count = 0
#             error_count = 0
            
#             try:
#                 csv_file = TextIOWrapper(uploaded_file.file, encoding='utf-8')
#                 reader = csv.DictReader(csv_file)
                
#                 store, _ = Stores.objects.get_or_create(
#                     name="Frankshirt",
#                     shopify_domain="frankshirt.co.in",
#                     defaults={
#                         'access_token': '',
#                         'created_at': timezone.now(),
#                         'updated_at': timezone.now()
#                     }
#                 )
                
#                 for row in reader:
#                     try:
#                         # Get remote_id from row
#                         remote_id = int(row['Name'].replace('#FS', '')) if row.get('Name') else 0
                        
#                         # Check if order already exists
#                         if Orders.objects.filter(store=store, remote_id=remote_id).exists():
#                             duplicate_count += 1
#                             continue  # Skip this row
                            
#                         # Helper function to safely convert to Decimal
#                         def safe_decimal(value):
#                             if not value or value.strip() == '':
#                                 return Decimal('0.00')
#                             try:
#                                 clean_value = value.replace('₹', '').replace(',', '').strip()
#                                 return Decimal(clean_value)
#                             except:
#                                 return Decimal('0.00')
                        
#                         # Parse dates with error handling
#                         try:
#                             paid_at = datetime.strptime(row['Paid at'], '%Y-%m-%d %H:%M:%S %z') if row.get('Paid at') else None
#                         except:
#                             paid_at = None
                        
#                         created_at = datetime.strptime(row['Created at'], '%Y-%m-%d %H:%M:%S %z') if row.get('Created at') else timezone.now()
                        
#                         # Get or create customer
#                         email = row.get('Email', '').strip() or None
#                         billing_name = row.get('Billing Name', '').strip()
#                         first_name = billing_name.split()[0] if billing_name else ''
#                         last_name = ' '.join(billing_name.split()[1:]) if billing_name else ''
                        
#                         customer, _ = Customers.objects.get_or_create(
#                             store=store,
#                             email=email,
#                             defaults={
#                                 'first_name': first_name,
#                                 'last_name': last_name,
#                                 'verified_email': False,
#                                 'currency': row.get('Currency', 'INR'),
#                                 'created_at': created_at,
#                                 'updated_at': created_at,
#                             }
#                         )
                        
#                         # Create order
#                         order = Orders.objects.create(
#                             store=store,
#                             remote_id=remote_id,
#                             order_number=remote_id,
#                             name=row.get('Name', ''),
#                             contact_email=email,
#                             contact_phone=row.get('Billing Phone', ''),
#                             financial_status=row.get('Financial Status', 'pending'),
#                             total_price=safe_decimal(row.get('Total', '0')),
#                             subtotal_price=safe_decimal(row.get('Subtotal', '0')),
#                             total_tax=safe_decimal(row.get('Taxes', '0')),
#                             total_discounts=safe_decimal(row.get('Discount Amount', '0')),
#                             currency=row.get('Currency', 'INR'),
#                             processed_at=paid_at,
#                             created_at=created_at,
#                             updated_at=created_at,
#                             customer=customer,
#                             tags=row.get('Tags', ''),
#                             payment_gateway=row.get('Payment Method', ''),
#                             shipping_title=row.get('Shipping Method', ''),
#                             shipping_code=row.get('Shipping Province', ''),
#                             shipping_price=safe_decimal(row.get('Shipping', '0')),
#                         )
                        
#                         # Create line item
#                         LineItems.objects.create(
#                             order=order,
#                             sku=row.get('Lineitem sku', ''),
#                             remote_id=order.remote_id * 100,
#                             name=row.get('Lineitem name', ''),
#                             quantity=int(row.get('Lineitem quantity', 1)),
#                             price=safe_decimal(row.get('Lineitem price', '0')),
#                             fulfillment_status=row.get('Lineitem fulfillment status', ''),
#                             created_at=created_at,
#                             updated_at=created_at,
#                         )
                        
#                         # Create billing address
#                         Addresses.objects.create(
#                             store=store,
#                             customer=customer,
#                             order=order,
#                             first_name=first_name,
#                             last_name=last_name,
#                             address1=row.get('Billing Address1', ''),
#                             address2=row.get('Billing Address2', ''),
#                             city=row.get('Billing City', ''),
#                             state=row.get('Billing Province', ''),
#                             country=row.get('Billing Country', ''),
#                             zip=row.get('Billing Zip', ''),
#                             phone=row.get('Billing Phone', ''),
#                             created_at=created_at,
#                             updated_at=created_at,
#                         )
                        
#                         success_count += 1
                        
#                     except Exception as e:
#                         error_count += 1
#                         # Log individual row errors if needed
#                         print(f"Error processing row: {e}")
#                         continue
                
#                 # Final message with import statistics
#                 message = (
#                     f"Import complete! "
#                     f"Success: {success_count}, "
#                     f"Duplicates skipped: {duplicate_count}, "
#                     f"Errors: {error_count}"
#                 )
#                 messages.success(request, message)
#                 return redirect('order_list')
            
#             except Exception as e:
#                 messages.error(request, f'Error processing file: {str(e)}')
#                 return redirect('upload_csv')
    
#     else:
#         form = UploadForm()
    
#     return render(request, 'upload.html', {'form': form})
# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login as auth_login
from .models import Orders, Customers, Addresses
import csv
from io import TextIOWrapper
from datetime import datetime
from decimal import Decimal
from .forms import UploadForm

# @login_required
# def dashboard(request):
#     orders = Orders.objects.select_related('customer')\
#                            .prefetch_related('addresses')\
#                            .all().order_by('-created_at')[:50]

#     combined_data = []

#     for order in orders:
#         customer = order.customer
#         address = order.addresses.first() if order.addresses.exists() else None

#         customer_name = f"{customer.first_name} {customer.last_name}" if customer else "-"
#         customer_email = customer.email if customer and customer.email else "-"
#         customer_phone = order.contact_phone if order.contact_phone else "-"
#         address_details = f"{address.address1}, {address.city}" if address and address.address1 else "-"

#         combined_data.append({
#             "order": order,
#             "customer_name": customer_name,
#             "customer_email": customer_email,
#             "customer_phone": customer_phone,
#             "address_details": address_details
#         })

#     return render(request, 'dashboard.html', {
#         'combined_data': combined_data
#     })


def landing_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('order_list') 
        else:
            error_message = "Incorrect username or password."
            return render(request, 'login.html', {
                'form': form,
                'error_message': error_message
            })
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            success_count = 0
            duplicate_count = 0
            update_count = 0
            error_count = 0
            error_messages = []

            try:
                csv_file = TextIOWrapper(uploaded_file.file, encoding='utf-8')
                reader = csv.DictReader(csv_file)

                # Validate CSV has required columns
                required_columns = ['Name', 'Email', 'Created at', 'Billing Phone', 'Total', 'Billing Name']
                if not all(col in reader.fieldnames for col in required_columns):
                    messages.error(request, "CSV is missing required columns")
                    return redirect('upload_csv')

                store, _ = Stores.objects.get_or_create(
                    name="Frankshirt",
                    shopify_domain="frankshirt.co.in",
                    defaults={
                        'access_token': 'dummy_token',
                        'created_at': timezone.now(),
                        'updated_at': timezone.now()
                    }
                )

                # First pass: Group all rows by order ID
                orders_data = {}
                for row_num, row in enumerate(reader, 1):
                    try:
                        order_id = row['Name'].replace('#', '').strip()
                        if not order_id:
                            continue
                            
                        if order_id not in orders_data:
                            orders_data[order_id] = {
                                'main_data': row,
                                'line_items': []
                            }
                        
                        # Only add as line item if it has product info
                        if row.get('Lineitem name'):
                            orders_data[order_id]['line_items'].append(row)
                    except Exception as e:
                        error_count += 1
                        error_messages.append(f"Row {row_num} grouping error: {str(e)}")
                        continue

                # Second pass: Process each order with its line items
                for order_id, order_data in orders_data.items():
                    try:
                        row = order_data['main_data']
                        line_items = order_data['line_items']
                        
                        # Parse customer name properly - prioritize Billing Name
                        billing_name = row.get('Billing Name', '').strip()
                        if not billing_name:
                            billing_name = row.get('Name', '').replace('#', '').strip()
                        
                        name_parts = [part for part in billing_name.split() if part]
                        first_name = name_parts[0] if name_parts else ''
                        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                        # Parse dates
                        try:
                            created_at = datetime.strptime(row['Created at'], '%Y-%m-%d %H:%M:%S %z')
                        except:
                            created_at = timezone.now()
                            logger.warning(f"Using current time for order {order_id} created_at")

                        paid_at = None
                        if row.get('Paid at'):
                            try:
                                paid_at = datetime.strptime(row['Paid at'], '%Y-%m-%d %H:%M:%S %z')
                            except:
                                logger.warning(f"Couldn't parse Paid at for order {order_id}")

                        # Get or create customer
                        email = row.get('Email', '').strip() or None
                        customer = None
                        
                        if email or billing_name:
                            customer, created = Customers.objects.get_or_create(
                                store=store,
                                email=email if email else f"no-email-{order_id}@frankshirt.com",
                                defaults={
                                    'first_name': first_name,
                                    'last_name': last_name,
                                    'verified_email': False,
                                    'currency': row.get('Currency', 'INR'),
                                    'created_at': created_at,
                                    'updated_at': created_at,
                                }
                            )
                            
                            if not created:
                                if not customer.first_name and first_name:
                                    customer.first_name = first_name
                                    customer.last_name = last_name
                                    customer.save()

                        # Calculate totals from line items
                        subtotal = sum(
                            safe_decimal(item.get('Lineitem price', '0')) * 
                            int(item.get('Lineitem quantity', 1))
                            for item in line_items
                        )
                        discount = safe_decimal(row.get('Discount Amount', '0'))
                        shipping = safe_decimal(row.get('Shipping', '0'))
                        taxes = safe_decimal(row.get('Taxes', '0'))
                        total = subtotal - discount + shipping + taxes

                        # Check for existing order
                        existing_order = Orders.objects.filter(store=store, remote_id=order_id).first()
                        if existing_order:
                            # Update existing order
                            existing_order.name = billing_name
                            existing_order.contact_email = email
                            existing_order.contact_phone = row.get('Billing Phone', '')
                            existing_order.financial_status = row.get('Financial Status', 'pending')
                            existing_order.total_price = total
                            existing_order.subtotal_price = subtotal
                            existing_order.total_tax = taxes
                            existing_order.total_discounts = discount
                            existing_order.shipping_price = shipping
                            existing_order.tags = row.get('Tags', '')
                            existing_order.updated_at = timezone.now()
                            existing_order.save()
                            
                            # Delete existing line items and recreate with sequential numbering
                            existing_order.lineitems.all().delete()
                            for index, item in enumerate(line_items, 1):
                                LineItems.objects.create(
                                    order=existing_order,
                                    sku=item.get('Lineitem sku', ''),
                                    remote_id=int(order_id) * 100 + index,  # Sequential numbering
                                    name=item.get('Lineitem name', ''),
                                    quantity=int(item.get('Lineitem quantity', 1)),
                                    price=safe_decimal(item.get('Lineitem price', '0')),
                                    fulfillment_status=item.get('Lineitem fulfillment status', ''),
                                    created_at=created_at,
                                    updated_at=created_at,
                                )
                            
                            update_count += 1
                            logger.debug(f"Updated order {order_id}")
                            continue

                        # Create new order
                        order = Orders(
                            store=store,
                            remote_id=order_id,
                            order_number=order_id,
                            name=billing_name,
                            contact_email=email,
                            contact_phone=row.get('Billing Phone', ''),
                            financial_status=row.get('Financial Status', 'pending'),
                            total_price=total,
                            subtotal_price=subtotal,
                            total_tax=taxes,
                            total_discounts=discount,
                            currency=row.get('Currency', 'INR'),
                            processed_at=paid_at,
                            created_at=created_at,
                            updated_at=created_at,
                            customer=customer,
                            tags=row.get('Tags', ''),
                            payment_gateway=row.get('Payment Method', ''),
                            shipping_title=row.get('Shipping Method', ''),
                            shipping_code=row.get('Shipping Province', ''),
                            shipping_price=shipping,
                        )
                        order.save()

                        # Create line items with sequential numbering
                        for index, item in enumerate(line_items, 1):
                            LineItems.objects.create(
                                order=order,
                                sku=item.get('Lineitem sku', ''),
                                remote_id=int(order_id) * 100 + index,  # Sequential numbering
                                name=item.get('Lineitem name', ''),
                                quantity=int(item.get('Lineitem quantity', 1)),
                                price=safe_decimal(item.get('Lineitem price', '0')),
                                fulfillment_status=item.get('Lineitem fulfillment status', ''),
                                created_at=created_at,
                                updated_at=created_at,
                            )

                        # Create address only if we have basic address info
                        if row.get('Billing Address1') or row.get('Billing City'):
                            Addresses.objects.create(
                                store=store,
                                customer=customer,
                                order=order,
                                first_name=first_name,
                                last_name=last_name,
                                address1=row.get('Billing Address1', ''),
                                address2=row.get('Billing Address2', ''),
                                city=row.get('Billing City', ''),
                                state=row.get('Billing Province', ''),
                                country=row.get('Billing Country', ''),
                                zip=row.get('Billing Zip', ''),
                                phone=row.get('Billing Phone', ''),
                                created_at=created_at,
                                updated_at=created_at,
                            )

                        success_count += 1
                        logger.info(f"Created order {order_id} for {first_name} {last_name}")

                    except Exception as e:
                        error_count += 1
                        error_msg = f"Order {order_id} error: {str(e)}"
                        error_messages.append(error_msg)
                        logger.error(error_msg, exc_info=True)
                        continue

                # Final status message
                message = (
                    f"Import complete: {success_count} new, {update_count} updated, "
                    f"{duplicate_count} duplicates skipped, {error_count} errors"
                )
                messages.success(request, message)
                
                if error_messages:
                    messages.warning(request, f"First error: {error_messages[0]}")
                    if len(error_messages) > 1:
                        messages.warning(request, f"... plus {len(error_messages)-1} more errors")

                return redirect('order_list')

            except Exception as e:
                logger.error(f"CSV processing failed: {str(e)}", exc_info=True)
                messages.error(request, f"Failed to process file: {str(e)}")
                return redirect('upload_csv')
    else:
        form = UploadForm()
    
    return render(request, 'upload.html', {'form': form})

from django.contrib.auth import logout
from django.shortcuts import redirect

def custom_logout(request):
    logout(request)
    return redirect('login') 

from django.http import HttpResponse
import csv

def download_orders(request):
    status_filter = request.GET.get('status', None)
    flag_filter = request.GET.get('flag', None)
    
    # Create the HttpResponse object with CSV header
    filename = "orders"
    if status_filter:
        filename = f"{status_filter}_orders"
    elif flag_filter:
        filename = f"{flag_filter}_flag_orders"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    
    # Create a CSV writer
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Order Number', 'Customer Name', 'Email', 'Phone', 
        'Address', 'Items', 'Quantity', 'Price', 'Total Price', 
        'Status', 'Created At', 'Flag Status'
    ])
    
    # Get filtered orders (same logic as order_list)
    orders = Orders.objects.select_related('customer').prefetch_related(
        'addresses', 'lineitems'
    ).all().order_by('-created_at')
    
    if status_filter == 'paid':
        orders = orders.filter(financial_status__in=['paid', 'prepaid'])
    elif status_filter == 'pending':
        orders = orders.exclude(financial_status__in=['paid', 'prepaid'])
    elif flag_filter in ['red', 'green']:
        all_orders = list(orders)
        flagged_orders = []
        
        for order in all_orders:
            is_flagged = False
            address = order.addresses.first() if order.addresses.exists() else None
            
            # Your existing flag logic here
            if address and len(address.address1 or '') < 20:
                is_flagged = True
            if order.contact_phone and len(''.join(filter(str.isdigit, order.contact_phone))) < 10:
                is_flagged = True
            # Add other flag conditions as needed
            
            if (flag_filter == 'red' and is_flagged) or (flag_filter == 'green' and not is_flagged):
                flagged_orders.append(order.id)
        
        orders = orders.filter(id__in=flagged_orders)
    
    # Write data rows
    for order in orders:
        customer = order.customer
        address = order.addresses.first() if order.addresses.exists() else None
        line_items = order.lineitems.all()
        
        # Customer info
        customer_name = f"{customer.first_name} {customer.last_name}" if customer else "N/A"
        customer_email = customer.email if customer else "N/A"
        customer_phone = order.contact_phone if order.contact_phone else "N/A"
        
        # Address info
        address_details = f"{address.address1}, {address.city}, {address.state}, {address.country} - {address.zip}" if address else "N/A"
        
        # Determine flag status
        is_flagged = False
        if address and len(address.address1 or '') < 20:
            is_flagged = True
        if order.contact_phone and len(''.join(filter(str.isdigit, order.contact_phone))) < 10:
            is_flagged = True
        flag_status = "Red Flag" if is_flagged else "Green Flag"
        
        # Line items
        for item in line_items:
            writer.writerow([
                order.order_number,
                customer_name,
                customer_email,
                customer_phone,
                address_details,
                item.name,
                item.quantity,
                item.price,
                order.total_price,
                order.financial_status,
                order.created_at.strftime("%Y-%m-%d %H:%M"),
                flag_status
            ])
        
        # Write an empty row if no line items
        if not line_items:
            writer.writerow([
                order.order_number,
                customer_name,
                customer_email,
                customer_phone,
                address_details,
                "No items",
                "",
                "",
                order.total_price,
                order.financial_status,
                order.created_at.strftime("%Y-%m-%d %H:%M"),
                flag_status
            ])
    
    return response