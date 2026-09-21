# 🍲 FoodShare — Food Donation & Rescue Platform

FoodShare is a full-stack food donation and waste-reduction management system that connects surplus food donors with NGOs/community receivers and delivery volunteers.

The platform provides role-based access control, OTP-based verification, donation and request management, volunteer pickup/delivery tracking, and impact analytics.

## 🎯 Project Objective

FoodShare aims to reduce avoidable food waste and improve food redistribution coordination.

- **Donors** publish surplus food donations and manage requests.
- **NGOs / Receivers** browse available food and submit requests.
- **Volunteers** claim pickup tasks and track delivery progress.
- **Admins** oversee platform activity and analytics.

## 👥 User Roles

### Donor
- Register and verify an account
- Create and manage food donations
- Review NGO requests
- Accept or reject requests
- Cancel eligible donations
- Track donation status

### NGO / Receiver
- Register and verify an account
- Browse available donations
- Request food with required serving quantities
- View and cancel eligible requests
- Track accepted donations

### Volunteer
- Register and verify an account
- Browse available pickup tasks
- Claim a pickup
- Update pickup and delivery status
- Track completed deliveries

### Admin
- Monitor users and platform activity
- Access administrative functionality
- Review platform analytics

## ✨ Major Features

- Email-based registration
- Role-based access control
- OTP verification for registration
- OTP-protected login
- Password reset using OTP
- Food category management
- Donation creation and management
- NGO donation-request workflow
- Donor request approval/rejection
- Volunteer pickup assignment
- Controlled pickup/delivery state transitions
- Donation completion tracking
- Impact analytics
- Docker and Docker Compose configuration
- Terraform-based AWS infrastructure
- Nginx configuration

## 🔄 Donation Lifecycle

```text
AVAILABLE
   │ NGO submits request
   ▼
REQUESTED
   │ Donor accepts request
   ▼
ACCEPTED
   │ Volunteer claims pickup
   ▼
PICKUP_ASSIGNED
   │ Food collected
   ▼
PICKED_UP
   │ Food delivered
   ▼
DELIVERED
   ▼
COMPLETED
```

Depending on the current state and business rules, a donation may also become `CANCELLED` or `EXPIRED`.

## 🏗️ Application Architecture

```text
User / Browser
      │
      ▼
React + TypeScript
    Frontend
      │
      ▼
   REST API
      │
      ▼
Django REST Framework
    Backend
      │
      ▼
  PostgreSQL
```

Nginx, Gunicorn, Docker, and Docker Compose provide the production-oriented application runtime.

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, TypeScript, Tailwind CSS, Axios |
| Backend | Python, Django, Django REST Framework |
| Authentication | JWT + Email OTP |
| Database | PostgreSQL |
| Application Server | Gunicorn |
| Web Server / Reverse Proxy | Nginx |
| Containerization | Docker, Docker Compose |
| Infrastructure as Code | Terraform |
| Cloud Platform | AWS |
| Cloud Compute | Amazon EC2 |
| Networking | Amazon VPC, Subnets, Security Groups, Internet Gateway |
| Version Control | Git / GitHub |

## 📁 Project Structure

```text
Food-donation-project/
├── .dockerignore
├── .env.example
├── .env.prod.example
├── .gitignore
├── README.md
├── docker-compose.yml
├── docker-compose.prod.yml
├── backend/
│   ├── Dockerfile
│   ├── manage.py
│   ├── requirements.txt
│   ├── gunicorn.conf.py
│   ├── config/
│   └── apps/
│       ├── core/
│       ├── users/
│       ├── donations/
│       ├── pickups/
│       └── analytics/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
├── infrastructure/
│   ├── scripts/
│   └── terraform/
│       ├── providers.tf
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── terraform.tfvars.example
├── nginx/
│   └── nginx.conf
└── docs/
```

## 🔐 Authentication and Security

FoodShare includes:

- Email-based user accounts
- Public roles restricted to Donor, NGO/Receiver, and Volunteer
- Public administrator registration blocked
- Six-digit OTP verification
- OTP expiration and attempt limits
- Separate OTP purposes for registration, login, and password reset
- Password validation
- JWT-based API authentication
- Role-based endpoint permissions
- Case-insensitive email uniqueness
- Unique mobile-number validation
- Environment-variable-based secret configuration
- Separate development and production settings

