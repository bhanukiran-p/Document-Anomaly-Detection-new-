# Redis Setup Guide

**Complete guide to enabling Redis caching in XFORIA DAD**

---

## ✅ Will Redis Work After Installation?

**YES!** Redis will **automatically work** after installation. The code is designed to:
1. ✅ **Auto-detect** Redis when available
2. ✅ **Auto-connect** using default settings
3. ✅ **Fallback gracefully** if Redis unavailable
4. ✅ **No code changes** required

---

## 🚀 Quick Setup (3 Steps)

### **Step 1: Install Redis**

**Mac:**
```bash
brew install redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install redis-server
```

**Linux (CentOS/RHEL):**
```bash
sudo yum install redis
```

**Docker (Any OS):**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

**Windows:**
- Download from: https://github.com/microsoftarchive/redis/releases
- Or use WSL/Docker

---

### **Step 2: Start Redis**

**Mac/Linux:**
```bash
# Start Redis server
redis-server

# Or run in background
redis-server --daemonize yes
```

**Docker:**
```bash
docker start redis
```

**Verify Redis is running:**
```bash
redis-cli ping
# Should return: PONG
```

---

### **Step 3: Configure (Optional)**

**Default settings work automatically:**
- Host: `localhost`
- Port: `6379`
- Database: `0`
- Password: None (optional)

**If using custom settings, add to `.env`:**
```bash
# Optional: Custom Redis configuration
REDIS_HOST=localhost      # Default: localhost
REDIS_PORT=6379          # Default: 6379
REDIS_DB=0               # Default: 0
REDIS_PASSWORD=          # Optional: leave empty if no password

# Cache settings
CACHE_ENABLED=true       # Default: true
CACHE_TTL=3600          # Default: 3600 seconds (1 hour)
```

**That's it!** Redis will automatically be used.

---

## 🔍 How Auto-Detection Works

### **Connection Flow:**

```
1. Application starts
   ↓
2. CacheManager.__init__() called
   ↓
3. Check if Redis library installed
   ├─ Not installed → Use in-memory cache
   └─ Installed → Try to connect
       ↓
4. Connect to Redis (localhost:6379)
   ├─ Success → Use Redis cache ✅
   └─ Failed → Use in-memory cache (with warning)
       ↓
5. Cache operations use active cache
```

### **Code Logic:**

```python
# Backend/utils/cache.py

if REDIS_AVAILABLE:  # Redis library installed?
    try:
        self.redis_client = redis.Redis(
            host=redis_host,      # From env or 'localhost'
            port=redis_port,      # From env or 6379
            db=redis_db,          # From env or 0
            password=redis_password
        )
        self.redis_client.ping()  # Test connection
        self.use_redis = True     # ✅ Redis active!
    except Exception as e:
        # Connection failed → fallback to in-memory
        self.use_redis = False
else:
    # Redis not installed → use in-memory
    self.use_redis = False
```

---

## ✅ Verification Steps

### **1. Check Redis Installation**

```bash
# Check if Redis is installed
redis-cli --version

# Should show version, e.g.:
# redis-cli 7.2.0
```

### **2. Check Redis Running**

```bash
# Test connection
redis-cli ping

# Should return:
# PONG
```

### **3. Check Python Redis Library**

```bash
cd Backend
python -c "import redis; print('Redis library:', redis.__version__)"
```

**If not installed:**
```bash
pip install redis==5.0.1
```

### **4. Test Cache Connection**

```bash
cd Backend
python -m utils.test_cache
```

**Expected Output (with Redis):**
```
✅ Redis cache is ACTIVE
   - Using distributed Redis cache
   - Cache is shared across instances
```

**Expected Output (without Redis):**
```
⚠️  Using IN-MEMORY cache fallback
   - Redis not available or connection failed
```

---

## 🔧 Configuration Options

### **Environment Variables (.env file):**

```bash
# Redis Connection (Optional - defaults work)
REDIS_HOST=localhost          # Redis server hostname
REDIS_PORT=6379              # Redis server port
REDIS_DB=0                   # Redis database number (0-15)
REDIS_PASSWORD=your_password  # Optional: Redis password

# Cache Settings
CACHE_ENABLED=true           # Enable/disable caching
CACHE_TTL=3600              # Default TTL in seconds
```

