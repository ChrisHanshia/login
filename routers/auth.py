from datetime import timedelta, datetime
from typing_extensions import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = '197b2c37c391bed93fe80344fe73b806947a65e36206e05a1a23c2fa12702fe3'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    first_name: str
    last_name: str
    password: str
    date_of_birth: str
    register_number: str
    phone_number: str
    gender: str
    address: str
    course: str


class Token(BaseModel):
    access_token: str
    token_type: str

class PasswordUpdate(BaseModel):
    old_password: str = Field(..., alias="oldPassword")
    new_password: str = Field(..., alias="newPassword")
    confirm_password: str = Field(..., alias="confirmPassword")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def authenticated_user(username: str, password: str, db):
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int,  expires_delta: timedelta):
    encode = {'sub': username, 'id': user_id, }
    expires = datetime.utcnow() + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='could not validate user.')
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='could not validate user.')


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency,
                      create_user_request: CreateUserRequest):
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        date_of_birth=create_user_request.date_of_birth,
        register_number=create_user_request.register_number,
        phone_number=create_user_request.phone_number,
        gender=create_user_request.gender,
        address=create_user_request.address,
        course=create_user_request.course
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    user = authenticated_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='could not validate user.')
    token = create_access_token(user.username, user.id,  timedelta(minutes=20))

    return {'access_token': token, 'token_type': 'bearer'}


@router.put("/forget_password")
async def forget_password(
        username_or_email: str,
        new_password: str,
        confirm_password: str,
        db: Session = Depends(get_db)
):
    user = db.query(Users).filter(
        (Users.username == username_or_email) | (Users.email == username_or_email)
    ).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    hashed_password = bcrypt_context.hash(new_password)
    user.hashed_password = hashed_password
    db.commit()


@router.put("/reset_password")
async def reset_password(password_update: PasswordUpdate,
                         current_user: dict = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.id == current_user['id']).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    old_password = password_update.old_password
    new_password = password_update.new_password
    confirm_password = password_update.confirm_password

    if not bcrypt_context.verify(old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password")

    if new_password != confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="New password and confirm password do not match")

    hashed_password = bcrypt_context.hash(new_password)
    user.hashed_password = hashed_password
    db.commit()

    return {"message": "Password updated successfully"}


@router.get("/users", status_code=status.HTTP_200_OK)
async def get_users(db: Session = Depends(get_db)):
    users = db.query(Users).all()
    return users
