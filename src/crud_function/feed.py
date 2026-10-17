from sqlalchemy.ext.asyncio.session import AsyncSession
from ..schemas import CreatePost, UpdatePost
from ..db import Post as DBFeed
from sqlalchemy import select
from typing import List
import uuid


async def add_feed(session: AsyncSession, item: CreatePost) -> DBFeed:

    feed = DBFeed(**item.model_dump())
    session.add(feed)

    await session.commit()
    await session.refresh(feed)

    return feed


async def get_feeds(session: AsyncSession) -> List[DBFeed]:
    statment = select(DBFeed).order_by(DBFeed.created_at.desc())

    result = await session.execute(statment)
    return result.scalars().all()


async def get_users_feeds(session: AsyncSession, user_id: uuid.UUID) -> List[DBFeed]:
    statement = select(DBFeed).where(
        DBFeed.user_id == user_id).order_by(DBFeed.created_at.desc())

    result = await session.execute(statement)

    return result.scalars().all()


async def get_feed(session: AsyncSession, feed_id: uuid.UUID) -> DBFeed | None:
    statment = select(DBFeed).where(DBFeed.id == feed_id)

    result = await session.execute(statment)
    return result.scalar_one_or_none()


async def delete_feed(session: AsyncSession, feed: DBFeed) -> None:
    await session.delete(feed)
    await session.commit()


async def update_feed(session: AsyncSession, feed_id: uuid.UUID, updated_feed: UpdatePost) -> DBFeed | None:
    statement = select(DBFeed).where(DBFeed.id == feed_id)

    result = await session.execute(statement)
    feed = result.scalar_one_or_none()

    if feed is None:
        return None

    for key, value in updated_feed.model_dump().items():
        setattr(feed, key, value)

        await session.commit()
        await session.refresh(feed)
        return feed
