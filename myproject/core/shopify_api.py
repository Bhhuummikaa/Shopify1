# # import requests
# # from .models import Stores, Customers, Orders, LineItems, Addresses
# # from django.utils.dateparse import parse_datetime

# # def fetch_shopify_orders(store):
# #     url = "https://0f24c3-4a.myshopify.com/admin/api/2023-04/orders.json"
# #     headers = {
# #         "X-Shopify-Access-Token": store.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
# #     }

# #     response = requests.get(url, headers=headers)
# #     if response.status_code != 200:
# #         raise Exception(f"Error fetching orders: {response.text}")

# #     orders_data = response.json().get("orders", [])

# #     for data in orders_data:
# #         # Customer
# #         customer_data = data.get("customer")
# #         customer = None
# #         if customer_data:
# #             customer, _ = Customers.objects.update_or_create(
# #                 store=store,
# #                 remote_id=customer_data["id"],
# #                 defaults={
# #                     "email": customer_data.get("email"),
# #                     "first_name": customer_data.get("first_name"),
# #                     "last_name": customer_data.get("last_name"),
# #                     "verified_email": customer_data.get("verified_email"),
# #                     "currency": customer_data.get("currency"),
# #                     "created_at": parse_datetime(customer_data.get("created_at")),
# #                     "updated_at": parse_datetime(customer_data.get("updated_at")),
# #                 },
# #             )

# #         # Order
# #         order_obj, _ = Orders.objects.update_or_create(
# #             store=store,
# #             remote_id=data["id"],
# #             defaults={
# #                 "order_number": data.get("order_number"),
# #                 "name": data.get("name"),
# #                 "contact_email": data.get("email"),
# #                 "contact_phone": data.get("phone"),
# #                 "financial_status": data.get("financial_status"),
# #                 "total_price": data.get("total_price"),
# #                 "subtotal_price": data.get("subtotal_price"),
# #                 "total_tax": data.get("total_tax"),
# #                 "total_discounts": data.get("total_discounts"),
# #                 "currency": data.get("currency"),
# #                 "processed_at": parse_datetime(data.get("processed_at")),
# #                 "created_at": parse_datetime(data.get("created_at")),
# #                 "updated_at": parse_datetime(data.get("updated_at")),
# #                 "tags": data.get("tags"),
# #                 "payment_gateway": data.get("gateway"),
# #                 "shipping_title": data.get("shipping_lines")[0].get("title") if data.get("shipping_lines") else None,
# #                 "shipping_code": data.get("shipping_lines")[0].get("code") if data.get("shipping_lines") else None,
# #                 "shipping_price": data.get("shipping_lines")[0].get("price") if data.get("shipping_lines") else None,
# #                 "customer": customer
# #             },
# #         )

# #         # Line Items
# #         for item in data.get("line_items", []):
# #             LineItems.objects.update_or_create(
# #                 order_id=order_obj.id,
# #                 remote_id=item["id"],
# #                 defaults={
# #                     "sku": item.get("sku"),
# #                     "name": item.get("name"),
# #                     "quantity": item.get("quantity"),
# #                     "price": item.get("price"),
# #                     "fulfillment_status": item.get("fulfillment_status"),
# #                     "created_at": parse_datetime(item.get("created_at")),
# #                     "updated_at": parse_datetime(item.get("updated_at")),
# #                 }
# #             )

# #         # Shipping Address
# #         address_data = data.get("shipping_address")
# #         if address_data:
# #             Addresses.objects.update_or_create(
# #                 store=store,
# #                 remote_id=address_data["id"],
# #                 defaults={
# #                     "customer": customer,
# #                     "order_id": order_obj.id,
# #                     "first_name": address_data.get("first_name"),
# #                     "last_name": address_data.get("last_name"),
# #                     "address1": address_data.get("address1"),
# #                     "address2": address_data.get("address2"),
# #                     "city": address_data.get("city"),
# #                     "state": address_data.get("province"),
# #                     "country": address_data.get("country"),
# #                     "zip": address_data.get("zip"),
# #                     "phone": address_data.get("phone"),
# #                     "created_at": parse_datetime(address_data.get("created_at")),
# #                     "updated_at": parse_datetime(address_data.get("updated_at")),
# #                 }
# #             )
# import requests
# from .models import Stores

# def fetch_stores_from_api():
#     api_url = "https://0f24c3-4a.myshopify.com/admin/api/2023-10/orders.json?"  # Your API URL
#     access_token = "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"          # Your token for auth

#     headers = {
#         "Authorization": f"Token {access_token}",
#         "Accept": "application/json",
#     }

#     response = requests.get(api_url, headers=headers)

#     if response.status_code == 200:
#         data = response.json()  # Assuming list of stores returned
#         for store_data in data:
#             # Save or update in local DB
#             store, created = Stores.objects.update_or_create(
#                 id=store_data['id'],
#                 defaults={
#                     'name': store_data['name'],
#                     'shopify_domain': store_data['shopify_domain'],
#                     'access_token': store_data['access_token'],
#                     # Add other fields as needed
#                 }
#             )
#         return True
#     else:
#         print(f"API call failed: {response.status_code} - {response.text}")
#         return False
