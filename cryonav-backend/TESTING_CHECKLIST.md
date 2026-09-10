# ✅ CryoNav AI - Testing Checklist

Use this checklist to verify the backend is working correctly before your demo.

## Pre-Demo Setup

### ☐ 1. Installation Check
```bash
pip install -r requirements.txt
```
✅ Expected: No errors, all packages installed

### ☐ 2. Server Start
```bash
uvicorn app.main:app --reload
```
✅ Expected: Server running on http://0.0.0.0:8000

### ☐ 3. Browser Access
Open: http://localhost:8000/docs
✅ Expected: Swagger UI loads with 9 endpoints visible

---

## Automated Testing

### ☐ 4. Run Test Suite
```bash
python test_api.py
```
✅ Expected: All tests pass (13/13)

---

## Manual Endpoint Testing

### ☐ 5. Health Check
```bash
curl http://localhost:8000/api/health
```
✅ Expected:
```json
{
  "status": "CryoNav API Running",
  "timestamp": "2024-01-15T..."
}
```

### ☐ 6. Ice Analysis (Scenario 0)
```bash
curl http://localhost:8000/api/ice-analysis
```
✅ Expected: JSON with `ice_zones` array and `average_concentration: 35`

### ☐ 7. Icebergs (Scenario 0 - Should be empty)
```bash
curl http://localhost:8000/api/icebergs
```
✅ Expected:
```json
{
  "icebergs": []
}
```

### ☐ 8. Routes
```bash
curl http://localhost:8000/api/routes
```
✅ Expected: JSON with 3 routes (safest, fastest, fuel_efficient)

### ☐ 9. Risk Assessment (Scenario 0)
```bash
curl http://localhost:8000/api/risk-assessment
```
✅ Expected:
```json
{
  "level": "GREEN",
  "message": "Safe conditions",
  ...
}
```

### ☐ 10. Explanation (Scenario 0)
```bash
curl http://localhost:8000/api/explanation
```
✅ Expected: Text about "All clear conditions"

### ☐ 11. Drift Predictions (Scenario 0 - Should be empty)
```bash
curl http://localhost:8000/api/predict-drift
```
✅ Expected:
```json
{
  "predictions": []
}
```

---

## Scenario Progression Testing

### ☐ 12. Advance to Scenario 1
```bash
curl -X POST http://localhost:8000/api/advance-time
```
✅ Expected:
```json
{
  "scenario": 1,
  "message": "Advanced to scenario 1"
}
```

### ☐ 13. Check Icebergs (Scenario 1 - Should have 1)
```bash
curl http://localhost:8000/api/icebergs
```
✅ Expected: 1 iceberg with id "ICE-047"

### ☐ 14. Check Predictions (Scenario 1)
```bash
curl http://localhost:8000/api/predict-drift
```
✅ Expected: Trajectory data for ICE-047

### ☐ 15. Filter Predictions
```bash
curl "http://localhost:8000/api/predict-drift?iceberg_id=ICE-047"
```
✅ Expected: Only predictions for ICE-047

### ☐ 16. Advance to Scenario 2
```bash
curl -X POST http://localhost:8000/api/advance-time
```
✅ Expected: scenario: 2

### ☐ 17. Check Risk Level (Scenario 2)
```bash
curl http://localhost:8000/api/risk-assessment
```
✅ Expected: `"level": "ORANGE"`

### ☐ 18. Check Icebergs (Scenario 2 - Should have 2)
```bash
curl http://localhost:8000/api/icebergs
```
✅ Expected: 2 icebergs (ICE-047, ICE-048)

### ☐ 19. Advance to Scenario 3
```bash
curl -X POST http://localhost:8000/api/advance-time
```
✅ Expected: scenario: 3

### ☐ 20. Check Risk Level (Scenario 3)
```bash
curl http://localhost:8000/api/risk-assessment
```
✅ Expected: `"level": "RED"`, `"collision_risk_percent": 87`

### ☐ 21. Check Explanation (Scenario 3)
```bash
curl http://localhost:8000/api/explanation
```
✅ Expected: Text containing "CRITICAL" and "14 minutes"

### ☐ 22. Check Icebergs (Scenario 3 - Should have 3)
```bash
curl http://localhost:8000/api/icebergs
```
✅ Expected: 3 icebergs (ICE-047, ICE-048, ICE-049)

### ☐ 23. Advance (Should loop back to 0)
```bash
curl -X POST http://localhost:8000/api/advance-time
```
✅ Expected: scenario: 0

### ☐ 24. Verify Loop Back
```bash
curl http://localhost:8000/api/risk-assessment
```
✅ Expected: `"level": "GREEN"`

