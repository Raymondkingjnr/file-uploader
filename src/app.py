import uuid

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Form, status
from contextlib import asynccontextmanager
from .db import Post as DBPost, Task as DBTask, create_db_and_tables, get_async_session, User
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .images import imagekit
from .users import auth_backend, current_active_user, fastapi_users
from .schemas import UserCreate, UserRead, UserUpdate, PublicPost, CreatePost
from .crud_function import feed
from typing import List


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(fastapi_users.get_auth_router(
    auth_backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(
    UserRead, UserCreate), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_reset_password_router(),
                   prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_verify_router(
    UserRead), prefix="/auth", tags=["auth"])
app.include_router(fastapi_users.get_users_router(
    UserRead, UserUpdate), prefix="/users", tags=["users"])


@app.post("/post-feed", status_code=status.HTTP_201_CREATED, response_model=PublicPost)
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(...),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        file_bytes = await file.read()

        upload_result = await imagekit.files.upload(
            file=file_bytes,
            file_name=file.filename or "uploaded_file",
            use_unique_file_name=True,
            tags=["backend-upload"],
        )

        post_data = CreatePost(
            user_id=user.id,
            caption=caption,
            url=upload_result.url,
            file_type="video" if file.content_type and file.content_type.startswith(
                "video/") else "image",
            file_name=upload_result.name,
        )

        post_item = await feed.add_feed(session=session, item=post_data)

        return post_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await file.close()


@app.get("/get-feeds", response_model=List[PublicPost])
async def get_feeds(session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    try:
        posts_data = await feed.get_feeds(session=session)

        return posts_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-user-feeds/{user_id}", response_model=List[PublicPost])
async def get_user_feeds(user_id: uuid.UUID, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    user_feed = await feed.get_users_feeds(session=session, user_id=user_id)
    return user_feed


@app.get("/get-feed-by-id/{post_id}", response_model=PublicPost)
async def get_feed_by_id(post_id: uuid.UUID, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    feed_item = await feed.get_feed(session=session, post_id=post_id)

    if not feed_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {post_id} not found")

    return feed_item


@app.delete("/delete-feed/{post_id}")
async def delete_feed(post_id: uuid.UUID, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    feed_item = await feed.get_feed(session=session, post_id=post_id)

    if not feed_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {post_id} not found")

    if feed_item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to delete this post")

    await feed.delete_feed(session=session, feed=feed_item)

    return {"message": f"Post with id {post_id} has been deleted successfully."}


@app.get("/tasks")
async def get_tasks(
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(DBTask))
    tasks = result.scalars().all()
    return {
        "tasks": [
            {
                "id": str(t.id),
                "user_id": str(t.user_id),
                "title": t.title,
                "description": t.description,
                "tasksList": t.tasksList,
            }
            for t in tasks
        ]
    }


@app.get("/tasks/{user_id}")
async def get_tasks_by_user(
    user_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    user_uuid = uuid.UUID(user_id)
    result = await session.execute(
        select(DBTask).where(DBTask.user_id == user_uuid)
    )
    tasks = result.scalars().all()
    return {
        "tasks": [
            {
                "id": str(t.id),
                "user_id": str(t.user_id),
                "title": t.title,
                "description": t.description,
                "tasksList": t.tasksList,
            }
            for t in tasks
        ]
    }


@app.post("/tasks")
async def create_task(
    title: str = Form(...),
    description: str = Form(...),
    tasksList: str = Form(...),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        task = DBTask(
            user_id=user.id,
            title=title,
            description=description,
            tasksList=tasksList,
        )

        session.add(task)
        await session.commit()
        await session.refresh(task)

        return {
            "id": str(task.id),
            "user_id": str(task.user_id),
            "title": task.title,
            "description": task.description,
            "tasksList": task.tasksList,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
