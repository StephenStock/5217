# Spec: V1 Foundation

## Status

In progress

## Problem

The project needs a clean technical foundation for a lodge treasurer web app that can grow into a maintainable operational tool.

## Scope

This spec covers:

- Flask application setup
- SQLite database setup
- Starter schema
- Seed data
- Basic dashboard page
- Local launch flow
- Project documentation for incremental development

This spec does not cover:

- Authentication
- Data entry forms
- Editing workflows
- Online payments
- Email sending

## Users

- Treasurer
- Secretary
- Member

## Current implementation notes

- App uses Flask with an application factory
- SQLite database file is `instance/Lodge.db`
- Seed data includes users, members, dues, events, bookings, and messages
- UI is server-rendered with vanilla JavaScript for light interactivity

## Acceptance criteria

- The repo contains a working Flask app structure
- The database schema can be initialized locally
- The seeded database is enough to render a meaningful dashboard
- The project can be launched with `start.bat`
- The project has a docs structure for future feature specs

## Deferred items

- Login and permissions
- CRUD forms
- CSV import/export
- Audit logging
- Payment processing
