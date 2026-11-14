from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbSession
from app.schemas.auth import Token, UserCreate, UserRead
from app.schemas.common import CONFLICT, INVALID_LOGIN
from app.services import auth as auth_service

router = APIRouter()


@router.post("/register", status_code=201, summary="Create an account", responses=CONFLICT)
async def register(payload: UserCreate, db: DbSession) -> UserRead:
    return await auth_service.register(db, payload)


@router.post("/token", summary="Log in and get an access token", responses=INVALID_LOGIN)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession) -> Token:
    """An OAuth2 password form: put the e-mail in `username`.

    This is the endpoint the **Authorize** button of `/docs` talks to.
    """
    return await auth_service.login(db, email=form.username, password=form.password)
