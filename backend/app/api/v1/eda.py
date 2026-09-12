"""API endpoints for Exploratory Data Analysis."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.eda import EDAResponse
from app.services.eda_service import EDAService

router = APIRouter(prefix="/datasets", tags=["Exploratory Data Analysis"])


@router.get(
    "/{dataset_id}/eda",
    response_model=APIResponse[EDAResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive Exploratory Data Analysis report",
)
async def get_dataset_eda(
    dataset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Compute and return full statistical EDA profile including distributions, outliers, and correlations."""
    eda_service = EDAService(db)
    report = await eda_service.generate_eda_report(dataset_id=dataset_id, user=current_user)
    return APIResponse(
        success=True,
        data=report,
        message="Exploratory Data Analysis generated successfully",
    )
