# Free Deployment Options for Flashcard App

## Summary of Changes

✅ **Removed incorrect/correct popup messages**
✅ **Fixed statistics page error**  
✅ **Added user authentication (login/logout)**
✅ **Each user has their own decks and data**

## Free Hosting Options (for <10 users)

### Option 1: **Render.com** (RECOMMENDED)
**FREE TIER**: 750 hours/month, auto-sleep after 15 min inactivity

**Pros:**
- Easiest setup
- PostgreSQL database included (free 90-day limit, then $7/month)
- Auto HTTPS
- Good for < 10 users

**Steps:**
1. Create account at https://render.com
2. Connect your GitHub repository
3. Create new "Web Service"
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Add environment variable: `SECRET_KEY=your-random-secret-key-here`
5. Deploy!

**Database:** Use SQLite (default) or upgrade to PostgreSQL

---

### Option 2: **PythonAnywhere**
**FREE TIER**: 1 web app, always on, 512MB storage

**Pros:**
- Always running (no sleep)
- Easy Python setup
- Built-in database

**Steps:**
1. Create account at https://www.pythonanywhere.com
2. Upload your code or clone from Git
3. Create virtual environment
4. Configure WSGI file
5. Set working directory

**Limitations:**
- Slower than Render
- Only HTTP (no HTTPS on free tier)

---

### Option 3: **Fly.io**
**FREE TIER**: 3 shared VMs, 3GB storage

**Pros:**
- Very fast
- Always on
- Multiple regions
- HTTPS included

**Steps:**
1. Install Fly CLI: `brew install flyctl`
2. Login: `fly auth login`
3. Create app: `fly launch`
4. Deploy: `fly deploy`

**Requirements:**
- Add `Procfile`: `web: gunicorn app:app`
- Add `runtime.txt`: `python-3.11`

---

### Option 4: **Railway.app**
**FREE TIER**: $5/month credit (enough for small app)

**Pros:**
- Very easy deployment
- PostgreSQL included
- Auto HTTPS
- GitHub integration

**Steps:**
1. Go to https://railway.app
2. Click "Start a New Project"
3. Connect GitHub repo
4. Railway auto-detects Flask
5. Add environment variables
6. Deploy!

---

### Option 5: **Heroku** (New Pricing)
**NO FREE TIER** - Starts at $5/month

Not recommended for free deployment anymore.

---

## Recommended Setup for Your Use Case

### For <10 Users: **Render.com**

1. **Add Gunicorn** to `requirements.txt`:
```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
python-dateutil==2.8.2
Werkzeug==3.0.1
gunicorn==21.2.0
```

2. **Update config.py** for production:
```python
import os

class Config:
    # Use environment variable or default
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-this'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.dirname(__file__), 'instance', 'flashcards.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # App settings
    CARDS_PER_SESSION = 20
```

3. **Create Procfile**:
```
web: gunicorn app:app
```

4. **Deploy to Render**:
   - Push to GitHub
   - Connect to Render
   - Set environment variable `SECRET_KEY` to a random string
   - Deploy!

---

## Database Considerations

### SQLite (Current - FREE)
- **Pros**: No setup, works everywhere, free
- **Cons**: Single file, can have issues with multiple concurrent writes
- **Good for**: <10 users, low traffic

### PostgreSQL (Paid - $7/month on Render)
- **Pros**: Better for multiple users, more robust
- **Cons**: Requires migration, costs money
- **Good for**: Production apps, >10 users

**To migrate to PostgreSQL**:
```bash
pip install psycopg2-binary
# Update DATABASE_URL environment variable
# Run: flask db upgrade (if using Flask-Migrate)
```

---

## Security Recommendations

1. **Change SECRET_KEY** in production:
```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

2. **Use HTTPS** (automatic on Render, Fly.io, Railway)

3. **Set strong passwords** for users

4. **Backup database** regularly:
```bash
# For SQLite
cp instance/flashcards.db backups/flashcards_$(date +%Y%m%d).db
```

---

## Cost Summary (Monthly)

| Platform | Free Tier | Database | Total |
|----------|-----------|----------|-------|
| **Render** | Free | SQLite=Free, PostgreSQL=$7 | $0-7 |
| **PythonAnywhere** | Free | SQLite included | $0 |
| **Fly.io** | Free | SQLite=Free | $0 |
| **Railway** | $5 credit | Included | ~$0 |

---

## First User Setup

After deployment:
1. Visit your app URL
2. Click "Register"
3. Create first user account
4. Login
5. Import your JSON decks

Each user will have their own separate data!

---

## Quick Deploy Command (Render)

```bash
# 1. Install gunicorn
pip install gunicorn==21.2.0

# 2. Add to requirements.txt
echo "gunicorn==21.2.0" >> requirements.txt

# 3. Create Procfile
echo "web: gunicorn app:app" > Procfile

# 4. Commit and push
git add .
git commit -m "Ready for deployment"
git push

# 5. Deploy on Render.com via web interface
```

---

## Monitoring Free Tier Limits

- **Render**: 750 hours/month (enough for 1 app running 24/7)
- **PythonAnywhere**: Always on, no hour limits
- **Fly.io**: 3 VMs, unlimited hours
- **Railway**: $5/month credit (~160 hours)

---

## Support

For questions, check:
- Render Docs: https://render.com/docs
- PythonAnywhere Help: https://help.pythonanywhere.com
- Fly.io Docs: https://fly.io/docs

