# wya-backend

This is the backend for the *wya?* app — a location-based anonymous posting app.

## Tech Stack
- FastAPI (Python)
- PostgreSQL
- Amazon Cognito (for authentication)
- Render (for deployment)

## Setup
1. Create a `.env` file using `.env.example` as a template
2. Run: `uvicorn app.main:app --reload`
3. Make sure PostgreSQL is running locally and matches the connection string

## Deployment
This backend is deployed on Render using a private `.env`.

## License
MIT
