# Mini Bank Management System API 🏦

A production-ready **Mini Bank Management System REST API** built with **Django** and **Django REST Framework (DRF)**. The system provides secure customer authentication, bank account management, atomic deposits and withdrawals, peer-to-peer transfers, transactional audit history with PDF/CSV statements, and administrative controls.

---

## 🌟 Key Features

### 1. Customer Authentication & Profiles
- **JWT-Based Authentication**: Secure token issuance (`access` and `refresh` tokens) powered by `djangorestframework-simplejwt`.
- **Customer Registration & Login**: Validated registration with password matching, hashing, and email uniqueness.
- **Profile Management**: Endpoints to view (`GET`) and update (`PATCH`) customer personal profile details.
- **Object-Level Security**: Customers can only view and manipulate their own data; cross-customer access is forbidden.

### 2. Bank Account Management
- **Account Creation**: Customers can create accounts (`Savings` or `Current`) with an optional opening deposit.
- **Auto-Generated Unique Account Numbers**: Guaranteed unique 10-digit account numbers.
- **Real-Time Balance Enquiry**: Instant, reliable balance check endpoint.
- **Strict Non-Negative Balance Enforcement**: Guaranteed both at the database level (`CheckConstraint`) and application logic.

### 3. Deposits & Withdrawals
- **Deposit Operations**: Instant deposits with strict positive amount validation (`amount > 0.00`).
- **Withdrawal Operations**: Balance verification preventing overdrafts.
- **Atomic Operations**: Employs `django.db.transaction.atomic()` and row-level locking (`select_for_update()`) to prevent race conditions.
- **Transaction Logging**: Automatically records every deposit and withdrawal.

### 4. Money Transfers
- **Account-to-Account Transfers**: Move funds between accounts atomically.
- **Consistency & Atomicity**: Sender account balance decreases and receiver account balance increases within an atomic block; rolls back completely on any failure.
- **Deadlock-Free Locking**: Locks both accounts ordered by database ID to eliminate concurrency deadlocks.
- **Validation**:
  - Rejects zero or negative amounts.
  - Rejects transfers where sender account equals receiver account.
  - Rejects transfers if sender has insufficient funds.
  - Verifies account active status and sender ownership.
- **Linked Reference**: Generates a single unique transaction reference (`TXN-YYYYMMDD-XXXXXXXX`) shared across both counterparties.

### 5. Transaction History & Filtering
- **Paginated Ledger**: Paginated output showing all transactions associated with the customer's accounts.
- **Rich Audit Details**: Includes transaction type, amount, before/after balance, counterparty account, timestamp, and reference code.
- **Filtering Options**:
  - Filter by `transaction_type` (`DEPOSIT`, `WITHDRAWAL`, `TRANSFER`).
  - Filter by `start_date` and `end_date` (YYYY-MM-DD).
  - Filter by `account_id` or `account_number`.

### 6. Admin Management
- **Administrative Endpoints**:
  - `GET /api/admin/customers/` — View all registered bank customers.
  - `GET /api/admin/accounts/` — View all bank accounts across all customers.
  - `GET /api/admin/transactions/` — View and inspect all transaction audit logs.
- **Django Admin Interface**: Rich admin interface at `/admin/` with search, filters, and read-only financial balance guards.

### 7. Bonus Challenges (All Implemented! 🚀)
- ✅ **Date Range Filtering**: Filter transaction history by `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`.
- ✅ **Daily Withdrawal Limits**: Configurable per-account limit (`daily_withdrawal_limit`, default $50,000) that prevents withdrawals exceeding the threshold within a rolling 24-hour period.
- ✅ **Comprehensive Automated Unit Tests**: 23 automated test cases covering registration, accounts, deposits, withdrawals, transfers, daily limits, and security boundaries.
- ✅ **Downloadable Account Statements**: Export complete account statements in both **PDF** (via ReportLab with professional bank styling) and **CSV** formats (`/api/accounts/<id>/statement/?format=pdf|csv`).

---

## 🛠️ Technology Stack

