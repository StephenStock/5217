# PostgreSQL Setup

## Purpose

This note records the PostgreSQL setup on the current machine so we can later point the Treasurer app at it from the Family Room PC on the same home network.

## Current host

- Windows PC
- PostgreSQL 18.3
- Service name: `postgresql-x64-18`
- LAN IP: `192.168.1.201`
- Port: `5432`

## Database and role

- Database: `treasurer`
- Role: `treasurer`
- Password used at setup time: `lodge`

## Connectivity

- `listen_addresses` is set to allow network connections
- `pg_hba.conf` includes a home LAN rule for `192.168.1.0/24`
- PostgreSQL accepts connections on the LAN IP with:

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 192.168.1.201 -U treasurer -d treasurer
```

## Remaining manual step

Windows Firewall still needs an inbound TCP rule for port `5432` if it has not already been added manually with admin rights:

```powershell
New-NetFirewallRule -DisplayName "PostgreSQL 5432 Inbound" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5432 -RemoteAddress 192.168.1.0/24 -Profile Private
```

## App connection string

When we are ready to switch Treasurer from SQLite to PostgreSQL, the app should connect with a URL shaped like this:

```text
postgresql://treasurer:lodge@192.168.1.201:5432/treasurer
```

## Notes

- Keep the database host private on the home network.
- Do not use OneDrive for the live database file.
- SQLite remains the current application backend until we explicitly transition.
