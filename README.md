# Ravoos Pansy -- Backend

A production-grade Django REST Framework backend powering a full-stack e-commerce platform. Built with enterprise-level patterns including atomic inventory management, idempotent payment processing, hierarchical category trees, and comprehensive admin analytics.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Design Principles](#design-principles)
- [Data Model Overview](#data-model-overview)
- [Security Considerations](#security-considerations)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Database Design](#database-design)
- [Payment Flow](#payment-flow)
- [Stock Concurrency](#stock-concurrency)
- [API Reference](#api-reference)
- [Admin System](#admin-system)
- [Analytics Engine](#analytics-engine)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Production Notes](#production-notes)
- [Roadmap](#roadmap)

---

## Architecture Overview

The backend follows a modular, app-based Django architecture with clear separation of concerns across 8 domain-specific applications. Each app encapsulates its own models, serializers, views, and URL configuration.

```
ravoos_pansy/                 # Project configuration
    settings.py               # Django settings with environment-based config
    urls.py                   # Root URL router
    wsgi.py / asgi.py         # Server entry points

users/                        # Authentication and address management
products/                     # Catalog with hierarchical categories
cart/                         # Shopping cart operations
orders/                       # Order processing and lifecycle
payments/                     # Razorpay integration and fulfillment
coupons/                      # Discount coupon system
reviews/                      # Product reviews with aggregated ratings
wishlist/                     # User wishlist management
analytics/                    # Admin dashboard reporting
```

Key architectural decisions:

- **Atomic stock management** using Django F() expressions to prevent overselling under concurrent load
- **Row-level locking** via `select_for_update()` for idempotent payment verification
- **Database-level constraints** (CHECK, UNIQUE) as the last line of defense for data integrity
- **Denormalized aggregates** on Product (avg_rating, review_count) for read performance
- **Snapshot pattern** for payment data to preserve order integrity regardless of future catalog changes
- **Single-query tree building** for hierarchical categories with BFS traversal

---

## Design Principles

- Data integrity over convenience
- Database-level constraints as the final safeguard
- Idempotent and concurrency-safe payment flow
- Optimized read-heavy operations via denormalization
- Clear separation between public and admin APIs
- Scalability-first API design with pagination and filtering

---

## Data Model Overview

```
User → CartItem → Product
User → Payment → Order → OrderItem
User → Review → Product
User → WishlistItem → Product
Category (self-referencing tree) → Product
```

---

## Security Considerations

- Token-based authentication with per-request validation
- Role-based access control via custom `IsAdmin` permission class
- Server-side payment amount calculation (client-provided amounts are never trusted)
- Razorpay webhook signature verification using HMAC
- Database constraints preventing invalid data states (negative stock, duplicate reviews)
- Stock modification is restricted to atomic fulfillment and cancellation logic

---

## Tech Stack

| Layer             | Technology                            |
| ----------------- | ------------------------------------- |
| Framework         | Django 6.0                            |
| API Layer         | Django REST Framework 3.16.1          |
| Database          | PostgreSQL (via psycopg2-binary)      |
| Authentication    | Token-based (DRF TokenAuthentication) |
| Payment Gateway   | Razorpay                              |
| CORS              | django-cors-headers 4.9.0             |
| Environment       | python-dotenv, dj-database-url        |
| Production Server | Gunicorn                              |
| Image Processing  | Pillow 12.1.0                         |

---

## Features

### Authentication and Users

- Custom User model with email-based authentication (no username field)
- Token-based auth with automatic token creation on login
- User profile management (name updates)
- Address CRUD with default address designation
- Role-based access control (admin vs customer)

### Product Catalog

- Full product CRUD with image URLs, pricing, and stock tracking
- Hierarchical category system with self-referencing parent-child relationships
- SEO-friendly category slug paths (e.g., `clothes/men/shirts`)
- Single-query nested tree generation via BFS
- Category descendant resolution for inclusive filtering
- Circular parent prevention in category serializer validation

### Cart System

- Per-user cart with product quantity management
- Add, update quantity, remove individual items, and bulk clear
- Unique constraint ensuring one cart entry per user per product

### Order Processing

- Order creation with line-item snapshots (price frozen at purchase time)
- Address text snapshot for order permanence
- Seven-stage status lifecycle: pending, placed, packing, shipped, out_for_delivery, delivered, cancelled
- Atomic stock restoration on order cancellation using F() expressions
- Admin status update endpoint with validation

### Payment Integration

- Razorpay order creation with server-side amount calculation
- Dual verification: client-side signature check and server-side webhook
- Idempotent payment fulfillment using `select_for_update()` row locking
- Cart snapshot and address snapshot frozen at payment intent creation
- Atomic order and order items creation within `transaction.atomic()`
- Automatic cart clearing after successful payment
- GST calculation (5%) applied server-side
- Coupon discount application during payment

### Coupon System

- Coupon CRUD for admins
- Client-side coupon validation endpoint
- Coupon code and discount amount stored on Payment record for analytics
- Active/inactive toggling

### Review System

- One review per user per product (database-enforced unique constraint)
- Rating range validation (1-5) via CHECK constraint and serializer
- Purchase verification: only users with delivered orders can review
- Automatic product rating refresh using Django aggregates (Avg, Count)
- Review edit and delete with rating recalculation
- Admin review moderation with paginated listing

### Wishlist

- Toggle-based add/remove with single endpoint
- Move-to-cart functionality
- Unique constraint per user per product
- Optimized indexes for user-scoped queries

### Admin APIs

- Separate admin endpoints for products, categories, orders, coupons, and reviews
- Product listing includes inactive products (hidden from public catalog)
- Category CRUD with referential integrity checks (prevents deletion of categories with children or assigned products)
- Order listing with status filtering and pagination (15 per page)
- Paginated review management

---

## Database Design

### Constraints and Integrity

| Model        | Constraint                           | Purpose                                       |
| ------------ | ------------------------------------ | --------------------------------------------- |
| Product      | `CHECK(stock >= 0)`                  | Prevents negative inventory at database level |
| Review       | `CHECK(rating >= 1 AND rating <= 5)` | Enforces valid rating range                   |
| Review       | `UNIQUE(user, product)`              | One review per user per product               |
| Category     | `UNIQUE(parent, slug)`               | Unique slugs within same parent               |
| CartItem     | `unique_together(user, product)`     | One cart entry per product per user           |
| WishlistItem | `UNIQUE(user, product)`              | One wishlist entry per product per user       |

### Indexes

| Model        | Index                                             | Purpose                              |
| ------------ | ------------------------------------------------- | ------------------------------------ |
| Category     | `category_parent_idx` on parent                   | Fast child lookups for tree building |
| Order        | `order_user_status` on (user, status)             | Efficient order filtering            |
| Review       | `review_product_recent` on (product, -created_at) | Fast product review listing          |
| WishlistItem | `wishlist_user_recent` on (user, -created_at)     | Fast user wishlist queries           |

### Denormalized Fields

Product maintains `avg_rating` and `review_count` as denormalized fields, updated atomically via `refresh_product_rating()` whenever reviews are created, updated, or deleted. This avoids expensive aggregate queries on every product listing.

---

## Payment Flow

```
1. Client calls POST /api/payments/create-intent/
   - Backend validates cart items and stock availability
   - Calculates subtotal + GST (5%) - coupon discount
   - Creates Razorpay order via server-side API call
   - Snapshots cart items and address into Payment record
   - Returns razorpay_order_id and amount to client

2. Client completes payment on Razorpay checkout

3. Client calls POST /api/payments/verify/
   - Backend acquires row lock: Payment.objects.select_for_update()
   - Verifies Razorpay signature using HMAC
   - Checks payment status is still "created" (idempotency)
   - Atomically: creates Order + OrderItems, deducts stock via F()
   - Clears user cart
   - Marks payment as "paid"

4. Razorpay sends webhook POST /api/payments/webhook/
   - Verifies webhook signature
   - Acquires row lock on Payment
   - If payment is still "created", runs same fulfillment logic
   - Handles async payment confirmation as backup
```

Both verification paths (client and webhook) are idempotent. If a payment has already been fulfilled, duplicate requests are safely ignored.

---

## Stock Concurrency

The system uses a multi-layered approach to prevent overselling:

**Layer 1 -- Atomic F() Expressions**

```python
updated = Product.objects.filter(
    id=item["product_id"],
    stock__gte=item["quantity"],
).update(stock=F("stock") - item["quantity"])
```

The WHERE clause (`stock__gte=quantity`) and the F() expression execute as a single atomic SQL UPDATE. If stock is insufficient, `updated` returns 0 and the entire transaction is rolled back.

**Layer 2 -- Database CHECK Constraint**

```python
CheckConstraint(check=Q(stock__gte=0), name="product_stock_non_negative")
```

Even if application logic has a bug, the database rejects any UPDATE that would result in negative stock.

**Layer 3 -- Row-Level Locking**

```python
payment = Payment.objects.select_for_update().get(...)
```

Acquires a row lock on the Payment record, preventing concurrent payment verification from creating duplicate orders.

**Layer 4 -- Atomic Stock Restoration**

When an order is cancelled, stock is restored using the same atomic F() pattern:

```python
Product.objects.filter(id=item.product_id).update(
    stock=F("stock") + item.quantity
)
```

---

## API Reference

### Authentication

| Method | Endpoint            | Auth   | Description          |
| ------ | ------------------- | ------ | -------------------- |
| POST   | `/api/auth/signup/` | Public | Register new user    |
| POST   | `/api/auth/login/`  | Public | Login, returns token |
| GET    | `/api/auth/me/`     | Token  | Get current user     |
| PUT    | `/api/auth/me/`     | Token  | Update user name     |

### Addresses

| Method | Endpoint                           | Auth  | Description         |
| ------ | ---------------------------------- | ----- | ------------------- |
| GET    | `/api/auth/addresses/`             | Token | List user addresses |
| POST   | `/api/auth/addresses/`             | Token | Create address      |
| PUT    | `/api/auth/addresses/<id>/`        | Token | Update address      |
| DELETE | `/api/auth/addresses/<id>/delete/` | Token | Delete address      |

### Products

| Method | Endpoint                | Auth   | Description                              |
| ------ | ----------------------- | ------ | ---------------------------------------- |
| GET    | `/api/products/`        | Public | List products (`?category=`, `?search=`) |
| GET    | `/api/products/<id>/`   | Public | Product detail                           |
| GET    | `/api/categories/`      | Public | List categories                          |
| GET    | `/api/categories/tree/` | Public | Nested category tree                     |

### Cart

| Method | Endpoint                 | Auth  | Description     |
| ------ | ------------------------ | ----- | --------------- |
| GET    | `/api/cart/`             | Token | Get cart items  |
| POST   | `/api/cart/add/`         | Token | Add to cart     |
| PUT    | `/api/cart/update/`      | Token | Update quantity |
| DELETE | `/api/cart/remove/<id>/` | Token | Remove item     |
| DELETE | `/api/cart/clear/`       | Token | Clear cart      |

### Orders

| Method | Endpoint                   | Auth  | Description         |
| ------ | -------------------------- | ----- | ------------------- |
| GET    | `/api/orders/`             | Token | List user orders    |
| GET    | `/api/orders/<id>/`        | Token | Order detail        |
| PATCH  | `/api/orders/<id>/status/` | Admin | Update order status |
| DELETE | `/api/orders/<id>/delete/` | Token | Delete order        |

### Payments

| Method | Endpoint                       | Auth   | Description              |
| ------ | ------------------------------ | ------ | ------------------------ |
| POST   | `/api/payments/create-intent/` | Token  | Create Razorpay order    |
| POST   | `/api/payments/verify/`        | Token  | Verify payment signature |
| POST   | `/api/payments/webhook/`       | Public | Razorpay webhook         |

### Reviews

| Method | Endpoint                                 | Auth   | Description              |
| ------ | ---------------------------------------- | ------ | ------------------------ |
| GET    | `/api/products/<id>/reviews/`            | Public | List product reviews     |
| GET    | `/api/products/<id>/reviews/can-review/` | Token  | Check review eligibility |
| POST   | `/api/products/<id>/reviews/create/`     | Token  | Create review            |
| PUT    | `/api/reviews/<id>/`                     | Token  | Update own review        |
| DELETE | `/api/reviews/<id>/delete/`              | Token  | Delete own review        |

### Wishlist

| Method | Endpoint                           | Auth  | Description                |
| ------ | ---------------------------------- | ----- | -------------------------- |
| GET    | `/api/wishlist/`                   | Token | List wishlist items        |
| POST   | `/api/wishlist/toggle/`            | Token | Toggle product in wishlist |
| DELETE | `/api/wishlist/<id>/`              | Token | Remove item                |
| POST   | `/api/wishlist/<id>/move-to-cart/` | Token | Move to cart               |

### Coupons

| Method | Endpoint                 | Auth  | Description          |
| ------ | ------------------------ | ----- | -------------------- |
| POST   | `/api/coupons/validate/` | Token | Validate coupon code |

---

## Admin System

All admin endpoints require `IsAdmin` permission (`user.is_staff = True`).

### Admin Products and Categories

| Method | Endpoint                             | Description                            |
| ------ | ------------------------------------ | -------------------------------------- |
| GET    | `/api/admin/products/`               | List all products (including inactive) |
| POST   | `/api/admin/products/`               | Create product                         |
| PUT    | `/api/admin/products/<id>/`          | Update product                         |
| DELETE | `/api/admin/products/<id>/delete/`   | Delete product                         |
| POST   | `/api/admin/categories/`             | Create category                        |
| PUT    | `/api/admin/categories/<id>/`        | Update category                        |
| DELETE | `/api/admin/categories/<id>/delete/` | Delete category                        |

### Admin Orders

| Method | Endpoint                  | Description                                 |
| ------ | ------------------------- | ------------------------------------------- |
| GET    | `/api/admin/orders/`      | Paginated order list (`?status=`, `?page=`) |
| GET    | `/api/admin/orders/<id>/` | Order detail with items                     |

### Admin Coupons

| Method | Endpoint                          | Description      |
| ------ | --------------------------------- | ---------------- |
| GET    | `/api/admin/coupons/`             | List all coupons |
| POST   | `/api/admin/coupons/`             | Create coupon    |
| PUT    | `/api/admin/coupons/<id>/`        | Update coupon    |
| DELETE | `/api/admin/coupons/<id>/delete/` | Delete coupon    |

### Admin Reviews

| Method | Endpoint                          | Description           |
| ------ | --------------------------------- | --------------------- |
| GET    | `/api/admin/reviews/`             | Paginated review list |
| DELETE | `/api/admin/reviews/<id>/delete/` | Delete review         |

---

## Analytics Engine

All analytics endpoints are under `/api/admin/analytics/` and require admin access.

**Overview** (`GET /overview/`) -- Aggregated platform metrics including total and daily revenue, orders, users, products, low stock count, average order value, and 30-day growth percentages.

**Revenue Chart** (`GET /revenue-chart/?days=30`) -- Daily revenue time series for the specified period. Returns date-amount pairs for chart rendering.

**Orders by Status** (`GET /orders-by-status/`) -- Order counts grouped by status for distribution visualization.

**Top Products** (`GET /top-products/?limit=5`) -- Products ranked by total quantity sold with revenue contribution.

**Coupon Analytics** (`GET /coupons/`) -- Per-coupon usage metrics: total times used, total discount given, generated revenue, and revenue per use.

**Wishlist Stats** (`GET /wishlist-stats/`) -- Most wishlisted products with counts and total wishlist items across the platform.

---

## Setup Instructions

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- pip

### Installation

```bash
cd ravoos-pansy-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your values

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

---

## Environment Variables

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgres://user:password@localhost:5432/ravoos_pansy

# Razorpay
RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
RAZORPAY_KEY_SECRET=your-razorpay-secret
RAZORPAY_WEBHOOK_SECRET=your-webhook-secret

# Admin (optional, for initial setup)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=secure-password
```

---

## Running Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Apply migrations
python manage.py migrate

# Run development server
python manage.py runserver

# Server starts at http://127.0.0.1:8000
# API base URL: http://127.0.0.1:8000/api/
```

### Verification

```bash
python manage.py check
```

---

## Production Notes

- Set `DEBUG=False` and configure `ALLOWED_HOSTS`
- Use Gunicorn as the WSGI server: `gunicorn ravoos_pansy.wsgi:application`
- Database connections use `conn_max_age=600` for connection pooling
- SSL is required for database connections when `DEBUG=False`
- Configure CORS allowed origins for your production frontend domain
- Set up Razorpay webhook URL pointing to `/api/payments/webhook/`
- Use a reverse proxy (Nginx) for SSL termination
- Monitor stock levels via the analytics overview endpoint

---

## Roadmap

- [ ] Email verification and password reset flow
- [ ] Multi-image product gallery
- [ ] Product variants (size, color)
- [ ] Inventory alerts and notifications
- [ ] Order tracking with delivery partner integration
- [ ] Rate limiting on authentication endpoints
- [ ] Elasticsearch integration for full-text product search
- [ ] Redis caching for category trees and analytics
- [ ] Automated test suite with pytest
- [ ] API documentation with drf-spectacular (OpenAPI)
- [ ] Percentage-based and multi-tier coupon discounts
- [ ] Customer order export (CSV/PDF)
