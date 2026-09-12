"""Service handling User entity lifecycle and database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException
from app.models.user import User, UserRole


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Fetch user by primary key UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Fetch user by unique email."""
        stmt = select(User).where(User.email == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        full_name: str,
        password_hash: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Create new user entity after checking uniqueness."""
        existing = await self.get_by_email(email)
        if existing:
            raise ConflictException(f"User with email '{email}' already exists")

        user = User(
            id=uuid.uuid4(),
            email=email.lower().strip(),
            full_name=full_name.strip(),
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user
