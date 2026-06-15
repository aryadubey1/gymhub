# GymHub

A production-ready Django web application for gym membership management. Mobile-first design with Bootstrap 5 and Font Awesome.

## Features

- **Dashboard**: Overview of active members, expiring memberships, overdue payments, and birthdays
- **Member Management**: Add, edit, and manage gym members with profile photos
- **Membership Tracking**: Track membership plans, expiry dates, and renewal status
- **Payment Recording**: Record payments with multiple payment methods (Cash, UPI, Card)
- **Messaging**: Send SMS and WhatsApp messages using templates
- **Bulk Messaging**: Send messages to groups (active members, expiring soon, overdue, all)

## Tech Stack

- Python 3.11+
- Django 5.x
- PostgreSQL (production) / SQLite (development)
- Gunicorn (WSGI server)
- Nginx (reverse proxy)
- Whitenoise (static file serving)
- Pillow (image handling)
- python-decouple (environment variables)
- Bootstrap 5 (styling)
- Font Awesome (icons)

## Project Structure

```
gymhub/
├── config/                    # Django project config
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── production.py    # Production settings
│   │   └── development.py   # Development settings
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── members/                   # Members app
│   ├── models.py            # Plan, Member, Membership, Payment models
│   ├── views.py             # Dashboard, member CRUD views
│   ├── forms.py             # Django forms
│   ├── admin.py             # Django admin configuration
│   └── urls.py              # URL patterns
├── messaging/                 # Messaging app
│   ├── models.py            # MessageTemplate model
│   ├── views.py             # Bulk messaging view
│   ├── admin.py             # Django admin configuration
│   └── urls.py              # URL patterns
├── templates/                 # HTML templates
│   ├── base.html            # Base template with bottom nav
│   ├── dashboard.html
│   ├── members/             # Member-related templates
│   └── messaging/           # Messaging templates
├── fixtures/                  # Initial data fixtures
│   └── initial_data.json
├── static/                    # Global static files
├── media/                     # Uploaded files (gitignored)
├── .env.example               # Environment variables example
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── gunicorn.conf.py           # Gunicorn configuration
├── deploy.sh                  # Deployment script
├── gymhub.service             # Systemd unit file
├── nginx.conf                 # Nginx configuration
└── manage.py                  # Django management script
```

## Installation

### Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Copy environment variables:
   ```bash
   cp .env.example .env
   ```

5. Set `DJANGO_SETTINGS_MODULE=config.settings.development` in `.env`

6. Run migrations:
   ```bash
   python manage.py migrate
   ```

7. Load initial data:
   ```bash
   python manage.py loaddata fixtures/initial_data.json
   ```

8. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

9. Run the development server:
   ```bash
   python manage.py runserver
   ```

### Production Deployment

1. Set up PostgreSQL database
2. Configure environment variables in `.env`:
   ```
   SECRET_KEY=your-secret-key-here
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   DB_NAME=gymhub
   DB_USER=gymhub_user
   DB_PASSWORD=your-db-password
   DB_HOST=localhost
   DB_PORT=5432
   DJANGO_SETTINGS_MODULE=config.settings.production
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

6. Load initial data:
   ```bash
   python manage.py loaddata fixtures/initial_data.json
   ```

7. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

8. Configure systemd service:
   ```bash
   sudo cp gymhub.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable gymhub
   sudo systemctl start gymhub
   ```

9. Configure Nginx:
   ```bash
   sudo cp nginx.conf /etc/nginx/sites-available/gymhub
   sudo ln -s /etc/nginx/sites-available/gymhub /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

## Usage

### Dashboard
- View overview of active members, expiring memberships, overdue payments, and birthdays

### Member Management
- **Add Member**: Click the floating "+" button on the member list page
- **View Member**: Click on a member card to see details, payment history, and quick actions
- **Edit Member**: Click the "Edit" button on the member detail page
- **Record Payment**: Click the "Pay" button on the member detail page
- **Renew Membership**: Click the "Renew" button on the member detail page

### Messaging
- **Individual Message**: On member detail page, select a template and send SMS/WhatsApp
- **Bulk Message**: Go to Message tab, select template and recipient group, then send

## SMS/WhatsApp Integration

- **SMS**: Uses the native `sms:` URI scheme - opens the phone's SMS app
- **WhatsApp**: Uses the `wa.me` deep link - opens WhatsApp with the message pre-filled
- No third-party SMS/WhatsApp API required

## Time Zone

The application uses `Asia/Kolkata` time zone for all date/time operations.

## Security Features

- CSRF protection enabled
- Secure cookie settings in production
- XSS protection
- Content type nosniff
- Frame options (DENY)
- SSL redirect in production (can be disabled if not using HTTPS)

## License

This project is proprietary software.
