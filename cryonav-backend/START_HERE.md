# 🚢 START HERE - CryoNav AI Backend

## Welcome! 👋

You're about to run the **CryoNav AI** backend - an Antarctic ship navigation system for your hackathon demo.

## ⚡ Super Quick Start (30 seconds)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Run
uvicorn app.main:app --reload

# 3. Test
# Open http://localhost:8000/docs in your browser
```

**That's it!** Your API is running. 🎉

---

## 📖 What You Just Built

A **FastAPI backend** with:
- ✅ 9 REST API endpoints
- ✅ 4 demo scenarios (safe → warning → emergency)
- ✅ 20 pre-made JSON data files
- ✅ Automatic documentation
- ✅ CORS enabled for frontends
- ✅ Docker support

---

## 🎯 Quick Demo

### 1. Open Interactive Docs
http://localhost:8000/docs

### 2. Try These Endpoints
- Click **GET /api/health** → Try it out → Execute
- Click **GET /api/risk-assessment** → Execute (shows GREEN)
- Click **POST /api/advance-time** → Execute (advances scenario)
- Click **GET /api/risk-assessment** → Execute (still GREEN)
- Click **POST /api/advance-time** → Execute (advance again)
- Click **GET /api/risk-assessment** → Execute (now ORANGE!)
- Click **POST /api/advance-time** → Execute (advance once more)
- Click **GET /api/risk-assessment** → Execute (now RED - EMERGENCY!)

---

## 📚 Full Documentation

| File | What's Inside |
|------|---------------|
| **QUICKSTART.md** | 2-minute setup guide |
| **README.md** | Full project documentation |
| **API_REFERENCE.md** | Complete API endpoint reference |
| **PROJECT_SUMMARY.md** | Technical overview |
| **TESTING_CHECKLIST.md** | 40-point testing checklist |

**Start with:** `QUICKSTART.md`

---

## 🎬 The 4 Scenarios

Your demo cycles through these:

| # | Alert | Description |
|---|-------|-------------|
| 0 | 🟢 GREEN | Safe - no icebergs |
| 1 | 🟡 YELLOW | Iceberg detected 45km away |
| 2 | 🟠 ORANGE | Warning - hazard approaching |
| 3 | 🔴 RED | EMERGENCY - collision imminent |

Use `/api/advance-time` to progress through scenarios.

---

## 🔧 Alternative Start Methods

### Using Scripts

**Windows:**
```bash
start_server.bat
```

**Mac/Linux:**
```bash
chmod +x start_server.sh
./start_server.sh
```

### Using Docker
```bash
docker-compose up --build
```

### Using Python directly
```bash
python app/main.py
```

---

## 🧪 Testing

### Automated Tests
```bash
python test_api.py
```
Runs 13 tests covering all endpoints.

### Manual Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Get risk level
curl http://localhost:8000/api/risk-assessment

# Advance scenario
curl -X POST http://localhost:8000/api/advance-time
```

---

## 🎨 Frontend Integration

Point your frontend to:
```javascript
const API_URL = 'http://localhost:8000';

// Example: Get risk assessment
fetch(`${API_URL}/api/risk-assessment`)
  .then(res => res.json())
  .then(data => {
    console.log(data.level); // "GREEN", "ORANGE", or "RED"
  });
```

CORS is already enabled - no configuration needed!

---

## 📡 Key Endpoints

### Data (GET)
- `/api/health` - Server status
- `/api/ice-analysis` - Ice zones
- `/api/icebergs` - Detected icebergs
- `/api/routes` - Route options
- `/api/risk-assessment` - Alert level
- `/api/explanation` - Situation description
- `/api/predict-drift` - Drift predictions

### Control (POST)
- `/api/advance-time` - Next scenario
- `/api/reset-demo` - Back to start

---

## 🎪 Demo Tips

