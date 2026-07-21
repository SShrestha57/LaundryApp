# LaundryApp

CSC336 Group Project

# Team Members

1. Alhassana Diallo
2. Benny
3. Sufyaan
4. Pedro
5. Yeasin Riyad
6. Sangita Shrestha
7. Jancarlos Jaquez


# Project Description

A SaaS platform that allows apartment tenants to reserve and pay for laundry machines while providing building managers with real-time machine availability and revenue tracking.

# Repository Structure

1. backend/ → Backend application code
2. frontend/ → User interface code
3. database/ → Database schema, SQL scripts, and ER diagrams
4. docs/ → Project documentation and reports

# WashWise Laundry Reservation System

WashWise is a full-stack laundry reservation application for apartment buildings.

Tenants can log in, view available washers and dryers, reserve a machine, view their bookings, and cancel reservations.

Building managers can log in to a manager dashboard to monitor machines, view live revenue information, and see the building subscription plan.

## Team Project

Course: CSC336 – Introduction to Database Systems

Project type: Full-stack relational database application

## Technology Stack

### Frontend

- SvelteKit
- HTML
- CSS
- JavaScript

### Backend

- Python
- Flask
- mysql-connector-python

### Database

- MySQL
- Stored procedures
- Triggers
- Views
- Indexes

## Main Features

- Database-based login for tenants and managers
- Role-based tenant and manager dashboards
- Live washer and dryer availability
- Machine duration and price information
- Tenant machine reservations
- Tenant booking history
- Booking cancellation
- Stored procedure for booking creation
- Booking overlap prevention
- Trigger-based machine status updates
- Manager machine inventory
- Live booking-fee revenue from MySQL
- Live subscription revenue from MySQL
- Live building subscription plan information
- Transaction-fee revenue model
- Building SaaS subscription model

## Revenue Model

WashWise uses two revenue streams:

1. A transaction fee from every laundry booking
2. A recurring SaaS subscription paid by each apartment building

Example for a $3.00 laundry cycle:

- Building share: $2.85
- Application developer fee: $0.15
- Transaction fee rate: 5%

The database stores the revenue split in the `booking_payments` table.

Building subscriptions are stored using:

- `subscription_plans`
- `building_subscriptions`
- `subscription_payments`

## Database Tables

The final database contains these main tables:

1. `buildings`
2. `users`
3. `machines`
4. `bookings`
5. `booking_payments`
6. `subscription_plans`
7. `building_subscriptions`
8. `subscription_payments`

The data model is normalized to at least Second Normal Form.

## Demo Login Accounts

### Manager Account

Email:

```text
maya.manager@example.com
```

Password:

```text
password123
```

### Tenant Account

Email:

```text
pedro.tenant@example.com
```

Password:

```text
password123
```

## Repository Structure

```text
LaundryApp/
├── backend/
│   ├── app.py
│   ├── db.py
│   ├── schema.sql
│   ├── procedures.sql
│   ├── indexes_views.sql
│   ├── seed.py
│   ├── test_api.py
│   ├── test_db.py
│   ├── requirements.txt
│   └── .env.example
├── database/
├── docs/
├── frontend/
│   ├── src/
│   │   └── routes/
│   │       └── +page.svelte
│   ├── package.json
│   └── vite.config.js
├── compose.yaml
├── Midpitch.pdf
└── README.md
```

## Local Setup

GitHub contains the source code, but the application must be run locally unless the frontend, backend, and database are deployed online.

The application requires:

- MySQL
- Python 3
- Node.js
- npm

## Step 1: Create the MySQL Database

Open MySQL Workbench.

The database name is:

```sql
laundry_app
```

Run the SQL files in this order:

```text
1. backend/schema.sql
2. backend/procedures.sql
3. backend/indexes_views.sql
```

After running the SQL files, load the sample data using `seed.py`.

## Step 2: Configure the Backend

Open a terminal in the project folder:

```bash
cd ~/Desktop/LaundryApp/backend
```

Create and activate the Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the Python requirements:

```bash
pip install -r requirements.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Update `backend/.env` with the local MySQL credentials.

Example:

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=laundry_app
```

Do not upload the `.env` file to GitHub.

## Step 3: Load the Demo Data

From the backend folder, run:

```bash
python3 seed.py
```

This creates the demo users, machines, bookings, payments, and subscription information.

## Step 4: Start the Flask Backend

From the backend folder, run:

```bash
source venv/bin/activate
python3 app.py
```

The backend should run at:

```text
http://127.0.0.1:5001
```

Keep the backend terminal open.

## Step 5: Start the SvelteKit Frontend

Open another terminal:

```bash
cd ~/Desktop/LaundryApp/frontend
```

Install the frontend packages:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Open the local address shown by Vite, such as:

```text
http://localhost:5173
```

The port number may be different if another port is already being used.

## Application Flow

### Tenant Flow

1. Tenant logs in
2. Tenant views available washers and dryers
3. Tenant selects a machine
4. Tenant chooses a date and time
5. The booking is created through the Flask backend
6. The booking is stored in MySQL
7. The machine becomes unavailable
8. The tenant can view the booking
9. The tenant can cancel the booking
10. The machine becomes available again

### Manager Flow

1. Manager logs in
2. Manager opens the Manager Dashboard
3. Manager views machine totals and machine status
4. Manager views live transaction-fee revenue
5. Manager views live subscription revenue
6. Manager views the building subscription plan

## API Examples

Important backend routes include:

```text
POST /login
GET /machines
POST /bookings
GET /users/<user_id>/bookings
DELETE /bookings/<booking_id>
GET /subscriptions
GET /reports/revenue
```

## Database Logic

The project uses:

- Parameterized SQL queries
- Foreign keys
- Stored procedures
- Triggers
- Indexes
- Views
- Booking conflict prevention
- Role-based frontend behavior
- Revenue calculations
- Subscription tracking

The `sp_book_machine` stored procedure creates bookings.

Database triggers validate bookings and update machine status when bookings are created, cancelled, or completed.

## Testing Completed

The following application flow was tested successfully:

- Tenant login
- Manager login
- Role-based navigation
- Machine availability
- Machine reservation
- Booking creation
- Booking history
- Booking cancellation
- Machine availability after cancellation
- Manager machine dashboard
- Live revenue report
- Live subscription information
- Frontend-to-backend connection
- Backend-to-MySQL connection

## Important Security Note

The `.env` files are excluded from GitHub because they contain local database credentials.

Each person running the application must create their own local `.env` file.

## Current Deployment Status

The application currently runs locally.

GitHub stores the project source code and documentation, but GitHub does not automatically run:

- The MySQL database
- The Flask backend
- The SvelteKit frontend

For a classroom demonstration, start MySQL, the Flask backend, and the frontend locally.