### **When to Customize:**

**Custom Host/Port:**
- Redis on different server: `REDIS_HOST=redis.example.com`
- Custom port: `REDIS_PORT=6380`

**Password Protection:**
- If Redis requires password: `REDIS_PASSWORD=your_secure_password`

**Multiple Databases:**
- Use different DB for different environments:
  - Development: `REDIS_DB=0`
  - Production: `REDIS_DB=1`

---

## 🎯 What Happens After Installation

### **Before Redis Installation:**
```
Application Start
  ↓
Check for Redis library
  ↓
Not found → Use in-memory cache
  ↓
Cache works (local only)
```

### **After Redis Installation:**
```
Application Start
  ↓
Check for Redis library
  ↓
Found! → Try to connect
  ↓
Connection successful → Use Redis cache ✅
  ↓
Cache works (distributed, persistent)
```

**No code changes needed!** The application automatically detects and uses Redis.

---

## 📊 Performance Comparison

### **In-Memory Cache (Current):**
- ✅ Fast (local memory)
- ⚠️ Lost on restart
- ⚠️ Not shared across instances
- ⚠️ Limited by RAM

### **Redis Cache (After Installation):**
- ✅ Fast (in-memory Redis)
- ✅ Persistent (survives restarts)
- ✅ Shared across instances
- ✅ Scalable (can use Redis cluster)
- ✅ Better for production

---

## 🐛 Troubleshooting

### **Issue: Redis not connecting**

**Check 1: Is Redis running?**
```bash
redis-cli ping
# Should return: PONG
```

**Check 2: Is Redis library installed?**
```bash
pip list | grep redis
# Should show: redis 5.0.1
```

**Check 3: Check logs**
```bash
# Look for these log messages:
# "Redis cache initialized: localhost:6379" ✅
# "Failed to connect to Redis: ..." ❌
```

**Check 4: Port conflict**
```bash
# Check if port 6379 is in use
lsof -i :6379
# Should show redis-server
```

### **Issue: Cache not working**

**Check 1: Is caching enabled?**
```bash
# In .env file
CACHE_ENABLED=true
```

**Check 2: Check cache status**
```bash
python -m utils.test_cache
```

**Check 3: Check Redis connection**
```bash
redis-cli
> GET test:cache:key
> (should return cached value or nil)
```

---

## 🔒 Security Considerations

### **Production Setup:**

1. **Use Password:**
   ```bash
   # In redis.conf
   requirepass your_secure_password
   
   # In .env
   REDIS_PASSWORD=your_secure_password
   ```

2. **Bind to Localhost Only:**
   ```bash
   # In redis.conf
   bind 127.0.0.1
   ```

3. **Use SSL/TLS (if remote):**
   ```python
   # In cache.py (if needed)
   redis.Redis(
       host=host,
       port=port,
       ssl=True,
       ssl_cert_reqs='required'
   )
   ```

---

## 📝 Summary

### **What You Need to Do:**

1. ✅ **Install Redis** (`brew install redis` or `apt-get install redis-server`)
2. ✅ **Start Redis** (`redis-server`)
3. ✅ **Verify** (`redis-cli ping` → should return `PONG`)
4. ✅ **Done!** Redis will automatically be used

### **What Happens Automatically:**

- ✅ Code detects Redis installation
- ✅ Code connects to Redis
- ✅ Cache switches from in-memory to Redis
- ✅ No code changes needed
- ✅ No restart needed (will use Redis on next request)

### **Optional Configuration:**

- Custom host/port (if Redis on different server)
- Password (if Redis requires authentication)
- Custom TTL (if you want different cache durations)

---

## ✅ Quick Checklist

- [ ] Redis installed (`redis-cli --version`)
- [ ] Redis running (`redis-cli ping` → `PONG`)
- [ ] Python redis library installed (`pip install redis`)
- [ ] Cache enabled in config (`CACHE_ENABLED=true`)
- [ ] Test cache (`python -m utils.test_cache`)
- [ ] Verify Redis usage (check logs for "Redis cache initialized")

---

**That's it!** Redis will work automatically after installation. 🚀