- **Framework**: Django 6.1.x, Django REST Framework 3.18.x
- **Authentication**: SimpleJWT (`djangorestframework-simplejwt`)
- **Filtering**: `django-filter`
- **PDF Generation**: `reportlab` & `pillow`
- **Database**: SQLite (default, easily switchable to PostgreSQL/MySQL)
- **Language**: Python 3.13+

---

## 📂 Project Structure

```
Mini Bank Management System API/
│
├── config/                     # Django project configuration
│   ├── __init__.py
│   ├── settings.py             # DRF, JWT, and database settings
│   ├── urls.py                 # Root URL routing & API discovery root
│   ├── wsgi.py
│   └── asgi.py
│
├── users/                      # Customer & authentication app
│   ├── models.py               # Custom User model extending AbstractUser
│   ├── serializers.py          # Register, Login, Profile serializers
│   ├── views.py                # Auth and profile views
│   ├── permissions.py          # Custom DRF permission classes
│   ├── urls.py
│   ├── admin.py
│   └── tests.py                # Auth test cases
│
├── accounts/                   # Bank accounts app
│   ├── models.py               # BankAccount model with non-negative constraints
│   ├── serializers.py          # BankAccount and Balance serializers
│   ├── views.py                # Account CRUD, balance check & statement export
│   ├── utils.py                # PDF and CSV statement export generators
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py                # Account management & statement tests
│   └── management/
│       └── commands/
│           └── setup_demo_data.py # Demo database seeder
│
├── transactions/               # Financial transactions app
│   ├── models.py               # Transaction model with double-entry reference
│   ├── serializers.py          # Deposit, Withdraw, Transfer serializers
│   ├── views.py                # Atomic financial transaction views
│   ├── filters.py              # FilterSet for type and date range
│   ├── urls.py
│   ├── admin.py
│   └── tests.py                # Deposit, withdrawal, transfer, limit unit tests
│
├── Mini_Bank_API_Postman_Collection.json # Ready-to-import Postman collection
├── requirements.txt
├── manage.py
├── .gitignore
└── README.md
```

---

## 🚀 Quickstart & Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd "Mini Bank Management System API"
```

### 2. Create and Activate Virtual Environment
```bash
# On Windows:
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Apply Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed Demo Data (Optional but Recommended)
Populates demo users, bank accounts, and initial transaction records:
```bash
python manage.py setup_demo_data
```

**Pre-seeded Demo Credentials:**
| Role | Username | Password | Notes |
|---|---|---|---|
| **Admin** | `admin` | `admin123` | Full administrative privileges |
| **Customer 1** | `john_doe` | `password123` | Has Savings & Current accounts with funds |
| **Customer 2** | `jane_smith` | `password123` | Has Savings account |

### 6. Run the Development Server
```bash
python manage.py runserver
```
The API root will be accessible at: `http://127.0.0.1:8000/`  
The Django Admin panel will be at: `http://127.0.0.1:8000/admin/`

---

## 🧪 Running Automated Tests

Run the full automated test suite (23 comprehensive tests):
```bash
python manage.py test
```

Sample output:
```text
Creating test database for alias 'default'...
.......................
----------------------------------------------------------------------
Ran 23 tests in 4.5s

OK
Destroying test database for alias 'default'...
```

---

## 📋 API Endpoints Reference

All endpoints (except `api-root` and `/admin/`) are prefixed with `/api/`.

### 1. Authentication & Profile
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register a new customer | No |
| `POST` | `/api/auth/login/` | Customer login; returns JWT tokens | No |
| `GET` | `/api/profile/` | View current customer's profile | Yes (Bearer) |
| `PATCH`| `/api/profile/` | Update profile information | Yes (Bearer) |

