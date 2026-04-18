# ─────────────────────────────────────────────────
#  HomeEase — Environment Variables
#  Copy this to  .env  and fill in your values.
#  Never commit .env to version control.
# ─────────────────────────────────────────────────

SECRET_KEY=your-very-secret-key-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# MySQL
DB_NAME=homeease_db
DB_USER=root
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=3306

# CORS — allow all origins in dev (set False in production)
CORS_ALLOW_ALL=True
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:5500
