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

## WashWise Setup and Demo Accounts

### Database Setup

WashWise uses MySQL. The database name is:

```text
laundry_app
```

Open MySQL Workbench and run these SQL files in this order:

```text
1. database/schema.sql
2. database/procedures.sql
3. database/indexes_views.sql
```

Do not use `database/sample_data.sql` for the demo users because it contains placeholder password hashes.

After creating the database tables, use `backend/seed.py` to insert working sample data and demo accounts.

### Backend Environment Setup

Inside the `backend` folder, create a file named:

```text
.env
```

Add the following information:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=laundry_app
```

Replace:

```text
your_mysql_password
```

with the password for MySQL on your computer.

Do not upload the real `.env` file to GitHub because it contains private database credentials.

### Install and Start the Backend

Open a terminal and run:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 seed.py
python3 app.py
```

The backend should run at:

```text
http://127.0.0.1:5001
```

Keep the backend terminal open while using WashWise.

### Install and Start the Frontend

Open another terminal and run:

```bash
cd frontend
npm install
npm run dev
```

Open the local URL shown in the terminal. It will usually be:

```text
http://localhost:5173
```

If port `5173` is already in use, Vite may use another port, such as:

```text
http://localhost:5174
```

or:

```text
http://localhost:5175
```

Keep the frontend terminal open while using WashWise.

## Demo Login Accounts

All demo accounts use the same password:

```text
password123
```

### Tenant Accounts

```text
pedro.tenant@example.com
sofia.tenant@example.com
```

### Manager Accounts

```text
maya.manager@example.com
daniel.manager@example.com
```

## Login Instructions

1. Start MySQL.
2. Start the Flask backend.
3. Start the SvelteKit frontend.
4. Open the frontend URL in a browser.
5. Click **Log In**.
6. Enter one of the demo email addresses.
7. Enter the password `password123`.

## Main Features

WashWise allows users to:

- Log in using an account stored in the MySQL database
- View available washers and dryers
- View machine duration and price
- Reserve an available machine
- View current and previous bookings
- Cancel confirmed bookings
- Read and update data through the Flask backend

## Technology Stack

```text
Frontend: SvelteKit
Backend: Python Flask
Database: MySQL
Database connection: mysql-connector-python
```

## Important Note

GitHub stores the WashWise project source code, but GitHub does not automatically run the MySQL database, Flask backend, or SvelteKit frontend.

To use the application locally, the database, backend, and frontend must all be running.