### 2. Bank Accounts
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/accounts/` | List current customer's bank accounts | Yes (Bearer) |
| `POST` | `/api/accounts/` | Create a new bank account (`SAVINGS`/`CURRENT`) | Yes (Bearer) |
| `GET` | `/api/accounts/<id>/` | View account details | Yes (Owner/Admin) |
| `GET` | `/api/accounts/<id>/balance/` | Check real-time account balance | Yes (Owner/Admin) |
| `GET` | `/api/accounts/<id>/statement/?format=pdf\|csv` | Download account statement (PDF or CSV) | Yes (Owner/Admin) |

### 3. Transactions
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/transactions/deposit/` | Deposit money into an account | Yes (Owner/Admin) |
| `POST` | `/api/transactions/withdraw/` | Withdraw money (with daily limit check) | Yes (Owner/Admin) |
| `POST` | `/api/transactions/transfer/` | Transfer money to another account | Yes (Owner/Admin) |
| `GET` | `/api/transactions/` | View paginated transaction history | Yes (Bearer) |

**Transaction History Query Filters:**
- `?transaction_type=DEPOSIT|WITHDRAWAL|TRANSFER`
- `?account_id=<id>`
- `?start_date=YYYY-MM-DD`
- `?end_date=YYYY-MM-DD`
- `?min_amount=100.00`
- `?max_amount=5000.00`
- `?page=1`

### 4. Admin Management (Staff Only)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/admin/customers/` | List all registered customers | Yes (Admin) |
| `GET` | `/api/admin/accounts/` | List all bank accounts | Yes (Admin) |
| `GET` | `/api/admin/transactions/` | List all transactions across the system | Yes (Admin) |

---

## 📬 Sample API Payloads

### 1. Register Customer
**`POST /api/auth/register/`**
```json
{
    "username": "sarah_connor",
    "email": "sarah@example.com",
    "password": "Password123!",
    "password_confirm": "Password123!",
    "first_name": "Sarah",
    "last_name": "Connor",
    "phone_number": "+15554321000",
    "address": "Los Angeles, CA"
}
```

### 2. Login Customer
**`POST /api/auth/login/`**
```json
{
    "username": "john_doe",
    "password": "password123"
}
```
**Response (200 OK):**
```json
{
    "message": "Login successful.",
    "user": {
        "id": 2,
        "username": "john_doe",
        "email": "john.doe@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "tokens": {
        "refresh": "eyJhbGciOi...",
        "access": "eyJhbGciOi..."
    }
}
```

### 3. Create Bank Account
**`POST /api/accounts/`**
```json
{
    "account_type": "SAVINGS",
    "initial_deposit": "1000.00"
}
```

### 4. Deposit Money
**`POST /api/transactions/deposit/`**
```json
{
    "account": 1,
    "amount": "250.00",
    "description": "Freelance payout"
}
```

### 5. Withdraw Money
**`POST /api/transactions/withdraw/`**
```json
{
    "account": 1,
    "amount": "100.00",
    "description": "ATM cash withdrawal"
}
```

### 6. Transfer Money
**`POST /api/transactions/transfer/`**
```json
{
    "from_account": 1,
    "to_account": 3,
    "amount": "150.00",
    "description": "Shared project expense"
}
```

---

## 📦 Postman Testing

A comprehensive Postman Collection is included in the project root:
👉 **`Mini_Bank_API_Postman_Collection.json`**

### How to use:
1. Open **Postman** and click **Import**.
2. Select `Mini_Bank_API_Postman_Collection.json`.
3. In the collection, run the **Login Customer** request.
   - The test script **automatically saves the returned JWT `access_token`** into collection variables!
4. All subsequent authenticated requests (Accounts, Deposits, Withdrawals, Transfers, Statements) will automatically use the active token.

---

## 🔒 Security & Business Rules Implemented

1. **Overdraft Prevention**: Account balances are guarded at both the database level (`bank_account_balance_non_negative`) and the application serializer level.
2. **Concurrency Safety**: Account balances are modified within atomic database transactions with row-level locks (`select_for_update()`).
3. **Data Isolation**: Customers cannot view or operate on accounts they do not own.
4. **Audit Trail**: Every balance mutation produces an immutable `Transaction` record storing `balance_after` and a unique reference code.
5. **Daily Limits**: Prevents fraudulent or unauthorized massive withdrawals in a rolling 24-hour period.
