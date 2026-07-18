# LaundryApp Database

This folder contains the MySQL database implementation for LaundryApp.

## Files

- `schema.sql` creates the database tables and relationships.
- `sample_data.sql` inserts sample records for testing.
- `queries.sql` contains tested SQL queries used by the application.

## Requirements

Install and start Docker Desktop before running the database.

## Environment setup

From the root of the repository, create a local `.env` file from the example:

```powershell
Copy-Item .env.example .env