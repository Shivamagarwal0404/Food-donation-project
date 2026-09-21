
# 🍲 FoodShare — Community Food Donation & Rescue Platform

A production-ready full-stack e-commerce platform for a local shoe and clothing store.
A full-stack, production-ready food rescue platform connecting surplus food donors (restaurants, caterers, supermarkets, households) with verified NGOs, shelters, community kitchens, and delivery volunteers.

Built with **Django + React**, containerised with **Docker**, and deployable to **AWS EC2**.
Built with **Django REST Framework + React + TypeScript + Tailwind CSS**, containerised with **Docker**, and orchestrated via **Nginx** and **PostgreSQL**.

---

## ✨ Features
## 🌟 Vision & Key Features

### Customer
- Browse shoes and clothes with category filtering
- Product search and sorting
- Product detail pages with image gallery, size/color selection
- Add to cart, manage cart, stock validation
- User registration, login, logout (JWT)
- Customer profile and address management
- Checkout with Cash on Delivery (Razorpay ready)
- Order history and status tracking
FoodShare addresses food insecurity and urban food waste by providing real-time tracking from donation posting to final delivery.

### Admin
- Product management (add/edit/delete/images)
- Category and size management
- Size-specific inventory tracking
- Customer management
- Order management and status updates
- Basic sales statistics dashboard
### 🏢 Food Donors (Restaurants, Caterers, Supermarkets, Individuals)
- **Post Food Donations:** Specify quantity, unit (meals, kg, packets, liters), food category, dietary type (Veg, Non-Veg, Vegan), preparation time, safe expiration window, and pickup address.
- **Manage Claims:** Review incoming claim requests from verified NGOs and approve distribution with a single click.
- **Status Visibility:** Track real-time progress as volunteers are assigned, food is picked up, and delivery is confirmed.
- **Donation History:** View past donations and metrics on meals provided to the community.

---
### 🤝 NGOs & Community Receivers (Shelters, Food Banks, Orphanages)
- **Browse Available Food:** Search and filter surplus food donations by proximity, category, dietary restrictions, and expiration times.
- **Request / Claim Food:** Submit claim requests with specified serving needs and intended distribution purpose.
- **Delivery Tracking:** View assigned volunteer and estimated arrival times.
- **Fulfillment Confirmation:** Acknowledge receipt of food to complete the donation lifecycle.

## 🛠️ Technology Stack
### 🚴 Delivery Volunteers
- **Available Pickup Board:** Browse unassigned pickups in the local area.
- **Accept Logistics Tasks:** Self-assign to transport accepted donations from donors to receiver facilities.
- **Real-Time Status Updates:** Transition status from `ASSIGNED` → `IN_TRANSIT` → `PICKED_UP` → `DELIVERED`.
- **Impact Tracker:** Track individual volunteer milestones and total successful deliveries completed.

| Layer       | Technology                                 |
|-------------|--------------------------------------------|
| Frontend    | React 18, Vite, TypeScript, Axios          |
| Backend     | Python 3.12, Django 5, Django REST Framework |
| Auth        | JWT (djangorestframework-simplejwt)        |
| Database    | PostgreSQL 15                              |
| Media       | AWS S3 (production), local filesystem (dev) |
| Web Server  | Nginx + Gunicorn                           |
| DevOps      | Docker, Docker Compose                     |
| IaC         | Terraform                                  |
| Cloud       | AWS EC2, S3                                |
### 📊 Platform Analytics & Admin
- **Impact Dashboard:** Track total meals saved, estimated kg of food rescued, active donors, partner NGOs, and volunteer deliveries.
- **Role Verification:** Review and verify NGO registrations and food safety licenses.
- **Audit Trails:** Ensure safe food handling time windows and prevent illegal status transitions.

---

## 🏗️ Architecture
## 🔄 Controlled Donation Lifecycle

