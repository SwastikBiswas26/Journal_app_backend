# Journal Application - Modular Flask & MongoDB Atlas Backend

A modular, enterprise-ready Flask REST API backend integrated with MongoDB Atlas for a Journal Application.

---

## 🏗️ Modular Architecture (4 Clean Layers)

The codebase is divided into several single-responsibility units to maximize readability and maintainability:

1. **`utils/` (Helper Layer)**
   - [utils/jwt_helper.py](file:///d:/WebDev/backend/utils/jwt_helper.py): Dedicated JWT token creation, header extraction, and verification.
   - [utils/response.py](file:///d:/WebDev/backend/utils/response.py): Standardized API response format generator (`success_response` & `error_response`).
   - [utils/auth_middleware.py](file:///d:/WebDev/backend/utils/auth_middleware.py): `@token_required` Flask decorator.
   - [utils/serializers.py](file:///d:/WebDev/backend/utils/serializers.py): MongoDB BSON ObjectId to JSON converter.

2. **`validators/` (Validation Layer)**
   - [validators/auth_validator.py](file:///d:/WebDev/backend/validators/auth_validator.py): Email regex, username format, and password strength checks.
   - [validators/journal_validator.py](file:///d:/WebDev/backend/validators/journal_validator.py): Request payload and ObjectId format validation.

3. **`services/` (Business Logic Layer)**
   - [services/auth_service.py](file:///d:/WebDev/backend/services/auth_service.py): User signup, case-insensitive username/email resolution, and authentication.
   - [services/journal_service.py](file:///d:/WebDev/backend/services/journal_service.py): Public community feed, journal CRUD, and privacy toggle logic.

4. **`routes/` (Presentation/HTTP Controller Layer)**
   - [routes/auth.py](file:///d:/WebDev/backend/routes/auth.py): Clean controller endpoints for `/api/auth`.
   - [routes/journal.py](file:///d:/WebDev/backend/routes/journal.py): Clean controller endpoints for `/api/journals`.

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
py -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and set your MongoDB Atlas connection string (`MONGO_URI`):
```env
PORT=5000
SECRET_KEY=journal_secret_jwt_token_key_change_me_in_production_min_32_chars
MONGO_URI=mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority
DATABASE_NAME=journal_app_db
```

### 3. Run Server
```bash
py app.py
```
Server runs at `http://localhost:5000`.

### 4. Run Test Suite
```bash
py -m pytest tests/test_api.py
```

---

## 📡 Standard API Response Format (For React Developer)

All API responses follow a consistent JSON structure:

### Success Response Format:
```json
{
  "success": true,
  "message": "Operation description",
  "data": { ... }
}
```

### Error Response Format:
```json
{
  "success": false,
  "error": "Detailed error message"
}
```

---

## 📖 API Endpoints Quick Reference

| Method | Endpoint | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/signup` | No | Register new user |
| `POST` | `/api/auth/login` | No | Log in with email or username |
| `GET` | `/api/auth/me` | Yes | Get authenticated user profile |
| `GET` | `/api/journals/feed` | No | Browse public community feed |
| `POST` | `/api/journals` | Yes | Create post (`is_public: true` or `false`) |
| `GET` | `/api/journals/my` | Yes | Get user's own posts (`?status=public/private`) |
| `GET` | `/api/journals/<id>` | Optional | Get single post details (checks private authorization) |
| `PATCH` | `/api/journals/<id>/privacy` | Yes | Change privacy (`is_public: true` or `false`) |
| `PUT` | `/api/journals/<id>` | Yes | Update title, content, or tags |
| `DELETE` | `/api/journals/<id>` | Yes | Delete journal entry |
