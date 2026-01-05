# Ravoos Pansy – Database / Model Documentation

---

## Overview

The project consists of **5 apps** that together model a simple e‑commerce system. Below is a complete description of every model, its fields, and how the models relate to each other.

---

## 1. `users` App

### Model: `User`

**Purpose** – Represents a registered person who can log in, browse products, manage a cart, place orders, and store addresses.

**Fields**
- `email` – `EmailField`, unique. Used as the login identifier.
- `name` – `CharField(max_length=100)`. Human‑readable name of the user.
- `is_active` – `BooleanField(default=True)`. Marks whether the account is usable.
- `is_staff` – `BooleanField(default=False)`. Flags admin users; gives access to admin‑only endpoints.
- `date_joined` – `DateTimeField(auto_now_add=True)`. Timestamp of account creation.

**Relationships** – No foreign keys. The model is referenced by other models via `settings.AUTH_USER_MODEL`.

---

### Model: `Address`

**Purpose** – Stores a shipping address belonging to a user. Used during checkout to capture where the order should be delivered.

**Fields**
- `user` – `ForeignKey(User, on_delete=CASCADE, related_name="addresses")`. Each address belongs to one user; deleting the user removes all their addresses.
- `full_name` – `CharField(max_length=100)`. Name of the recipient.
- `phone` – `CharField(max_length=15)`. Contact phone number.
- `street` – `TextField()`. Street address (can be multiline).
- `city` – `CharField(max_length=50)`.
- `state` – `CharField(max_length=50)`.
- `pincode` – `CharField(max_length=10)`.
- `landmark` – `CharField(max_length=100, blank=True)` – optional extra location info.
- `is_default` – `BooleanField(default=False)`. Marks the primary address for the user.
- `created_at` – `DateTimeField(auto_now_add=True)`.

**Relationships** – One‑to‑many from `User` (a user can have many addresses). `related_name="addresses"` lets you access them via `user.addresses.all()`.

---

## 2. `products` App

### Model: `Category`

**Purpose** – Groups products into logical sections (e.g., electronics, clothing). Allows filtering and navigation.

**Fields**
- `name` – `CharField(max_length=50, unique=True)`. Human readable name.
- `slug` – `SlugField(unique=True)`. URL‑friendly identifier.
- `theme` – `CharField(max_length=30)`. Arbitrary tag such as "food", "drinks", etc.
- `is_active` – `BooleanField(default=True)`. Soft‑delete flag; inactive categories are hidden.

**Relationships** – No foreign keys. `Product` points to `Category`.

---

### Model: `Product`

**Purpose** – Represents an item that can be sold.

**Fields**
- `name` – `CharField(max_length=150)`.
- `description` – `TextField(blank=True)`.
- `price` – `DecimalField(max_digits=8, decimal_places=2)` – monetary value.
- `category` – `ForeignKey(Category, on_delete=CASCADE, related_name="products")`. Deleting a category removes its products.
- `image` – `ImageField(upload_to="products/", blank=True, null=True)` – optional picture.
- `is_active` – `BooleanField(default=True)` – hide discontinued items.
- `created_at` – `DateTimeField(auto_now_add=True)`.

**Relationships** – Many‑to‑one to `Category`. `related_name="products"` enables `category.products.all()`.

---

## 3. `cart` App

### Model: `CartItem`

**Purpose** – Holds a product that a user intends to purchase, together with the desired quantity.

**Fields**
- `user` – `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="cart_items")`. Each cart item belongs to a single user; deleting the user clears the cart.
- `product` – `ForeignKey(Product, on_delete=CASCADE)`. The product being added. Deleting the product also removes the cart entry.
- `quantity` – `PositiveIntegerField(default=1)`.
- `added_at` – `DateTimeField(auto_now_add=True)`.

**Constraints** – `unique_together = ("user", "product")` ensures a user cannot have duplicate entries for the same product.

**Relationships** – One‑to‑many from `User` (`user.cart_items.all()`). Many‑to‑one to `Product`.

---

## 4. `orders` App

### Model: `Order`

**Purpose** – Captures a completed purchase, including billing totals and a snapshot of the shipping address.

**Fields**
- `user` – `ForeignKey(settings.AUTH_USER_MODEL, on_delete=CASCADE, related_name="orders")`. Owner of the order.
- `subtotal` – `DecimalField(max_digits=10, decimal_places=2)` – sum of product prices × quantities before tax/discount.
- `gst` – `DecimalField(max_digits=10, decimal_places=2)` – tax amount (5% in the checkout view).
- `discount` – `DecimalField(max_digits=10, decimal_places=2, default=0)` – coupon discount applied.
- `total` – `DecimalField(max_digits=10, decimal_places=2)` – final amount charged.
- `address_text` – `TextField()` – **snapshot** of the address at order time (so later address changes do not affect past orders).
- `status` – `CharField(max_length=20, choices=[('pending','Pending'),('delivered','Delivered'),('cancelled','Cancelled')], default='pending'`.
- `created_at` – `DateTimeField(auto_now_add=True)`.

