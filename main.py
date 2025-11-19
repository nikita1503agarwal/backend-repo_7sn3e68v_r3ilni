import os
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict

from database import (
    db,
    create_document,
    get_documents,
    get_document_by_id,
    update_document,
    push_to_array,
    find_one,
    upsert_one,
)

from schemas import (
    AppUser,
    SOSSetting,
    FamilyProfile,
    BloodRequest,
    HealthNotice,
    MedicineOrder,
    Hospital,
    Doctor,
    Booking,
    TokenFeed,
    MedicineReminder,
    BloodSugarLog,
    VaccinationItem,
    Appointment,
)

app = FastAPI(title="HamroSwasthya API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"name": "HamroSwasthya API", "status": "ok"}


# 1) Users
@app.post("/users", response_model=dict)
def create_user(user: AppUser):
    user_id = create_document("appuser", user)
    return {"id": user_id}


@app.get("/users", response_model=List[dict])
def list_users(city: Optional[str] = None, blood_group: Optional[str] = None):
    filt: Dict = {}
    if city:
        filt["location"] = city
    if blood_group:
        filt["blood_group"] = blood_group
    return get_documents("appuser", filt)


# 2) SOS settings
@app.post("/sos/settings", response_model=dict)
def save_sos(settings: SOSSetting):
    # upsert by user_id
    doc = upsert_one("sossetting", {"user_id": settings.user_id}, settings.model_dump())
    return {"id": doc.get("_id")}


class SOSTrigger(BaseModel):
    user_id: str
    emergency_type: str
    lat: Optional[float] = None
    lng: Optional[float] = None


@app.post("/sos/trigger", response_model=dict)
def trigger_sos(payload: SOSTrigger):
    # Store SOS event; in real life integrate SMS/calls/ambulance APIs
    data = payload.model_dump()
    data["status"] = "sent"
    _id = create_document("sos_event", data)
    return {"id": _id, "status": "sent"}


# 3) Family Profiles
@app.post("/family", response_model=dict)
def add_family(profile: FamilyProfile):
    _id = create_document("familyprofile", profile)
    return {"id": _id}


@app.get("/family", response_model=List[dict])
def list_family(user_id: str):
    return get_documents("familyprofile", {"user_id": user_id})


@app.post("/family/{profile_id}/vaccinations")
def add_vaccination(profile_id: str, item: VaccinationItem):
    ok = push_to_array("familyprofile", profile_id, "vaccinations", item.model_dump())
    if not ok:
        raise HTTPException(404, "Profile not found")
    return {"status": "added"}


@app.post("/family/{profile_id}/sugar-logs")
def add_sugar_log(profile_id: str, item: BloodSugarLog):
    ok = push_to_array("familyprofile", profile_id, "sugar_logs", item.model_dump())
    if not ok:
        raise HTTPException(404, "Profile not found")
    return {"status": "logged"}


@app.post("/family/{profile_id}/reminders")
def add_medicine_reminder(profile_id: str, item: MedicineReminder):
    ok = push_to_array("familyprofile", profile_id, "medicine_reminders", item.model_dump())
    if not ok:
        raise HTTPException(404, "Profile not found")
    return {"status": "scheduled"}


@app.post("/family/{profile_id}/appointments")
def add_appointment(profile_id: str, item: Appointment):
    ok = push_to_array("familyprofile", profile_id, "appointments", item.model_dump())
    if not ok:
        raise HTTPException(404, "Profile not found")
    return {"status": "booked"}


# 4) BloodLink Nepal
@app.post("/blood/requests", response_model=dict)
def create_blood_request(req: BloodRequest):
    _id = create_document("bloodrequest", req)
    # In a real system, notify nearby same-group users
    return {"id": _id}


@app.get("/blood/requests", response_model=List[dict])
def list_blood_requests(city: Optional[str] = None, blood_group: Optional[str] = None, status: Optional[str] = None):
    filt: Dict = {}
    if city:
        filt["location"] = city
    if blood_group:
        filt["blood_group"] = blood_group
    if status:
        filt["status"] = status
    return get_documents("bloodrequest", filt)


# Award karma points (simplified)
class KarmaAward(BaseModel):
    user_id: str
    points: int


@app.post("/blood/karma")
def award_karma(payload: KarmaAward):
    from bson import ObjectId
    try:
        obj_id = ObjectId(payload.user_id)
    except Exception:
        raise HTTPException(400, "Invalid user id")
    res = db["appuser"].update_one({"_id": obj_id}, {"$inc": {"karma_points": payload.points}})
    if res.matched_count == 0:
        raise HTTPException(404, "User not found")
    return {"status": "ok"}


# 5) Health Notices
@app.post("/notices", response_model=dict)
def create_notice(notice: HealthNotice):
    _id = create_document("healthnotice", notice)
    return {"id": _id}


@app.get("/notices", response_model=List[dict])
def list_notices(city: Optional[str] = None, region: Optional[str] = None):
    filt: Dict = {}
    if city:
        filt["city"] = city
    if region:
        filt["region"] = region
    return get_documents("healthnotice", filt)


# 6) Medicine Orders
@app.post("/orders", response_model=dict)
def place_order(order: MedicineOrder):
    _id = create_document("medicineorder", order)
    return {"id": _id, "status": "placed"}


@app.get("/orders", response_model=List[dict])
def list_orders(user_id: Optional[str] = None):
    filt = {"user_id": user_id} if user_id else {}
    return get_documents("medicineorder", filt)


# 7) Hospitals & Appointments
@app.post("/hospitals", response_model=dict)
def add_hospital(h: Hospital):
    _id = create_document("hospital", h)
    return {"id": _id}


@app.get("/hospitals", response_model=List[dict])
def list_hospitals(city: Optional[str] = None):
    filt = {"city": city} if city else {}
    return get_documents("hospital", filt)


@app.post("/doctors", response_model=dict)
def add_doctor(d: Doctor):
    _id = create_document("doctor", d)
    return {"id": _id}


@app.get("/doctors", response_model=List[dict])
def list_doctors(hospital_id: Optional[str] = None, department: Optional[str] = None):
    filt: Dict = {}
    if hospital_id:
        filt["hospital_id"] = hospital_id
    if department:
        filt["department"] = department
    return get_documents("doctor", filt)


@app.post("/bookings", response_model=dict)
def book_appointment(b: Booking):
    # assign a token sequentially per doctor+date
    from bson import ObjectId
    try:
        _ = ObjectId(b.doctor_id)
    except Exception:
        raise HTTPException(400, "Invalid doctor id")

    date_key = b.date.strftime('%Y-%m-%d')
    # get current max token
    feed_name = f"tokenfeed_{b.doctor_id}_{date_key}"
    feed = db["tokenfeed"].find_one({"_key": feed_name})
    next_token = (feed.get("last_token", 0) + 1) if feed else 1
    db["tokenfeed"].update_one(
        {"_key": feed_name},
        {"$set": {"_key": feed_name, "doctor_id": b.doctor_id, "date": date_key, "last_token": next_token}},
        upsert=True,
    )

    data = b.model_dump()
    data["token"] = next_token
    _id = create_document("booking", data)
    return {"id": _id, "token": next_token}


class TokenUpdate(BaseModel):
    doctor_id: str
    date: str  # YYYY-MM-DD
    current_token: int


@app.post("/token/update")
def update_token(t: TokenUpdate):
    feed_name = f"tokenfeed_{t.doctor_id}_{t.date}"
    db["tokenfeed"].update_one(
        {"_key": feed_name},
        {"$set": {"_key": feed_name, "doctor_id": t.doctor_id, "date": t.date, "current_token": t.current_token}},
        upsert=True,
    )
    return {"status": "ok"}


@app.get("/token/status")
def token_status(doctor_id: str, date: str):
    feed_name = f"tokenfeed_{doctor_id}_{date}"
    feed = db["tokenfeed"].find_one({"_key": feed_name}) or {}
    if feed.get("_id"):
        feed["_id"] = str(feed["_id"])  # stringify
    return feed


# Utility endpoints for schema viewer
@app.get("/schema")
def get_schema_definitions():
    from inspect import getmembers, isclass
    import schemas as s
    out = {}
    for name, obj in getmembers(s):
        if isclass(obj) and hasattr(obj, "model_json_schema"):
            out[name] = obj.model_json_schema()
    return out


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
