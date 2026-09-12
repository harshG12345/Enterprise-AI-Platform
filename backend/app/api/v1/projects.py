"""Projects REST API endpoints for workspace management."""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.core.responses import APIResponse
from app.database.database import get_db
from app.models.user import User
from app.schemas.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Project Workspace",
)
async def create_project(
    payload: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectResponse]:
    """Create a new AI/ML project workspace."""
    service = ProjectService(db)
    project = await service.create_project(payload, current_user)

    # Return formatted project response
    project_response = ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        owner_email=current_user.email,
        owner_name=current_user.full_name,
        dataset_count=0,
        model_count=0,
        experiment_count=0,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
    return APIResponse(
        success=True,
        data=project_response,
        message="Project workspace created successfully",
    )


@router.get(
    "",
    response_model=APIResponse[ProjectListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Projects",
)
async def list_projects(
    page: int = Query(1, ge=1, description="Page index"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search query across project name or description"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectListResponse]:
    """List accessible projects with pagination and search filtering."""
    service = ProjectService(db)
    items, total, total_pages = await service.list_projects(
        user=current_user,
        page=page,
        page_size=page_size,
        search=search,
    )

    return APIResponse(
        success=True,
        data=ProjectListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        ),
        message="Projects retrieved successfully",
    )


@router.get(
    "/{project_id}",
    response_model=APIResponse[ProjectDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Project Details",
)
async def get_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectDetailResponse]:
    """Get project details and summaries of associated datasets, models, and experiments."""
    service = ProjectService(db)
    project_detail = await service.get_project_by_id(project_id, current_user)

    return APIResponse(
        success=True,
        data=project_detail,
        message="Project details retrieved successfully",
    )


@router.put(
    "/{project_id}",
    response_model=APIResponse[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Update Project",
)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ProjectResponse]:
    """Update project metadata with ownership enforcement."""
    service = ProjectService(db)
    updated_project = await service.update_project(project_id, payload, current_user)

    return APIResponse(
        success=True,
        data=ProjectResponse(
            id=updated_project.id,
            name=updated_project.name,
            description=updated_project.description,
            owner_id=updated_project.owner_id,
            owner_email=current_user.email,
            owner_name=current_user.full_name,
            created_at=updated_project.created_at,
            updated_at=updated_project.updated_at,
        ),
        message="Project updated successfully",
    )


@router.delete(
    "/{project_id}",
    response_model=APIResponse[None],
    status_code=status.HTTP_200_OK,
    summary="Delete Project",
)
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[None]:
    """Delete project workspace and all cascaded children."""
    service = ProjectService(db)
    await service.delete_project(project_id, current_user)

    return APIResponse(
        success=True,
        data=None,
        message="Project deleted successfully",
    )