```
                Internet
                   │
               Domain/IP
                   │
                 Nginx
                   │
            ┌──────┴──────┐
            │             │
         React           Django (Gunicorn)
          SPA               │
                       PostgreSQL
                            │
                          AWS S3
                      (product images)
[ DONOR ]
  Creates Donation
         │
         ▼
    AVAILABLE ───────────► EXPIRED / CANCELLED
         │
[ NGO / RECEIVER ]
  Submits Claim
         │
         ▼
    REQUESTED ───────────► CANCELLED / REJECTED
         │
[ DONOR ]
  Accepts Claim
         │
         ▼
    ACCEPTED
         │
[ VOLUNTEER ]
  Accepts Task
         │
         ▼
  PICKUP_ASSIGNED
         │
[ VOLUNTEER ]
  Collects Food from Donor
         │
         ▼
    PICKED_UP
         │
[ VOLUNTEER ]
  Hands over Food to NGO
         │
         ▼
    DELIVERED
         │
         ▼
    COMPLETED
```

**Development (Docker Compose):**
```
React Vite Dev Server :5173
          │
Django runserver :8000
          │
     PostgreSQL :5432
```
---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Vite, TypeScript, Tailwind CSS, Axios, Lucide/React Icons |
| **Backend** | Python 3.12, Django 5, Django REST Framework |
| **Authentication** | JWT (`djangorestframework-simplejwt`) with role-based access control |
| **Database** | PostgreSQL 15 |
| **Reverse Proxy** | Nginx (static/media routing + API reverse proxy) |
| **Containerisation** | Docker, Docker Compose |
| **IaC** | Terraform (AWS VPC, EC2, S3 for donation photos) |

---

## 📁 Project Structure
## 📁 Clean Domain Architecture

```
chachu-shop/
├── .env.example               # Environment variable template
FoodShare/
├── .env.example               # Environment template
├── .env                       # Local development environment
├── .gitignore
├── .dockerignore
├── docker-compose.yml         # Local development orchestration
├── README.md
│
├── backend/                   # Django application
├── backend/                   # Django REST Framework backend
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── gunicorn.conf.py
│   ├── config/                # Django project config
│   ├── config/                # Django project configuration
│   │   ├── settings/
│   │   │   ├── base.py        # Shared settings
│   │   │   ├── development.py
│   │   │   └── production.py
│   │   ├── urls.py
│   │   │   ├── development.py # Local settings
│   │   │   └── production.py  # Hardened production settings
│   │   ├── urls.py            # Root URL router (/api/v1/)
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/
│       ├── core/              # Shared base models & utils
│       ├── accounts/          # User, Profile, Address
│       ├── products/          # Category, Product, Variant, Image
│       ├── cart/              # Cart, CartItem
│       └── orders/            # Order, OrderItem, Payment
│       ├── core/              # TimeStampedModel, Health check
│       ├── users/             # User, DonorProfile, NGOProfile, VolunteerProfile, Address
│       ├── donations/         # FoodCategory, FoodDonation, DonationRequest
│       ├── pickups/           # Pickup, Volunteer assignment & tracking
│       └── analytics/         # Community impact calculations & statistics
│
├── frontend/                  # React application
├── frontend/                  # React 18 + Vite + TypeScript frontend
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── assets/
│       ├── components/
│       │   ├── common/        # Button, Input, Modal, etc.
│       │   ├── layout/        # Navbar, Footer, Sidebar
│       │   ├── products/      # ProductCard, ProductGrid, etc.
│       │   ├── cart/          # CartItem, CartSummary
│       │   ├── orders/        # OrderCard, OrderTimeline
│       │   └── admin/         # Admin-specific components
│       ├── pages/
│       │   ├── public/        # Home, Products, Shoes, Clothes, etc.
│       │   ├── customer/      # Profile, Orders, Cart, Checkout
│       │   └── admin/         # Dashboard, Products, Orders, etc.
│       ├── context/           # AuthContext, CartContext
│       ├── hooks/             # useAuth, useCart, useProducts, etc.
│       ├── services/          # Axios API client + per-resource services
│       ├── types/             # TypeScript interfaces
│       └── utils/             # Helpers, formatters, validators
│       ├── App.tsx            # Main FoodShare application dashboard
│       ├── types/index.ts     # Domain TypeScript interfaces
│       ├── services/index.ts  # Axios API clients
│       ├── index.css          # Tailwind CSS styles
│       └── main.tsx
│
├── nginx/
│   └── nginx.conf             # Nginx reverse proxy config
│   └── nginx.conf             # Reverse proxy configuration
│
└── infrastructure/
    └── terraform/
        ├── providers.tf       # AWS provider
        ├── main.tf            # VPC, EC2, S3, Security Groups
    └── terraform/             # AWS Cloud infrastructure definition
        ├── providers.tf
        ├── main.tf
        ├── variables.tf
        ├── outputs.tf
        └── terraform.tfvars.example
```

