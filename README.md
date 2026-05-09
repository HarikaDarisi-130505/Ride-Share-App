# Realtime Ride-Sharing Mobile Application

A full-stack mobile ride-sharing platform built using **Expo React Native**, **FastAPI**, and **MySQL**. The application supports smart ride discovery, realtime communication, live location tracking, and secure authentication workflows for both passengers and drivers.

---

# Features

## Authentication & Security

* JWT-based authentication
* Access token + refresh token flow
* OTP-based email verification
* Optional two-factor authentication (2FA)
* Password hashing using bcrypt

---

## Ride Management

* Publish rides with pickup, destination, stops, pricing, and seat availability
* Smart ride search with route-aware matching
* Instant booking and request-confirmation workflows
* Ride lifecycle management:

  * Scheduled
  * Ongoing
  * Completed
  * Cancelled

---

## Smart Route Matching

* Polyline-based route matching
* Coordinate proximity checks for pickup/drop points
* Segment-aware pricing support
* Google Directions + OSRM route integration

---

## Realtime Features

* WebSocket-based realtime chat
* Live driver/passenger location tracking
* Ride-specific realtime communication rooms

---

## Maps & Location

* Google Maps integration
* OpenStreetMap Nominatim geocoding
* Reverse geocoding support
* Route visualization with polylines

---

# Tech Stack

## Frontend

* Expo React Native
* React Navigation
* Axios
* AsyncStorage
* react-native-maps
* expo-location

---

## Backend

* FastAPI
* SQLAlchemy ORM
* MySQL
* Alembic
* JWT Authentication
* WebSockets
* Pydantic

---

## Infrastructure & Deployment

* Railway (Backend + Database Hosting)
* Expo EAS (Android Builds)
* SMTP-based OTP system

---

# Project Architecture

```text id="gh1"
React Native Mobile App
        ↕
 FastAPI REST APIs + WebSockets
        ↕
      MySQL Database
```

---

# Core Modules

## Frontend

* Authentication Flow
* Passenger & Driver Modes
* Ride Search
* Ride Publishing
* Booking & Requests
* Chat & Tracking
* Profile & Settings

---

## Backend

* Auth APIs
* Ride APIs
* Booking Workflow
* Realtime WebSocket Manager
* Ratings System
* Location Services
* Route Matching Engine

---

# Authentication Flow

```text id="gh2"
Register/Login
→ OTP Verification
→ JWT Token Generation
→ Access + Refresh Token Storage
→ Protected API Access
```

---

# Realtime Communication

The application uses FastAPI WebSockets for:

* ride chat
* live tracking
* realtime ride updates

Each ride creates a dedicated communication room:

```text id="gh3"
/ws/ride/{ride_id}/{user_id}
```

---

# Deployment

## Backend

* Hosted on Railway
* MySQL configured using DATABASE_URL
* Supports HTTPS APIs and WebSocket endpoints

## Android App

* Built using Expo EAS
* Managed Expo workflow
* Google Maps API integration

---

# Future Improvements

* JWT-secured WebSocket authentication
* Spatial indexing using PostGIS
* Redis caching for ride search
* CI/CD automation
* Improved geospatial optimization

---

# Learning Outcomes

This project helped in understanding:

* full-stack mobile architecture
* realtime systems using WebSockets
* JWT authentication workflows
* geospatial route matching
* cloud deployment and mobile builds
* frontend-backend integration at scale

---

# Author

Harika Darisi
B.Tech – Computer Science and Business Systems
VIT-AP University
