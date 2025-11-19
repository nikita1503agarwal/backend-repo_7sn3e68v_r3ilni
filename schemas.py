"""
HamroSwasthya Database Schemas

Each Pydantic model below maps to a MongoDB collection with the lowercase
name of the class.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal, Dict
from datetime import datetime

# Core user for BloodLink + app auth
class AppUser(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None  # city/area
    age: Optional[int] = Field(None, ge=0, le=120)
    blood_group: Optional[str] = Field(None, description="A+, A-, B+, B-, AB+, AB-, O+, O-")
    karma_points: int = 0

# Emergency/SOS settings and emergency contacts
class EmergencyContact(BaseModel):
    name: str
    phone: str
    relation: Optional[str] = None

class SOSSetting(BaseModel):
    user_id: str
    contacts: List[EmergencyContact] = []
    preferred_hospital: Optional[str] = None

# Family health diary
class MedicalHistoryItem(BaseModel):
    date: Optional[datetime] = None
    note: str

class VaccinationItem(BaseModel):
    name: str
    due_date: Optional[datetime] = None
    completed: bool = False

class HealthUpdate(BaseModel):
    date: Optional[datetime] = None
    update: str

class BloodSugarLog(BaseModel):
    date: Optional[datetime] = None
    value_mgdl: float
    period: Literal['fasting','post-meal','random'] = 'random'

class MedicineReminder(BaseModel):
    name: str
    dosage: str
    time: str  # HH:MM
    days: List[str] = []  # ['Mon','Tue',...]
    active: bool = True

class Appointment(BaseModel):
    title: str
    date: datetime
    location: Optional[str] = None
    doctor: Optional[str] = None

class FamilyProfile(BaseModel):
    user_id: str
    photo_url: Optional[str] = None
    name: str
    age: Optional[int] = None
    blood_group: Optional[str] = None
    allergies: Optional[str] = None
    conditions: Optional[str] = None
    medical_history: List[MedicalHistoryItem] = []
    vaccinations: List[VaccinationItem] = []
    health_updates: List[HealthUpdate] = []
    sugar_logs: List[BloodSugarLog] = []
    medicine_reminders: List[MedicineReminder] = []
    appointments: List[Appointment] = []

# BloodLink Nepal
class BloodRequest(BaseModel):
    requester_id: str
    location: str
    blood_group: str
    units_needed: int
    urgency: Literal['low','medium','high'] = 'medium'
    note: Optional[str] = None
    status: Literal['open','matched','fulfilled','cancelled'] = 'open'

# Notices & alerts
class HealthNotice(BaseModel):
    title: str
    body: str
    city: Optional[str] = None
    region: Optional[str] = None
    tags: List[str] = []
    starts_at: Optional[datetime] = None
    ends_at: Optional[datetime] = None

# Medicine ordering
class MedicineItem(BaseModel):
    name: str
    quantity: int = 1

class MedicineOrder(BaseModel):
    user_id: str
    items: List[MedicineItem]
    address: str
    delivery_charge: float
    status: Literal['placed','confirmed','out-for-delivery','delivered','cancelled'] = 'placed'
    tracking_code: Optional[str] = None

# Hospitals & appointments
class Hospital(BaseModel):
    name: str
    city: Optional[str] = None
    departments: List[str] = []

class Doctor(BaseModel):
    name: str
    department: str
    hospital_id: str
    experience_years: Optional[int] = None

class Booking(BaseModel):
    user_id: str
    doctor_id: str
    date: datetime
    token: Optional[int] = None
    status: Literal['booked','cancelled','completed'] = 'booked'

class TokenFeed(BaseModel):
    doctor_id: str
    current_token: int = 0
