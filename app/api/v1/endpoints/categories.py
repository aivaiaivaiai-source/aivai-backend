from fastapi import APIRouter, Depends

from app.api.deps import get_category_service
from app.schemas.category import CategoryTreeNode
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/tree", response_model=list[CategoryTreeNode])
async def get_category_tree(
    service: CategoryService = Depends(get_category_service),
) -> list[CategoryTreeNode]:
    return await service.get_category_tree()