1. **Start clean:** `POST /api/reset-demo`
2. **Show safe state:** Scenario 0 has no icebergs
3. **Progress slowly:** Explain each scenario as you advance
4. **Highlight drama:** Scenario 3 says "14 minutes to impact"
5. **Show trade-offs:** Routes have different speeds/safety/fuel
6. **Use explanations:** `/api/explanation` has narrative text
7. **Visual impact:** Risk level goes GREEN → ORANGE → RED

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 busy | `uvicorn app.main:app --reload --port 8001` |
| Module errors | `pip install -r requirements.txt` |
| Can't connect | Check server is running |
| CORS errors | Already fixed - check browser console |

---

## 📂 Project Structure

```
cryonav-backend/
├── app/
│   ├── main.py          # All API endpoints
│   ├── config.py        # Settings
│   └── models.py        # Data schemas
│
├── data/scenarios/      # 4 scenarios × 5 files = 20 files
│
├── Documentation/       # 5 markdown files
├── Scripts/            # Test & start scripts
└── Configuration/      # requirements, Docker, env
```

---

## ✨ What Makes This Special

- **Zero configuration** - works immediately
- **Self-documenting** - automatic API docs at /docs
- **Demo-ready** - 4 scenarios simulate time progression
- **Frontend-friendly** - CORS enabled, clean JSON
- **Fully tested** - includes automated test suite
- **Docker-ready** - optional containerization
- **Well documented** - 5 comprehensive guides

---

## 🚀 Next Steps

### For Backend Work
1. Read `API_REFERENCE.md` for endpoint details
2. Run `python test_api.py` to verify everything works
3. Check `TESTING_CHECKLIST.md` for full testing guide

### For Frontend Work
1. Start the server: `uvicorn app.main:app --reload`
2. Open the docs: http://localhost:8000/docs
3. Test endpoints in browser
4. Integrate with your frontend code

### For Demo Prep
1. Read `QUICKSTART.md` for 2-minute walkthrough
2. Practice advancing scenarios
3. Prepare talking points for each scenario
4. Have browser tabs ready

---

## 🎓 Learning Resources

### FastAPI
- **Docs:** http://localhost:8000/docs (your running server)
- **ReDoc:** http://localhost:8000/redoc (alternative docs)
- **OpenAPI:** http://localhost:8000/openapi.json (raw schema)

### Project Docs
- Start with: `QUICKSTART.md`
- Deep dive: `README.md`
- API details: `API_REFERENCE.md`
- Testing: `TESTING_CHECKLIST.md`

---

## 🏆 Success Criteria

You'll know it's working when:
- ✅ Server starts without errors
- ✅ http://localhost:8000/docs loads
- ✅ `/api/health` returns status
- ✅ `/api/risk-assessment` shows GREEN
- ✅ `/api/advance-time` changes scenario
- ✅ Risk level changes to ORANGE then RED
- ✅ All test pass: `python test_api.py`

---

## 💡 Pro Tips

- **Use Swagger UI** - Best way to explore API (http://localhost:8000/docs)
- **Check logs** - Server prints message for each request
- **Reset often** - `POST /api/reset-demo` to start fresh
- **Test early** - Run `python test_api.py` before demo
- **Have backup** - Know how to restart if server crashes

---

## 🆘 Need Help?

1. **Check docs:** Start with `QUICKSTART.md`
2. **Run tests:** `python test_api.py`
3. **Check logs:** Look at server terminal output
4. **Restart server:** CTRL+C then run again
5. **Verify data:** All 20 files in `data/scenarios/`

---

## 🎉 You're Ready!

The backend is **complete** and **ready to demo**.

**Start now:**
```bash
uvicorn app.main:app --reload
```

Then open: http://localhost:8000/docs

**Good luck with your hackathon! 🚢❄️**

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `pip install -r requirements.txt` | Install |
| `uvicorn app.main:app --reload` | Start server |
| `python test_api.py` | Run tests |
| `curl http://localhost:8000/api/health` | Test endpoint |

| URL | Purpose |
|-----|---------|
| http://localhost:8000 | API base |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/api/health | Health check |
| http://localhost:8000/api/risk-assessment | Get alert level |

---

**Happy Hacking! 🚀**