**Relationships** – One‑to‑many to `OrderItem` via `related_name="items"`.

---

### Model: `OrderItem`

**Purpose** – Represents a single line in an order (product, quantity, price at purchase time).

**Fields**
- `order` – `ForeignKey(Order, on_delete=CASCADE, related_name="items")`. Deleting the order removes its items.
- `product` – `ForeignKey(Product, on_delete=SET_NULL, null=True)`. The product purchased. `SET_NULL` preserves order history even if the product is later removed.
- `quantity` – `PositiveIntegerField()`.
- `price` – `DecimalField(max_digits=8, decimal_places=2)` – price per unit at the moment of purchase.

**Relationships** – Many‑to‑one to `Order` and to `Product`.

---

## 5. `coupons` App

### Model: `Coupon`

**Purpose** – Defines a discount code that can be applied during checkout.

**Fields**
- `code` – `CharField(max_length=20, unique=True)`. The string the user enters.
- `discount_amount` – `DecimalField(max_digits=8, decimal_places=2)`. Fixed amount subtracted from the total.
- `is_active` – `BooleanField(default=True)`. Deactivates a coupon without deleting it.
- `valid_from` – `DateTimeField()` – start of validity period.
- `valid_to` – `DateTimeField()` – end of validity period.
- `usage_limit` – `IntegerField(null=True, blank=True)` – optional maximum number of uses.
- `used_count` – `IntegerField(default=0)` – tracks how many times the coupon has been applied.

**Relationships** – No foreign keys. Used only by the checkout view.

---

## Relationships Overview (Text Diagram)
```
User
├── addresses (Address)
├── cart_items (CartItem) ──> Product ──> Category
└── orders (Order)
    └── items (OrderItem) ──> Product (SET_NULL on delete)
```

## Data Flow Explanation (Plain Language)

1. **Add to Cart**
   - A logged‑in user selects a product.
   - The `CartItem` record is created linking the `User` and the `Product` with a quantity.
   - If the same product is added again, the existing `CartItem` quantity is increased because of the `unique_together` constraint.

2. **Checkout**
   - The checkout view reads all `CartItem`s for the user.
   - It validates the supplied address (`Address` belonging to the user).
   - Sub‑total is calculated from each `CartItem` (`product.price * quantity`).
   - GST (5 %) and any coupon discount are added/subtracted.
   - An `Order` record is created storing the totals and a **text snapshot** of the address (`address_text`).
   - For every `CartItem`, an `OrderItem` is created linking the new `Order` to the `Product`. The price at purchase time is stored, so future price changes do not affect the historic order.
   - After the `Order` and its `OrderItem`s are saved, all the user’s `CartItem`s are deleted (cart cleared).

3. **Order History**
   - The user can list their `Order`s via `user.orders.all()`.
   - Each order shows its line items (`order.items.all()`) with the product name, quantity, and price captured at purchase time.
   - The stored `address_text` ensures the bill always shows the address used at checkout, even if the user later edits or deletes the original `Address`.

## Database Tables Overview
| Table | Stores | Core / Supporting |
|-------|--------|-------------------|
| `users_user` | Users (email, name, flags) | Core |
| `users_address` | Shipping addresses linked to users | Supporting |
| `products_category` | Product categories | Core |
| `products_product` | Product catalog (price, image, category) | Core |
| `cart_cartitem` | Items a user has placed in their cart | Supporting |
| `orders_order` | Orders with totals, status, address snapshot | Core |
| `orders_orderitem` | Individual line items of an order | Supporting |
| `coupons_coupon` | Discount codes | Supporting |

## Real‑World Scenarios

- **User deletes an address** – The address row is removed (`on_delete=CASCADE`). Existing orders keep the address because the order stores a plain‑text copy (`address_text`).
- **Product price changes** – New `Product.price` values affect future cart calculations and new orders. Past `OrderItem.price` values remain unchanged, preserving historical accuracy.
- **User deletes their account** – All related rows (`addresses`, `cart_items`, `orders`, and through cascade `order_items`) are deleted because every foreign key uses `on_delete=CASCADE`. This fully cleans up the user's data.
- **Product is removed** – Deleting a `Product` cascades to `CartItem` (removing it from any carts) and sets `product` to `NULL` on existing `OrderItem`s, so the order still exists but the product reference is blank.
- **Coupon becomes inactive** – Checkout will reject it (`Coupon.objects.get(..., is_active=True)`), leaving existing orders unchanged because the discount amount is already stored in the `Order`.

---

*Documentation generated by analyzing the existing Django models. No code changes were made.*
