# WorkSlot - Embeddable Booking Calendar SaaS

A production-ready subscription-based SaaS platform that enables service providers (plumbers, electricians, consultants, etc.) to embed booking calendars on their websites via API keys.

## Features

- **Provider Dashboard**: Manage bookings, availability, and API keys
- **Embeddable Widget**: Lightweight vanilla JS calendar that works on any website
- **Email Verification**: Secure booking flow with email confirmation
- **Subscription System**: Stripe-ready plan management (Free, Basic, Pro)
- **API Key Authentication**: Secure widget embedding with hashed keys
- **Rate Limiting**: Protection against abuse with Redis-backed limiting

## Tech Stack

- **Backend**: Python (FastAPI) with async PostgreSQL
- **Frontend**: React + Vite + TypeScript + Tailwind CSS
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Rate Limiting**: Redis
- **Auth**: JWT tokens with refresh capability
- **Email**: SMTP abstraction (pluggable for SendGrid, Resend, etc.)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local dashboard development)
- Python 3.11+ (for local backend development)

### Running with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services will be available at:
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:5173
- **Widget Demo**: http://localhost:3000

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Run migrations (after PostgreSQL is running)
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

#### Dashboard

```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev
```

#### Widget

The widget is plain JavaScript and doesn't require a build step for development. Simply serve the `widget/dist` folder with any static file server.

## Project Structure

```
workslot/
├── backend/
│   ├── app/
│   │   ├── api/           # Route handlers
│   │   ├── core/          # Config, security, dependencies
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── templates/     # Email templates
│   ├── alembic/           # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
├── dashboard/             # React + Vite
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   └── stores/       # State management
│   └── Dockerfile
├── widget/                # Vanilla JS embeddable
│   ├── src/
│   └── dist/
└── docker-compose.yml
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new account
- `POST /api/auth/login` - Login and get tokens
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user

### Public API (Widget)
- `GET /api/availability` - Get available time slots
- `POST /api/bookings` - Create a booking
- `GET /api/bookings/verify/{token}` - Verify booking email
- `GET /api/provider-info` - Get provider info

### Provider Dashboard
- `GET /api/provider/stats` - Dashboard statistics
- `GET /api/provider/subscription` - Subscription status
- `POST /api/provider/subscription/upgrade` - Upgrade plan

### Booking Management
- `GET /api/provider/bookings` - List all bookings
- `GET /api/provider/bookings/today` - Today's bookings
- `POST /api/provider/bookings/{id}/approve` - Approve booking
- `POST /api/provider/bookings/{id}/decline` - Decline booking
- `POST /api/provider/bookings/{id}/arrive` - Mark arrival
- `POST /api/provider/bookings/{id}/complete` - Complete booking

### Availability
- `GET /api/provider/availability` - Get weekly schedule
- `PUT /api/provider/availability/{day}` - Update day
- `POST /api/provider/availability/blocked` - Add blocked date

### API Keys
- `GET /api/provider/apikeys` - List API keys
- `POST /api/provider/apikeys` - Create API key
- `DELETE /api/provider/apikeys/{id}` - Revoke API key
- `POST /api/provider/apikeys/{id}/regenerate` - Regenerate key

## Widget Embed

Add this to any website to embed the booking calendar:

```html
<div id="workslot-calendar"></div>
<script src="https://your-domain.com/widget/workslot.js"></script>
<script>
  WorkSlot.init({
    apiKey: 'wsk_your_api_key_here',
    container: '#workslot-calendar',
    theme: 'light', // or 'dark'
    primaryColor: '#6366f1',
    onBookingSuccess: (booking) => {
      console.log('Booked:', booking);
    },
    onBookingError: (error) => {
      console.error('Error:', error);
    }
  });
</script>
```

## Environment Variables

See `backend/.env.example` for all available configuration options.

Key variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET_KEY` - Secret for JWT signing (generate secure key for production)
- `SMTP_*` - Email server configuration
- `STRIPE_*` - Stripe API keys (optional, for payment processing)

## Deployment

### Railway

This project is Railway-ready:

1. Create a new project in Railway
2. Add PostgreSQL and Redis services
3. Connect your GitHub repository
4. Set environment variables
5. Deploy!

### Docker

Build and push images:

```bash
# Backend
docker build -t workslot-backend ./backend
docker push your-registry/workslot-backend

# Dashboard
docker build -t workslot-dashboard ./dashboard
docker push your-registry/workslot-dashboard
```

## Security Features

- Password hashing with bcrypt
- JWT access/refresh tokens
- API key hashing (SHA-256)
- Rate limiting per API key/IP
- Input validation with Pydantic
- CORS configuration
- Security headers
- SQL injection prevention (ORM)
- Audit logging

## Subscription Plans

| Feature | Free | Basic ($19/mo) | Pro ($49/mo) |
|---------|------|----------------|--------------|
| Dashboard | ✓ | ✓ | ✓ |
| API Keys | 0 | 1 | 5 |
| Bookings/month | 0 | 100 | 1000 |
| Email notifications | - | ✓ | ✓ |
| Priority support | - | - | ✓ |

## License

MIT License - see LICENSE file for details.

