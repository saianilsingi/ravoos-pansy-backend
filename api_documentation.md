# Ravoos Pansy – API Documentation

---

## Overview

The **Ravoos Pansy** project is an e‑commerce backend built with **Django** and **Django REST Framework**. It provides RESTful endpoints for user management, product catalog, shopping cart, order processing, and coupons.

---

## Apps Summary

| App | Purpose |
|-----|---------|
| `users` | Authentication, user profile, and address management |
| `products` | Product catalog and category browsing |
| `cart` | Shopping‑cart operations |
| `orders` | Checkout, order history, and billing |
| `coupons` | Coupon definitions (no public API yet) |

---

## Authentication

All endpoints under **`/api/`** (except signup and login) require **Token Authentication**. Include the header:

```
Authorization: Token <your-token>
```

| Role | Description |
|------|-------------|
| **Guest** | Not authenticated – can only access signup and login |
| **User** | Authenticated regular user – can use cart, checkout, view orders, manage own addresses |
| **Admin** | `is_staff=True` – has additional admin endpoints for product management |

---

## Users (`users` app)

### 1. Sign‑up
- **Method:** `POST`
- **Endpoint:** `/api/auth/signup/`
- **Auth required:** No
- **Request body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "strongpassword"
}
```
- **Success (201):**
```json
{"message": "Signup successful"}
```
- **Errors:** 400 validation errors

### 2. Login
- **Method:** `POST`
- **Endpoint:** `/api/auth/login/`
- **Auth required:** No
- **Request body:**
```json
{
  "email": "user@example.com",
  "password": "strongpassword"
}
```
- **Success (200):**
```json
{
  "token": "<token>",
  "user": {"id": 1, "email": "user@example.com", "name": "John Doe", "role": "user"}
}
```
- **Errors:** 400 – invalid credentials

### 3. Get Current User
- **Method:** `GET`
- **Endpoint:** `/api/auth/me/`
- **Auth required:** Yes (Token)
- **Access:** User / Admin
- **Success (200):**
```json
{"id":1,"email":"user@example.com","name":"John Doe","role":"user"}
```

### 4. Address CRUD
- **List / Create**
  - **Method:** `GET` / `POST`
  - **Endpoint:** `/api/auth/addresses/`
  - **Auth required:** Yes
  - **Request (POST) example:**
    ```json
    {
      "full_name": "John Doe",
      "phone": "1234567890",
      "street": "123 Main St",
      "city": "City",
      "state": "State",
      "pincode": "123456",
      "landmark": "Near Park",
      "is_default": true
    }
    ```
  - **Success (GET):** List of address objects
  - **Success (POST 201):** Created address object

- **Update**
  - **Method:** `PUT`
  - **Endpoint:** `/api/auth/addresses/<int:pk>/`
  - **Auth required:** Yes
  - **Request body:** Same fields as create (partial updates allowed)

- **Delete**
  - **Method:** `DELETE`
  - **Endpoint:** `/api/auth/addresses/<int:pk>/delete/`
  - **Auth required:** Yes

---

## Products (`products` app)

### 1. List Categories
- **Method:** `GET`
- **Endpoint:** `/api/categories/`
- **Auth required:** No (public)
- **Success (200):**
```json
[{"id":1,"name":"Electronics","slug":"electronics"}, ...]
```

### 2. List Products
- **Method:** `GET`
- **Endpoint:** `/api/products/`
- **Auth required:** No
- **Query params:**
  - `category` – filter by category slug
  - `search` – case‑insensitive name search
- **Success (200):** List of product objects (read serializer)

### 3. Product Detail
- **Method:** `GET`
- **Endpoint:** `/api/products/<int:pk>/`
- **Auth required:** No
- **Success (200):** Single product object

### 4. Admin – Create Product
- **Method:** `POST`
- **Endpoint:** `/api/admin/products/`
- **Auth required:** Yes (Token) – **Admin only** (`IsAdmin` permission)
- **Request body (example):**
```json
{
  "name": "Smartphone",
  "price": "199.99",
  "category": 2,
  "description": "Latest model",
  "is_active": true
}
```
- **Success (201):** Created product object

### 5. Admin – Update Product
- **Method:** `PUT`
- **Endpoint:** `/api/admin/products/<int:pk>/`
- **Auth required:** Admin
- **Request body:** Same as create (partial allowed)

### 6. Admin – Delete Product
- **Method:** `DELETE`
- **Endpoint:** `/api/admin/products/<int:pk>/delete/`
- **Auth required:** Admin
- **Success (200):** `{"message": "Product deleted"}` (implicit)

---

## Cart (`cart` app)

### 1. View Cart Items
- **Method:** `GET`
- **Endpoint:** `/api/cart/`
- **Auth required:** Yes (User)
- **Success (200):** List of cart items with product details and quantity

### 2. Add to Cart
- **Method:** `POST`
- **Endpoint:** `/api/cart/add/`
- **Auth required:** Yes
- **Request body:**
```json
{"product_id": 5, "quantity": 2}
```
- **Success (200):** `{"message": "Added to cart"}`
- **Errors:** 404 product not found, 403 admin not allowed

### 3. Update Cart Item Quantity
- **Method:** `PUT`
- **Endpoint:** `/api/cart/update/`
- **Auth required:** Yes
- **Request body:**
```json
{"item_id": 12, "quantity": 3}
```
- **Success (200):** `{"message": "Cart updated successfully"}`
- **If quantity ≤ 0:** item is removed, message "Item removed from cart"

### 4. Remove Cart Item
- **Method:** `DELETE`
- **Endpoint:** `/api/cart/remove/<int:pk>/`
- **Auth required:** Yes
- **Success (200):** `{"message": "Item removed"}`

### 5. Clear Cart
- **Method:** `DELETE`
- **Endpoint:** `/api/cart/clear/`
- **Auth required:** Yes
- **Success (200):** `{"message": "Cart cleared"}`

---

## Orders (`orders` app)

### 1. Checkout (Create Order)
- **Method:** `POST`
- **Endpoint:** `/api/orders/checkout/`
- **Auth required:** Yes
- **Request body:**
```json
{
  "address_id": 3,
  "coupon": "WELCOME10"   // optional
}
```
- **Process:**
  1. Validates non‑empty cart
  2. Validates address belongs to user
  3. Calculates **subtotal**, **GST (5%)**, applies coupon discount, computes **total**
  4. Creates `Order` and related `OrderItem`s
  5. Clears the cart
- **Success (200):**
```json
{
  "order_id": 42,
  "subtotal": "100.00",
  "gst": "5.00",
  "discount": "10.00",
  "total": "95.00"
}
```
- **Errors:** 400 cart empty, invalid address, invalid coupon

### 2. List Orders (Order History)
- **Method:** `GET`
- **Endpoint:** `/api/orders/`
- **Auth required:** Yes
- **Success (200):** List of orders (uses `OrderSerializer`)

### 3. Order Detail (Bill)
- **Method:** `GET`
- **Endpoint:** `/api/orders/<int:pk>/`
- **Auth required:** Yes
- **Success (200):** Full order data including `items` array

### 4. Delete Single Order
- **Method:** `DELETE`
- **Endpoint:** `/api/orders/<int:pk>/delete/`
- **Auth required:** Yes
- **Success (200):** `{"message": "Order deleted"}`

### 5. Delete All Orders
- **Method:** `DELETE`
- **Endpoint:** `/api/orders/delete-all/`
- **Auth required:** Yes
- **Success (200):** `{"message": "All orders deleted"}`

---

## Coupons (`coupons` app)

*No public API endpoints are defined yet.* The `Coupon` model exists and can be used programmatically during checkout.

---

## End‑to‑End Test Flow

1. **Create a product** (admin) – `POST /api/admin/products/`
2. **Add product to cart** – `POST /api/cart/add/` with `product_id`
3. **Create an address** – `POST /api/auth/addresses/`
4. **Checkout** – `POST /api/orders/checkout/` with `address_id` (and optional `coupon`)
5. **View order list** – `GET /api/orders/`
6. **View order detail / bill** – `GET /api/orders/<order_id>/`
7. **(Optional) Delete order** – `DELETE /api/orders/<order_id>/delete/`

---

## Common Pitfalls & Tips

- **Admin vs User:** Admin endpoints reject non‑staff users with **403 Forbidden**.
- **Cart restrictions:** Admin users cannot use cart endpoints – they receive a 403 response.
- **Quantity handling:** Updating a cart item to `0` or a negative number automatically removes the item.
- **Coupon validation:** Only active coupons are accepted; an invalid code returns **400**.
- **Address ownership:** The address ID must belong to the requesting user; otherwise a **400** error is returned.
- **Token expiration:** If you receive **401 Unauthorized**, obtain a fresh token via the login endpoint.

---

*Documentation generated automatically from the existing Django project code.*