### ☐ 25. Reset Demo
```bash
curl -X POST http://localhost:8000/api/reset-demo
```
✅ Expected:
```json
{
  "message": "Demo reset to initial state"
}
```

### ☐ 26. Verify Reset
```bash
curl http://localhost:8000/api/risk-assessment
```
✅ Expected: scenario back to 0, level "GREEN"

---

## Data File Integrity

### ☐ 27. Check All Scenario Folders Exist
```bash
ls data/scenarios/
```
✅ Expected: scenario_0, scenario_1, scenario_2, scenario_3

### ☐ 28. Check Files in Each Scenario
```bash
ls data/scenarios/scenario_0/
```
✅ Expected: 5 files (explanation.txt, ice_data.json, icebergs.json, predictions.json, routes.json)

Repeat for scenarios 1, 2, 3.

---

## Performance Testing

### ☐ 29. Response Time Check
```bash
time curl http://localhost:8000/api/health
```
✅ Expected: Response in <100ms

### ☐ 30. Concurrent Requests
Open multiple terminal windows and run:
```bash
curl http://localhost:8000/api/ice-analysis
```
✅ Expected: All requests succeed

---

## Error Handling

### ☐ 31. Invalid Endpoint
```bash
curl http://localhost:8000/api/invalid-endpoint
```
✅ Expected: 404 error with proper JSON response

### ☐ 32. Invalid Method
```bash
curl -X POST http://localhost:8000/api/health
```
✅ Expected: 405 Method Not Allowed

---

## Browser Testing

### ☐ 33. Swagger UI
Visit: http://localhost:8000/docs
- ✅ All 9 endpoints visible
- ✅ Try out each endpoint
- ✅ Responses display correctly

### ☐ 34. ReDoc
Visit: http://localhost:8000/redoc
✅ Expected: Alternative documentation loads

### ☐ 35. Direct Browser Access
Visit: http://localhost:8000/api/health
✅ Expected: JSON displays in browser

---

## CORS Testing (If using frontend)

### ☐ 36. Frontend Request
From your frontend app:
```javascript
fetch('http://localhost:8000/api/health')
  .then(r => r.json())
  .then(console.log)
```
✅ Expected: No CORS errors in console

---

## Logging

### ☐ 37. Check Server Logs
Look at terminal where server is running
✅ Expected: Log messages for each request
Example: `INFO: GET /api/ice-analysis called (scenario=0)`

---

## Docker Testing (Optional)

### ☐ 38. Docker Build
```bash
docker-compose up --build
```
✅ Expected: Container builds and starts successfully

### ☐ 39. Docker Health Check
```bash
curl http://localhost:8000/api/health
```
✅ Expected: Same response as non-Docker

---

## Demo Dry Run

### ☐ 40. Full Demo Scenario
1. Start server
2. Show health endpoint
3. Show scenario 0 (safe)
4. Advance to scenario 1 (iceberg detected)
5. Show predictions
6. Advance to scenario 2 (warning)
7. Show explanation
8. Advance to scenario 3 (emergency)
9. Show risk level RED
10. Reset and loop

✅ Expected: Smooth progression through all scenarios

---

## Final Checklist

### Before Demo
- ☐ Server running and accessible
- ☐ All 9 endpoints tested and working
- ☐ All 4 scenarios tested
- ☐ Demo script prepared
- ☐ Browser tabs ready (docs, health check)
- ☐ Backup plan if server crashes (restart script ready)

### During Demo
- ☐ Start with clean state (reset to scenario 0)
- ☐ Have curl commands or Postman ready
- ☐ Know which endpoints to highlight
- ☐ Prepare for questions

### After Demo
- ☐ Reset demo to scenario 0
- ☐ Check server logs for errors
- ☐ Note any bugs or improvements

---

## Troubleshooting Quick Reference

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `uvicorn app.main:app --reload --port 8001` |
| Module not found | `pip install -r requirements.txt` |
| CORS errors | Check browser console, verify CORS settings |
| File not found | Check `data/scenarios/` directory exists |
| Server won't start | Check Python version (need 3.9+) |

---

## Quick Test Command

Run this one-liner to test all major endpoints:
```bash
curl http://localhost:8000/api/health && curl http://localhost:8000/api/ice-analysis && curl http://localhost:8000/api/icebergs && curl http://localhost:8000/api/routes && curl http://localhost:8000/api/risk-assessment && curl -X POST http://localhost:8000/api/advance-time && curl http://localhost:8000/api/risk-assessment && curl -X POST http://localhost:8000/api/reset-demo
```

✅ Expected: All return valid JSON responses

---

**All Checked? You're ready for the demo! 🚢❄️**
