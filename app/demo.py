"""
Live demo script for client_onboard_capmarkets API.
Run: python3 demo.py
"""
import urllib.request
import json

BASE = "http://localhost:8002/api/v1"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer dev-token",
}


def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=body, headers=HEADERS, method="POST")
    return json.loads(urllib.request.urlopen(req).read())


def get(path):
    req = urllib.request.Request(f"{BASE}{path}", headers=HEADERS)
    return json.loads(urllib.request.urlopen(req).read())


# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("  ZenLabs — Wealth Management Client Onboarding  ")
print("  Capital Markets Platform — Live Demo           ")
print("="*60)

# 1. HEALTH CHECK
raw = urllib.request.urlopen("http://localhost:8002/health")
health = json.loads(raw.read())
print(f"\n[1] Health: {health}")

# 2. START SESSION — Individual HNW client
print("\n[2] Starting individual HNW onboarding session...")
resp = post("/onboard/start", {
    "journey_type": "individual",
    "message": "I'd like to open a High Net Worth investment account. My investable assets are around $3.5 million.",
    "form_data": {
        "full_name": "James Harrington",
        "dob": "1975-04-12",
        "nationality": "US",
        "investable_assets": "3500000",
        "risk_appetite": "moderate",
    }
})

SESSION_ID = resp["session_id"]
print(f"   session_id:    {SESSION_ID}")
print(f"   journey_type:  {resp.get('journey_type')}")
print(f"   current_step:  {resp.get('current_step')}")
print(f"   routing_lane:  {resp.get('routing_lane')}")
print(f"   client_type:   {resp.get('client_type')}")
print(f"   agent says:    {str(resp.get('response', ''))[:180]}")

# 3. RESUME — provide KYC data
print("\n[3] Resuming session with KYC details...")
resp2 = post("/onboard/resume", {
    "session_id": SESSION_ID,
    "message": "My passport is ready. I have US nationality, SSN ending 7890.",
    "form_data": {
        "id_type": "passport",
        "id_number": "US9988776",
        "address": "123 Park Ave, New York, NY 10001",
        "source_of_wealth": "investment_income",
        "employment_status": "self_employed",
    }
})
print(f"   current_step:  {resp2.get('current_step')}")
print(f"   routing_lane:  {resp2.get('routing_lane')}")
print(f"   agent says:    {str(resp2.get('response', ''))[:180]}")

# 4. GET FULL SESSION STATE
print("\n[4] Full session state...")
state = get(f"/onboard/session/{SESSION_ID}")
print(f"   completed_steps:       {state.get('completed_steps', [])}")
print(f"   human_review_required: {state.get('human_review_required')}")
print(f"   risk_band:             {(state.get('risk_score') or {}).get('risk_band', '—')}")
print(f"   audit_events:          {len(state.get('audit_trail') or [])}")

# 5. DASHBOARD STATS
print("\n[5] Dashboard stats...")
stats = get("/applications/stats")
r = stats.get("routing_breakdown", {})
print(f"   stp_rate:              {stats.get('stp_rate'):.1%}")
print(f"   avg_completion_days:   {stats.get('avg_completion_days')}")
print(f"   pending_review:        {stats.get('pending_review')}")
print(f"   routing_breakdown:     {r}")

# 6. COMPLIANCE QUEUE
print("\n[6] Compliance review queue...")
queue = get("/review/queue")
print(f"   items in queue: {queue.get('count', 0)}")
for item in queue.get("queue", []):
    print(f"   → {item.get('session_id', '')[:8]}… | {item.get('routing_lane')} | {item.get('review_reason', '')[:60]}")

print("\n" + "="*60)
print("  Swagger UI: http://localhost:8002/docs")
print("  ReDoc:      http://localhost:8002/redoc")
print("="*60 + "\n")