> Never commit `.env`, database passwords, AWS credentials, private keys, Terraform state, or real `.tfvars` files.

## 🍱 Food Categories

Default categories include Rice & Grains, Bakery & Bread, Fruits & Vegetables, Dairy & Milk, Cooked Meals, Packaged & Canned Food, Pulses & Legumes, Snacks & Dry Food, Beverages, Baby Food, and Other.

When **Other** is selected, a custom food-item name is required.

## 📡 REST API

The backend API is versioned under:

```text
/api/v1/
```

Major API areas include:

```text
/api/v1/health/
/api/v1/users/
/api/v1/donations/
/api/v1/pickups/
/api/v1/analytics/
```

Authentication endpoints also support JWT, registration OTP, login OTP, and password recovery.

## 🚀 Local Development

### Prerequisites

- Python
- Node.js and npm
- PostgreSQL
- Git

### Clone

```bash
git clone https://github.com/Shivamagarwal0404/Food-donation-project.git
cd Food-donation-project
```

### Environment configuration

```bash
cp .env.example .env
```

Replace placeholder values with your local configuration. Never commit the generated `.env`.

### Backend

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_categories
python manage.py runserver
```

Development API:

```text
http://127.0.0.1:8000/api/v1/
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Development frontend:

```text
http://localhost:5173/
```

## 🐳 Docker

```bash
docker compose up --build
docker compose ps
docker compose down
```

## 🧪 Testing

Backend:

```bash
cd backend
python manage.py test
pytest
```

Frontend:

```bash
cd frontend
npx tsc --noEmit
npm run build
```

The project has been tested across authentication, donation/request workflows, pickup/delivery transitions, backend integration, and frontend production builds.

## ☁️ AWS & Terraform

Terraform configuration is stored under `infrastructure/terraform/`.

The infrastructure configuration covers:

- VPC
- Public subnets
- Internet Gateway
- Route table
- Security Groups
- EC2
- Elastic IP
- RDS-related networking

Typical workflow:

```bash
cd infrastructure/terraform
terraform init
terraform validate
terraform plan
```

Only after reviewing the plan:

```bash
terraform apply
```

> `terraform apply` can create billable AWS resources. Review the plan and AWS costs before applying.

Terraform state (`*.tfstate`) and real `.tfvars` files must remain outside version control.

## 🌐 Current AWS Deployment Status

The FoodShare **frontend production build has been successfully deployed to AWS EC2** and is served using Docker and Nginx.

Verified components include AWS VPC infrastructure, EC2, Elastic/public IP configuration, Security Groups, Docker, Nginx, the React/Vite production frontend, and public HTTP access.

### Current deployment limitation

The public AWS deployment is currently a **frontend demonstration deployment**.

The Django backend and production PostgreSQL/RDS database are not connected to the public deployment. The complete application workflow was developed and tested in the local environment.

The RDS production deployment was deferred because of an AWS account/free-plan resource limitation encountered during deployment. Therefore, the current public deployment should not be described as a fully operational three-tier production deployment.

## 📊 Core Workflow Rules

- Donation quantity must be greater than zero.
- Serving count must be valid.
- Expiration must be in the future.
- NGOs cannot request their own donations.
- Requested servings cannot exceed available servings.
- Duplicate active requests are prevented.
- Only eligible donation/request states can be modified.
- Volunteer pickup transitions follow the required sequence.
- Completed workflows cannot be modified through normal workflow actions.

## 🔮 Future Enhancements

- Production PostgreSQL deployment using Amazon RDS
- Full Django backend deployment on AWS
- HTTPS and custom domain
- Automated CI/CD
- Production email service for OTP delivery
- Donation image/object storage
- Geographic pickup matching
- Notifications
- Kubernetes/EKS deployment
- Monitoring and centralized logging

## 🎓 Academic Context

FoodShare was developed as a final-year Computer Science Engineering major project focused on **Cloud Computing and DevOps**.

It demonstrates full-stack web development, REST API design, role-based authentication and authorization, relational database integration, containerization, Infrastructure as Code, AWS networking and compute, frontend cloud deployment, and application testing.

## 📄 License

This repository is intended primarily for academic and portfolio use. Add an explicit open-source license before allowing unrestricted reuse or redistribution.

---

**FoodShare — Reducing Food Waste, Connecting Communities.**