---

## 🚀 Local Setup (Without Docker)
## 🚀 Quick Start (Local Setup)

### Prerequisites
### 1. Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 15+
- Git
- PostgreSQL 15+ (or Docker)

### Backend
### 2. Backend Setup

```bash
cd backend

# Create virtual environment
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp ../.env.example ../.env
# Edit .env with your local PostgreSQL credentials

# Run migrations
python manage.py migrate

# Create superuser (admin)
# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Frontend
Backend API will be live at: `http://localhost:8000/api/v1/`

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
cp ../.env.example .env.local
# Edit .env.local — set VITE_API_BASE_URL=http://localhost:8000/api/v1

# Start Vite dev server
npm run dev
```

Frontend will be accessible at: `http://localhost:5173/`

---

## 🐳 Docker Setup (Recommended)
## 🐳 Docker Setup

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Edit .env with your values (minimum: DJANGO_SECRET_KEY, POSTGRES_PASSWORD)

# 3. Start everything
# Start all services (Database, Django backend, React frontend)
docker compose up --build

# Access points:
#   Frontend:  http://localhost:5173
#   API:       http://localhost:8000/api/v1
#   DB Admin:  http://localhost:5432 (psql)
```

### Useful Docker commands

```bash
# Run migrations
# Run migrations inside the container
docker compose exec backend python manage.py migrate

# Create admin superuser
docker compose exec backend python manage.py createsuperuser

# View logs
# View service logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop everything
docker compose down

# Destroy volumes (wipe database)
docker compose down -v
```

---

## 🔑 Environment Variables
## 📡 REST API Reference

Copy `.env.example` to `.env` and configure:
All endpoints are versioned under `/api/v1/`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | **Required** |
| `DJANGO_DEBUG` | Enable debug mode | `True` |
| `POSTGRES_DB` | PostgreSQL database name | `chachushop` |
| `POSTGRES_USER` | PostgreSQL username | `chachushop_user` |
| `POSTGRES_PASSWORD` | PostgreSQL password | **Required** |
| `POSTGRES_HOST` | PostgreSQL host | `db` (Docker) |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | JWT access token expiry | `60` |
| `USE_S3` | Use S3 for media storage | `False` |
| `AWS_ACCESS_KEY_ID` | AWS credentials (if USE_S3=True) | - |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials (if USE_S3=True) | - |
| `AWS_STORAGE_BUCKET_NAME` | S3 bucket name (if USE_S3=True) | - |
| `VITE_API_BASE_URL` | Frontend API URL | `http://localhost:8000/api/v1` |
| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health/` | Service health and DB diagnostic check | Public |
| `POST` | `/api/v1/auth/token/` | Obtain JWT access and refresh tokens | Public |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh expired access token | Public |
| `POST` | `/api/v1/users/register/` | Register as Donor, NGO, or Volunteer | Public |
| `GET` | `/api/v1/users/me/` | Current user profile and address details | Authenticated |
| `GET` | `/api/v1/users/me/addresses/` | List user pickup/delivery addresses | Authenticated |
| `GET` | `/api/v1/donations/categories/` | List all food categories | Public |
| `GET` | `/api/v1/donations/` | List active available food donations | Public |
| `POST` | `/api/v1/donations/` | Post a new food surplus donation | Donor only |
| `GET` | `/api/v1/donations/<id>/` | Detailed view of a food donation | Public |
| `POST` | `/api/v1/donations/requests/` | Submit an NGO claim request | NGO only |
| `POST` | `/api/v1/donations/requests/<id>/accept/` | Accept NGO claim request | Donor only |
| `GET` | `/api/v1/donations/my-donations/` | List donations posted by current donor | Donor only |
| `GET` | `/api/v1/donations/my-requests/` | List claims made by current NGO | NGO only |
| `GET` | `/api/v1/pickups/available/` | List pickups awaiting volunteer pickup | Volunteer |
| `GET` | `/api/v1/pickups/my-pickups/` | List tasks assigned to current volunteer | Volunteer |
| `POST` | `/api/v1/pickups/<id>/assign/` | Self-assign a pickup delivery task | Volunteer |
| `POST` | `/api/v1/pickups/<id>/status/` | Update status (IN_TRANSIT / PICKED_UP / DELIVERED) | Volunteer |
| `GET` | `/api/v1/analytics/impact/` | Community impact and rescue statistics | Public |

---

## 📡 API Endpoints

```
POST   /api/v1/auth/register/
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
POST   /api/v1/auth/token/refresh/

