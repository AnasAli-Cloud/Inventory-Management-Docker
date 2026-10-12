# 📦 StockPulse — Dockerized Inventory & Sales Management System

> A full-stack inventory management web application demonstrating real-world **Docker multi-container architecture** with Python Flask and MySQL.

---

## 🧱 Architecture Overview

```
     Browser (http://localhost:5000)
              │
              │ HTTP
              ▼
     ┌──────────────────┐
     │  Flask App       │   Container 1
     │  (Gunicorn)      │   stockpulse_app
     │  Port: 5000      │
     └────────┬─────────┘
              │ Docker Network: inventory_network
              ▼
     ┌──────────────────┐
     │  MySQL 8.0       │   Container 2
     │  stockpulse_db   │   Port: 3306 (internal)
     └────────┬─────────┘
              │
              ▼
        Named Volume
         mysql_data
     (persists across restarts)
```

**Key Docker concept:** The Flask app connects to MySQL using `DB_HOST=db` — the service name, **not** `localhost`. Docker Compose creates a shared network where containers resolve each other by service name.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📦 **Product Management** | Add, edit, delete products with SKU codes, categories, pricing, and low-stock thresholds |
| 🔄 **Stock Movements** | Stock-In and Stock-Out operations with a full audit trail |
| 🛒 **Sales Orders** | Create sales with automatic inventory deduction and conflict protection |
| 📊 **Dashboard** | Live KPI cards, Chart.js revenue trend, category distribution charts |
| ⚠️ **Low Stock Alerts** | Automatic banner and badges when items drop below threshold |
| 🔍 **Search & Filter** | Search products by name/SKU, filter by category |
| 🐳 **Docker Architecture** | Multi-container app with healthchecks, named volumes, and Docker networking |

---

## 🗄️ Database Schema

```sql
categories      → id, name, description
products        → id, name, sku, category_id (FK), price, quantity, min_threshold
sales           → id, product_id (FK), quantity, unit_price, total_price, customer_name, sale_date
inventory_logs  → id, product_id (FK), change_type (IN/OUT), quantity, reason, created_at
```

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine installed
- Ports `5000` and `3307` available on your machine

### 1. Clone / Download the project
```bash
git clone <your-repo-url>
cd inventory-management
```

### 2. Start the system (single command!)
```bash
docker compose up --build
```

Compose will:
1. 🔨 Build the Flask app image from `Dockerfile`
2. 🐬 Pull `mysql:8.0` from Docker Hub
3. 🌐 Create the `inventory_network` bridge network
4. 💾 Create the `mysql_data` named volume
5. 🚀 Start both containers with healthchecks

### 3. Open the application
```
http://localhost:5000
```

### 4. Stop the system
```bash
# Stop without deleting data
docker compose down

# Stop AND delete all data (volume)
docker compose down -v
```

---

## 🐳 Docker Commands Cheatsheet

```bash
# Start in background (detached mode)
docker compose up -d --build

# View live logs
docker compose logs -f

# View logs for one service only
docker compose logs -f app
docker compose logs -f db

# Restart a single service
docker compose restart app

# List running containers
docker ps

# Open a shell inside the Flask container
docker exec -it stockpulse_app bash

# Open a MySQL shell inside the DB container
docker exec -it stockpulse_db mysql -u inventory_user -pinventory_secret inventory_db

# Inspect the Docker network
docker network inspect inventory-management_inventory_network

# Inspect the named volume
docker volume inspect inventory-management_mysql_data

# Rebuild only the app image (after code changes)
docker compose build app
docker compose up -d app
```

---

## 📁 Project Structure

```
inventory-management/
│
├── app/                         # Flask application
│   ├── app.py                   # Main entry point + dashboard routes
│   ├── database.py              # DB connection with retry logic
│   ├── requirements.txt         # Python dependencies
│   │
│   ├── routes/
│   │   ├── products.py          # CRUD for products & categories
│   │   ├── inventory.py         # Stock IN/OUT adjustments
│   │   └── sales.py             # Sale creation & listing
│   │
│   ├── templates/               # Jinja2 HTML templates
│   │   ├── base.html            # Shared layout + navigation
│   │   ├── index.html           # Dashboard
│   │   ├── products.html        # Products catalog
│   │   ├── inventory.html       # Stock movements
│   │   └── sales.html           # Sales history
│   │
│   └── static/
│       └── css/style.css        # Custom styles
│
├── database/
│   └── init.sql                 # DB schema + seed data (auto-runs on first boot)
│
├── Dockerfile                   # Flask container image definition
├── docker-compose.yml           # Multi-container orchestration
├── .env                         # Environment variables (secrets)
├── .dockerignore                # Files excluded from Docker build
└── README.md                    # This file
```

---

## 🔐 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | MySQL hostname (set to `db` in Compose) | `db` |
| `DB_PORT` | MySQL port | `3306` |
| `DB_NAME` | Database name | `inventory_db` |
| `DB_USER` | Application database user | `inventory_user` |
| `DB_PASSWORD` | Application database password | `inventory_secret` |
| `DB_ROOT_PASSWORD` | MySQL root password | — |
| `SECRET_KEY` | Flask session secret | — |

> ⚠️ Change all passwords in `.env` before deploying to any shared or public environment.

---

## 🧠 Docker Concepts Demonstrated

| Concept | Where it's used |
|---|---|
| **Image Building** | `Dockerfile` — FROM, RUN, COPY, CMD |
| **Layer Caching** | `requirements.txt` copied before app code |
| **Container Networking** | `inventory_network` bridge, `DB_HOST=db` |
| **Named Volumes** | `mysql_data` persists database across restarts |
| **Healthchecks** | MySQL checked before Flask starts |
| **Environment Variables** | `.env` file + `env_file:` in Compose |
| **Port Mapping** | `5000:5000` host → container |
| **depends_on** | App waits for healthy DB |
| **Multi-service Compose** | Two services in one `docker-compose.yml` |

---

## 🛠️ Tech Stack

- **Backend:** Python 3.12, Flask 3.x, Gunicorn
- **Database:** MySQL 8.0, PyMySQL
- **Frontend:** Bootstrap 5.3, Bootstrap Icons, Chart.js 4
- **Containerization:** Docker, Docker Compose
- **Fonts:** Plus Jakarta Sans, JetBrains Mono (Google Fonts)

---

*Built as a portfolio project to demonstrate Docker multi-container architecture for LinkedIn showcase.*
