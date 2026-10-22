from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any, List
from app.database import get_database
from app.models import HospitalRecord
from app.schemas import RECORD_SCHEMAS
from app.middleware.auth import verify_auth_cookie
from app.config import settings

router = APIRouter(prefix="/api/records", tags=["records"])

def generate_id(record_type: str, index: int) -> str:
    """Generate prefixed ID for a record."""
    prefixes = {
        "patients": "PT",
        "doctors": "DR",
        "appointments": "AP",
        "invoices": "INV",
    }
    prefix = prefixes.get(record_type, "REC")
    return f"{prefix}-{index:05d}"

async def get_next_id(record_type: str) -> str:
    """Get the next sequential ID for a record type."""
    db = get_database()
    records_model = HospitalRecord(db)
    records = await records_model.find_by_type(record_type)
    indices = []
    for r in records:
        rid = str(r.get("id", ""))
        parts = rid.split("-")
        if len(parts) == 2 and parts[1].isdigit():
            indices.append(int(parts[1]))
    next_index = max(indices) + 1 if indices else 1
    return generate_id(record_type, next_index)

def check_origin(request: Request):
    """Verify request origin for CSRF protection when Origin header is sent."""
    origin = request.headers.get("origin")
    if not origin:
        return
    origin_clean = origin.rstrip("/")
    allowed_clean = [o.rstrip("/") for o in settings.allowed_origins]
    if origin_clean in allowed_clean:
        return
    import os
    from urllib.parse import urlparse
    if os.getenv("VERCEL") == "1" or settings.node_env != "development":
        parsed = urlparse(origin_clean)
        if parsed.netloc.endswith(".vercel.app"):
            return
    raise HTTPException(status_code=403, detail="Forbidden: Origin not allowed.")

@router.get("/{record_type}")
async def list_records(
    record_type: str,
    auth_payload: dict = Depends(verify_auth_cookie),
):
    """Get all records of a type."""
    if record_type not in RECORD_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid record type.")

    db = get_database()
    records_model = HospitalRecord(db)
    records = await records_model.find_by_type(record_type)

    items = [
        {
            "id": record["id"],
            **record.get("data", {})
        }
        for record in records
    ]
    return {"records": items}

@router.get("/{record_type}/{record_id}")
async def get_record(
    record_type: str,
    record_id: str,
    auth_payload: dict = Depends(verify_auth_cookie),
):
    """Get a specific record."""
    if record_type not in RECORD_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid record type.")

    db = get_database()
    records_model = HospitalRecord(db)
    record = await records_model.find_one(record_type, record_id)

    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")

    rec_data = {
        "id": record["id"],
        **record.get("data", {})
    }
    return {"record": rec_data, **rec_data}

@router.post("/{record_type}")
async def create_record(
    record_type: str,
    payload: Dict[str, Any],
    request: Request,
    auth_payload: dict = Depends(verify_auth_cookie),
):
    """Create a new hospital record."""
    check_origin(request)

    if record_type not in RECORD_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid record type.")

    schema = RECORD_SCHEMAS[record_type]
    try:
        validated_data = schema(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = get_database()
    records_model = HospitalRecord(db)

    # Validate relationships
    if record_type == "patients" and validated_data.doctorId:
        doctor = await records_model.find_one("doctors", validated_data.doctorId)
        if not doctor:
            raise HTTPException(status_code=400, detail="Assigned doctor was not found.")

    if record_type == "appointments":
        patient = await records_model.find_one("patients", validated_data.patientId)
        if not patient:
            raise HTTPException(status_code=400, detail="Patient was not found.")
        doctor = await records_model.find_one("doctors", validated_data.doctorId)
        if not doctor:
            raise HTTPException(status_code=400, detail="Doctor was not found.")

    if record_type == "invoices":
        patient = await records_model.find_one("patients", validated_data.patientId)
        if not patient:
            raise HTTPException(status_code=400, detail="Patient was not found.")

    new_id = await get_next_id(record_type)
    record_data = validated_data.model_dump()
    record = await records_model.create(record_type, new_id, record_data)

    rec_obj = {
        "id": record["id"],
        **record.get("data", {})
    }
    return {"record": rec_obj, **rec_obj}

@router.put("/{record_type}/{record_id}")
async def update_record(
    record_type: str,
    record_id: str,
    payload: Dict[str, Any],
    request: Request,
    auth_payload: dict = Depends(verify_auth_cookie),
):
    """Update an existing record."""
    check_origin(request)

    if record_type not in RECORD_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid record type.")

    schema = RECORD_SCHEMAS[record_type]
    try:
        validated_data = schema(**payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = get_database()
    records_model = HospitalRecord(db)

    existing = await records_model.find_one(record_type, record_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Record not found.")

    # Validate relationships
    if record_type == "patients" and validated_data.doctorId:
        doctor = await records_model.find_one("doctors", validated_data.doctorId)
        if not doctor:
            raise HTTPException(status_code=400, detail="Assigned doctor was not found.")

    if record_type == "appointments":
        patient = await records_model.find_one("patients", validated_data.patientId)
        if not patient:
            raise HTTPException(status_code=400, detail="Patient was not found.")
        doctor = await records_model.find_one("doctors", validated_data.doctorId)
        if not doctor:
            raise HTTPException(status_code=400, detail="Doctor was not found.")

    if record_type == "invoices":
        patient = await records_model.find_one("patients", validated_data.patientId)
        if not patient:
            raise HTTPException(status_code=400, detail="Patient was not found.")

    record_data = validated_data.model_dump()
    updated = await records_model.update_one(record_type, record_id, record_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Record not found.")

    rec_obj = {
        "id": updated["id"],
        **updated.get("data", {})
    }
    return {"record": rec_obj, **rec_obj}

@router.delete("/{record_type}/{record_id}")
async def delete_record(
    record_type: str,
    record_id: str,
    request: Request,
    auth_payload: dict = Depends(verify_auth_cookie),
):
    """Delete a record with dependency checks."""
    check_origin(request)

    if record_type not in RECORD_SCHEMAS:
        raise HTTPException(status_code=400, detail="Invalid record type.")

    db = get_database()
    records_model = HospitalRecord(db)

    existing = await records_model.find_one(record_type, record_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Record not found.")

    # Check for dependent records
    dependent_filter = {}
    if record_type == "doctors":
        dependent_filter = {
            "$or": [
                {"type": "patients", "data.doctorId": record_id},
                {"type": "appointments", "data.doctorId": record_id},
            ]
        }
    elif record_type == "patients":
        dependent_filter = {
            "$or": [
                {"type": "appointments", "data.patientId": record_id},
                {"type": "invoices", "data.patientId": record_id},
            ]
        }

    if dependent_filter:
        has_dependents = await records_model.find_dependents(dependent_filter)
        if has_dependents:
            singular = record_type.rstrip('s')
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete {singular} because other active records reference it. Reassign or remove those records first."
            )

    await records_model.delete_one(record_type, record_id)
    singular = record_type.rstrip('s').capitalize()
    return {"message": f"{singular} deleted successfully."}
