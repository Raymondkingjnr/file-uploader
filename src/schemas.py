import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from fastapi_users import schemas


class Post(BaseModel):
    title: str
    content: str


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class PostBase(BaseModel):
    caption: str
    url: str
    file_type: str
    file_name: str


class CreatePost(PostBase):
    user_id: uuid.UUID


class PublicPost(PostBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
