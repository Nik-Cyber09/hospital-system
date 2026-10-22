import re
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, Dict, Any

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

def clean_email(v: str) -> str:
    v = v.strip().lower()
    if not EMAIL_REGEX.match(v) or len(v) > 254:
        raise ValueError('Invalid email address format.')
    return v

# ============ Account Schemas ============

class LoginRequest(BaseModel):
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return clean_email(v)

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v) < 1 or len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be 1-72 UTF-8 bytes.')
        return v

class CreateStaffRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str
    password: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return clean_email(v)

    @field_validator('password')
    @classmethod
    def validate_password_length(cls, v):
        if len(v) < 12 or len(v.encode('utf-8')) > 72:
            raise ValueError('Password must be at least 12 characters.')
        return v

class ChangePasswordRequest(BaseModel):
    currentPassword: str
    newPassword: str

    @field_validator('currentPassword')
    @classmethod
    def validate_current_password(cls, v):
        if len(v) < 1 or len(v.encode('utf-8')) > 72:
            raise ValueError('Current password is invalid.')
        return v

    @field_validator('newPassword')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 12 or len(v.encode('utf-8')) > 72:
            raise ValueError('New password must be at least 12 characters.')
        return v

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    createdAt: Optional[str] = None

# ============ Record Schemas ============

class PatientRecord(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=125)
    gender: Literal["Female", "Male", "Non-binary", "Prefer not to say"]
    phone: str = Field(..., min_length=3, max_length=40)
    condition: str = Field(..., min_length=1, max_length=240)
    doctorId: str = Field(default="", max_length=80)
    status: Literal["Stable", "Under care", "Needs follow-up"]

class DoctorRecord(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    specialty: str = Field(..., min_length=1, max_length=120)
    email: str
    phone: str = Field(..., min_length=3, max_length=40)
    status: Literal["On duty", "Off duty"]
    availability: str = Field(default="", max_length=200)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return clean_email(v)

class AppointmentRecord(BaseModel):
    patientId: str = Field(..., min_length=1, max_length=80)
    doctorId: str = Field(..., min_length=1, max_length=80)
    date: str  # ISO 8601 datetime
    reason: str = Field(..., min_length=1, max_length=240)
    status: Literal["Confirmed", "Waiting", "Completed", "Cancelled"]

class InvoiceRecord(BaseModel):
    patientId: str = Field(..., min_length=1, max_length=80)
    date: str  # ISO 8601 date
    description: str = Field(..., min_length=1, max_length=240)
    amount: float = Field(..., gt=0, le=1_000_000)
    status: Literal["Pending", "Paid", "Overdue"]

RECORD_SCHEMAS = {
    "patients": PatientRecord,
    "doctors": DoctorRecord,
    "appointments": AppointmentRecord,
    "invoices": InvoiceRecord,
}
