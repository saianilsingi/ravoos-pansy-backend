# Ravoos Pansy – Backend API

> **High-performance E-commerce REST API built with Django 6.0 & Django REST Framework.**

![Project Status](https://img.shields.io/badge/status-active-success.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![Django](https://img.shields.io/badge/Django-6.0-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.16-red.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)

## 📖 Project Overview

### Live API
https://ravoos-pansy-backend.onrender.com

**Ravoos Pansy** is a robust, stateless backend designed to power modern e-commerce distributed applications. Built specifically for the Chingu Tier-3 evaluation, it serves as the data layer for a separate React frontend.

This API handles the heavy lifting of e-commerce logic, including complex cart operations, secure order processing, and coupon management, while maintaining a strict separation of concerns through a RESTful architecture.

**Key Features:**
-   **Security**: Token-based authentication (TokenAuthentication).
-   **Catalog**: Hierarchical product and category management.
-   **Commerce**: Feature-rich shopping cart (add/update/remove) and order history.
-   **Admin Ops**: Restricted staff endpoints for inventory management.
-   **Scalability**: Dockerized environment ready for cloud deployment (Render).

---

## 🛠 Tech Stack

-   **Language**: Python 3.13
-   **Framework**: Django 6.0
-   **API Toolkit**: Django REST Framework 3.16
-   **Database**: PostgreSQL (Production & Development)
-   **Authentication**: DRF Token Authentication
-   **Server**: Gunicorn (WSGI)
-   **Deployment**: Docker & Render
-   **Utilities**: `django-cors-headers`, `python-dotenv`, `Pillow`

---

## 🏗 System Architecture

The system follows a standard **API-First** architecture:

1.  **Frontend (Client)**: React (Vite) application consumes JSON data.
2.  **API Layer (Backend)**: Django REST Framework views expose endpoints.
3.  **Service Layer**: Business logic resides in model methods and serializers.
4.  **Data Layer**: PostgreSQL database stores relational data (Users, Orders, Products).

The backend is fully stateless; all user session state is handled via token authentication, enabling horizontal scalability without shared server memory.

This separation ensures the backend remains stateless and scalable.

---

## 🔐 Authentication & Security

This project uses **Token-based Authentication**.

-   **Signup/Login**: Public endpoints generate a permanent auth token.
-   **Protected Routes**: Clients must include the `Authorization` header in requests:
    ```http
    Authorization: Token <your_generated_token>
    ```
-   **Permissions**:
    -   `AllowAny`: Registration and Product browsing.
    -   `IsAuthenticated`: Cart and Order operations.
    -   `IsAdminUser`: Product creation/deletion (Staff only).
-   **CORS**: Configured to allow cross-origin requests from the deployed frontend.

---

## 🚀 Local Development Setup

Follow these steps to run the backend locally.

### Prerequisites
-   Python 3.10+
-   PostgreSQL (optional, defaults to SQLite if not configured)
-   Git

### 1. Clone the Repository
```bash
git clone https://github.com/saianilsingi/ravoos-pansy-backend.git
cd ravoos-pansy-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```bash
touch .env
```
Add the following configuration (example for local dev):
```ini
# Security
SECRET_KEY=unsafe-secret-key-for-dev-only
DEBUG=True

# Database (Leave empty to use default SQLite, or add Postgres URL)
# DATABASE_URL=postgres://user:password@localhost:5432/ravoos_db
```

### 5. Run Migrations
Apply database schema changes:
```bash
python manage.py migrate
```

### 6. Start Development Server
```bash
python manage.py runserver
```
 The API will be available at `http://127.0.0.1:8000/`.

---

## 🐳 Docker Setup (Optional)

You can run the application containerized to match production:

```bash
# Build the image
docker build -t ravoos-backend .

# Run the container
docker run -p 8000:8000 ravoos-backend
```

---

## 🌍 Deployment (Render)

The application is deployed on **Render**.

### Build Command
```bash
pip install -r requirements.txt
```

### Start Command
```bash
python manage.py migrate && gunicorn
ravoos_pansy.wsgi:application --bind 0.0.0.0:$PORT
```

### Production Environment Variables
Set these on the Render Dashboard:
-   `SECRET_KEY`: (High entropy random string)
-   `DEBUG`: `False`
-   `DATABASE_URL`: (Internal Render PostgreSQL URL)
-   `PYTHON_VERSION`: `3.13.0`

---

## 📚 API Documentation

For full details on request/response formats, please see the [API Documentation](api_documentation.md) or [Models Documentation](model_documentation.md).

### Quick Reference

| Method | Endpoint | Description | Auth |
| :--- | :--- | :--- | :--- |
| **Auth** | | | |
| `POST` | `/api/auth/signup/` | Register new user | Public |
| `POST` | `/api/auth/login/` | Obtain auth token | Public |
| **Products** | | | |
| `GET` | `/api/products/` | List all products | Public |
| `GET` | `/api/categories/` | List categories | Public |
| **Cart** | | | |
| `GET` | `/api/cart/` | View cart items | **User** |
| `POST` | `/api/cart/add/` | Add item to cart | **User** |
| **Orders** | | | |
| `POST` | `/api/orders/checkout/`| Place order | **User** |
| `GET` | `/api/orders/` | User order history | **User** |

---

## 🔮 Future Improvements

-   [ ] **Rate Limiting**: Implement specific throttling classes for auth routes.
-   [ ] **Payment Gateway**: Integrate Stripe/Razorpay for real transactions.
-   [ ] **Email Notifications**: Send Async confirmation emails via Celery.
-   [ ] **Swagger UI**: Add `drf-spectacular` for interactive docs.

---

*Project developed for Chingu Tier-3 Portfolio.*
