# Application Scope

This project is becoming a lodge and chapter operations web app rather than a simple treasurer tool.

## Primary Purpose

- Support day-to-day administration for Masonic bodies.
- Provide a shared platform for treasury, secretary, and meeting-planning work.
- Include a public-facing booking form for dining or meal reservations.

## Current Primary Users

- You, as treasurer of one lodge.
- You, as secretary of a Royal Arch chapter.
- Future successors in those offices.

## Roles

The application should support role-based access for:

- Treasurer
- Secretary
- Director of Ceremonies or meeting planner
- Admin or platform maintainer
- Members using only the public booking form

## Organizations

The app should support multiple separate organizations, such as:

- Your first lodge
- Your Royal Arch chapter
- Other lodges or chapters in the future

Each organization should keep its own members, meetings, bookings, records, and officers separate.

## Core Functional Areas

Each lodge or chapter needs the same main themes:

- Treasury
- Secretary
- Meeting planning
- Dining or event booking

## Public Booking Form

The app should provide a URL that shows only a booking form to members.

Requirements:

- Public access through a link
- Separate link per meeting or event
- Booking limit of about 50 users
- Server-side enforcement of the limit
- No access to internal admin pages from the booking link

## Handover Model

The app should be designed so officers can change over time without losing continuity.

That means:

- Successors can be given the same role and access
- Historical records stay in place
- The system can be maintained by you for as long as you are able
- The app can later be transferred to another person or lodge if needed

## Hosting Direction

The preferred direction is a low-cost self-hosted setup rather than a recurring paid cloud service.

The den PC can act as the initial always-on host, with the option to move the app later to:

- A successor’s laptop or PC
- A lodge-owned machine
- Another always-on server

## Product Direction

The app should be built as a shared platform with:

- One codebase
- Multiple organizations
- Role-based access
- Public booking links
- Clean handover and export options

