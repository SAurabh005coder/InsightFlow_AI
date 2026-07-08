from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import RoleChecker
from app.services.reports import ReportService
from typing import Optional

router = APIRouter()

@router.get("/export/excel")
def export_excel(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["CEO", "Data_Analyst", "Store_Manager"]))
):
    try:
        buffer, filename = ReportService.generate_excel_report(db, dataset_id)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate Excel sheet: {str(e)}"
        )

@router.get("/export/pdf")
def export_pdf(
    dataset_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(RoleChecker(["CEO", "Data_Analyst", "Store_Manager"]))
):
    try:
        buffer, filename = ReportService.generate_pdf_report(db, dataset_id)
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compile PDF summary: {str(e)}"
        )