GET    /api/v1/users/me/
PUT    /api/v1/users/me/
GET    /api/v1/users/me/addresses/
POST   /api/v1/users/me/addresses/

GET    /api/v1/categories/
GET    /api/v1/categories/{slug}/

GET    /api/v1/products/
GET    /api/v1/products/{slug}/
GET    /api/v1/products/search/?q=...

GET    /api/v1/cart/
POST   /api/v1/cart/items/
PUT    /api/v1/cart/items/{id}/
DELETE /api/v1/cart/items/{id}/

POST   /api/v1/orders/
GET    /api/v1/orders/
GET    /api/v1/orders/{id}/

# Admin
GET    /api/v1/admin/products/
POST   /api/v1/admin/products/
PUT    /api/v1/admin/products/{id}/
DELETE /api/v1/admin/products/{id}/
GET    /api/v1/admin/orders/
PATCH  /api/v1/admin/orders/{id}/status/
GET    /api/v1/admin/customers/
GET    /api/v1/admin/dashboard/stats/
```

---

## ☁️ AWS Deployment (Phase 13)

> **Do not run terraform apply without reviewing the plan.**

```bash
cd infrastructure/terraform

# Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars

# Initialize Terraform
terraform init

# Review the plan (SAFE — no AWS resources created)
terraform plan

# Apply only after reviewing the plan
terraform apply
```

**Resources created:**
- VPC with public subnet
- Internet Gateway + Route Table
- Security Group (SSH/HTTP/HTTPS)
- EC2 t3.small (Ubuntu 22.04)
- Elastic IP
- S3 bucket (with encryption + versioning)

---

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Run with coverage
pytest --cov=apps --cov-report=html
```
# Run Django test suite
python manage.py test

---

## 📐 Database Models (Phase 3)

# Or run pytest
pytest
```
User ──────────── CustomerProfile
  │                      │
  │                   Address (multiple)
  │
  ├─── Cart ──── CartItem ─── ProductVariant
  │
  └─── Order ── OrderItem ── ProductVariant
                    │
                 Payment

Category (tree) ─── Product ─── ProductImage
                         │
                     ProductVariant (size + color + stock)
```

---

## 🔮 Future: Kubernetes/EKS (Phase 16)

The application is designed with containerisation in mind:
- All config via environment variables
- Stateless application servers
- External database (RDS-ready)
- External media storage (S3)
- Health check endpoints

Kubernetes resources to be created:
- `Deployment` (backend, frontend)
- `Service` (ClusterIP + LoadBalancer)
- `Ingress` (with cert-manager for HTTPS)
- `ConfigMap` (non-secret config)
- `Secret` (DB credentials, JWT key)
- `HorizontalPodAutoscaler`
- GitHub Actions CI/CD pipeline pushing to Amazon ECR

---

## 📋 Implementation Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Project structure & architecture | ✅ Complete |
| 2 | Django backend & PostgreSQL | ⏳ Next |
| 3 | Database models & migrations | ⬜ Pending |
| 4 | REST APIs & authentication | ⬜ Pending |
| 5 | React frontend | ⬜ Pending |
| 6 | Frontend ↔ Backend integration | ⬜ Pending |
| 7 | Products, categories, inventory | ⬜ Pending |
| 8 | Cart & checkout | ⬜ Pending |
| 9 | Orders & admin management | ⬜ Pending |
| 10 | Dockerize complete application | ⬜ Pending |
| 11 | Local testing | ⬜ Pending |
| 12 | Terraform AWS infrastructure | ⬜ Pending |
| 13 | Deploy to EC2 | ⬜ Pending |
| 14 | Domain & HTTPS | ⬜ Pending |
| 15 | GitHub Actions CI/CD | ⬜ Pending |
| 16 | Kubernetes/EKS preparation | ⬜ Pending |

---

## 🏪 About Chachu Shop

A real local shop selling shoes and clothes. This platform is designed for actual production use — not a college demo project.

---

*Built with ❤️ for Chachu Shop*
*FoodShare — Reducing Waste, Feeding Hope.*
