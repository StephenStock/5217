# Spec: V1 Authentication

## Status

Planned

## Problem

The app needs basic login and role-aware protection before real treasurer data should be managed through the web interface.

## Scope

- Login page
- Logout flow
- Session-based authentication
- Route protection for admin pages
- Treasurer and secretary role checks

## Acceptance criteria

- Unauthenticated users cannot access admin pages
- A seeded treasurer account can sign in
- Protected pages show the current signed-in user
- Logout clears the session cleanly

## Deferred items

- Password reset
- Member self-service login
- Multi-factor authentication
