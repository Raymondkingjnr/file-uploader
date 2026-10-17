import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from fastapi_users import schemas
from typing import List


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    pass


class UserUpdate(schemas.BaseUserUpdate):
    pass


class PostBase(BaseModel):
    caption: str | None = None
    url: str
    file_type: str
    file_name: str


class CreatePost(PostBase):
    user_id: uuid.UUID


class PublicPost(PostBase):
    id: uuid.UUID
    created_at: datetime
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class UpdatePost(BaseModel):
    caption: str | None = None
    url: str | None = None
    file_type: str | None = None
    file_name: str | None = None


class PublicUserWithFeeds(UserRead):
    post: List[PublicPost] = []
