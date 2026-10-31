from fastapi import APIRouter

from app.api.v1 import auth, projects, workspaces

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(workspaces.router)
router.include_router(projects.router)
