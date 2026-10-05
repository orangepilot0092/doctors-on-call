from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List
from app.core.abdm_hpr import abdm_hpr_client, validate_and_encode_file
from app.schemas.hpr import UpdateProfessionalRequest

router = APIRouter(prefix="/hpr", tags=["ABDM HPR Data & Documents"])

@router.post("/fetch-professional")
async def fetch_professional(hpr_id: str):
    try:
        return await abdm_hpr_client.fetch_professional_info(hpr_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/update-professional")
async def update_professional(request: UpdateProfessionalRequest):
    try:
        # Convert Pydantic model to dict, respecting aliases
        payload = request.model_dump(by_alias=True)
        return await abdm_hpr_client.update_professional(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/fetch-documents")
async def fetch_documents(hpr_id: str):
    try:
        return await abdm_hpr_client.fetch_documents_list(hpr_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload-document")
async def upload_document(
    hpr_token: str = Form(...),
    document_id: int = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # 1. Validate and encode the file
        base64_data = validate_and_encode_file(file, document_type)
        
        # 2. Determine file type from content_type
        file_type = file.content_type.split('/')[-1]  # e.g., "pdf", "jpeg"
        if file_type == "jpg": file_type = "jpeg"
        
        # 3. Prepare payload for ABDM
        documents = [{
            "document_id": document_id,
            "document_type": document_type,
            "fileType": file_type,
            "data": base64_data
        }]
        
        return await abdm_hpr_client.upload_document(hpr_token, documents)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document upload failed: {str(e)}")
