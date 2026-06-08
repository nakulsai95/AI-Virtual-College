"""Run learner code in a subject's mounted sandbox."""
from __future__ import annotations

from fastapi import APIRouter

from ..sandbox import SUPPORTED, run_code
from ..schemas import SandboxIn, SandboxOut

router = APIRouter(prefix="/api/sandbox", tags=["sandbox"])


@router.get("/supported")
def supported():
    return {"supported": SUPPORTED}


@router.post("/run", response_model=SandboxOut)
def run(body: SandboxIn):
    result = run_code(body.sandbox, body.code)
    return SandboxOut(**result, sandbox=body.sandbox)
