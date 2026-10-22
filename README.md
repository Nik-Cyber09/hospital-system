# Carepoint Hospital Management

Carepoint is a modern clinic and hospital operations system built with a **Python (FastAPI)** backend, **React 19 + Vite** frontend, and **MongoDB** storage with secure authenticated staff and administrator access.

## Architecture

- **Backend (`/server`)**: Python 3.13 / FastAPI, Motor (Async MongoDB), Pydantic v2, Python-Jose (JWT), BCrypt.
- **Frontend (`/client`)**: React 19, Vite, responsive clinic operations dashboard.
- **Database**: MongoDB (Local service or MongoDB Atlas).

---

## Prerequisites

1. **Python 3.13+**
2. **Node.js 20+** and npm
3. **MongoDB** running locally or a MongoDB Atlas URI

---

## Configuration

In `server/.env`:

```dotenv
NODE_ENV=development
PORT=4000
MONGODB_URI=mongodb://localhost:27017/carepoint
JWT_SECRET=your-random-32-character-secret-key
CLIENT_ORIGIN=http://127.0.0.1:5173,http://localhost:5173

# Admin bootstrap credentials
ADMIN_NAME=Clinic Administrator
ADMIN_EMAIL=admin@hospital.local
ADMIN_PASSWORD=AdminPassword123456
```

---

## Quick Start

### 1. Backend (Python FastAPI)

From the project root:

```powershell
# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements (already installed in .venv)
pip install -r server\requirements.txt

# Create the first administrator
python server\scripts\create_admin.py

# Run the FastAPI server (runs on port 4000)
python -m uvicorn app.main:app --app-dir server --host 0.0.0.0 --port 4000 --reload
```

### 2. Frontend (React / Vite)

In a separate terminal:

```powershell
cd client
npm install
npm run dev
```

Open `http://localhost:5173` or `http://127.0.0.1:5173` in your browser. Vite automatically proxies `/api` calls to the Python FastAPI backend on `http://127.0.0.1:4000`.

---

## Default Administrator Credentials

- **Email**: `admin@hospital.local`
- **Password**: `AdminPassword123456`
             
*(You can change the password anytime via the Account Security menu in the dashboard or create additional staff members under the Staff tab).*

---

## System Capabilities

- **Authentication & Security**: HTTP-only secure JWT cookies, BCrypt password hashing (12 rounds), token version invalidation on password change, login rate-limiting, and CSRF origin verification.
- **Patient Management**: Full demographic records, clinical condition status, assigned physician linking.
- **Doctor & Specialist Registry**: Specialties, duty availability, on-duty/off-duty statuses.
- **Appointment Scheduling**: Real-time patient-doctor booking with confirmation, waiting, and completion state toggling.
- **Invoicing & Billing**: Patient charge records with instant pending/paid status toggling.
- **Relational Integrity**: Enforced prevention of orphaned records (cannot delete doctors or patients while active consultations, appointments, or invoices reference them).
- **Staff Administration**: Administrator-controlled user account provisioning for hospital staff.

---

## Running Verification Tests

To verify the entire backend API suite:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir server --port 4000
# Run the end-to-end integration test
.\.venv\Scripts\python.exe C:\Users\asus\.gemini\antigravity\brain\43ec9f37-4957-4224-a5ce-8eb0fe2dc33a\scratch\test_backend.py
```
