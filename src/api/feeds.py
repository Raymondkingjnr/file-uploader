from fastapi import APIRouter, HTTPException, File, UploadFile, Depends, Form, status
import uuid
from ..crud_function import feed
from sqlalchemy.ext.asyncio.session import AsyncSession
from ..db import get_async_session, User
from ..images import imagekit
from ..schemas import PublicPost, CreatePost, UpdatePost
from ..users import current_active_user
from typing import List

router = APIRouter()


@router.post("/post-feed", status_code=status.HTTP_201_CREATED, response_model=PublicPost)
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


@router.get("/get-feeds", response_model=List[PublicPost])
async def get_feeds(session: AsyncSession = Depends(get_async_session), _: User = Depends(current_active_user)):
    try:
        posts_data = await feed.get_feeds(session=session)

        return posts_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/get-user-feeds/{user_id}", response_model=List[PublicPost])
async def get_user_feeds(user_id: uuid.UUID, session: AsyncSession = Depends(get_async_session), _: User = Depends(current_active_user)):
    user_feed = await feed.get_users_feeds(session=session, user_id=user_id)
    return user_feed


@router.get("/get-feed-by-id/{feed_id}", response_model=PublicPost)
async def get_feed_by_id(feed_id: uuid.UUID, session: AsyncSession = Depends(get_async_session), _: User = Depends(current_active_user)):
    feed_item = await feed.get_feed(session=session, feed_id=feed_id)

    if not feed_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {feed_id} not found")

    return feed_item


@router.delete("/delete-feed/{feed_id}", status_code=status.HTTP_200_OK)
async def delete_feed(feed_id: uuid.UUID, session: AsyncSession = Depends(get_async_session), user: User = Depends(current_active_user)):
    feed_item = await feed.get_feed(session=session, feed_id=feed_id)

    if not feed_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {feed_id} not found")

    if feed_item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to delete this post")

    await feed.delete_feed(session=session, feed=feed_item)

    return {"message": f"Post with id {feed_id} has been deleted successfully."}


@router.patch("/update-feed/{feed_id}", status_code=status.HTTP_200_OK, response_model=PublicPost)
async def update_feed(feed_id: uuid.UUID,
                      file: UploadFile = File(...),
                      caption: str = Form(...),
                      session: AsyncSession = Depends(get_async_session),
                      user: User = Depends(current_active_user)):

    feed_item = await feed.get_feed(session=session, feed_id=feed_id)

    if not feed_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"post with id {feed_id} not found")

    if feed_item.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to update this post")

    file_bytes = await file.read()

    upload_result = await imagekit.files.upload(
        file=file_bytes,
        file_name=file.filename or "uploaded_file",
        use_unique_file_name=True,
        tags=["backend-upload"],
    )
    feed_items = UpdatePost(
        caption=caption,
        url=upload_result.url,
        file_type="video" if file.content_type and file.content_type.startswith(
            "video/") else "image",
        file_name=upload_result.name,
    )

    updated_feed = await feed.update_feed(session=session, feed_id=feed_id, updated_feed=feed_items)

    return updated_feed
