from uuid import UUID

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Group
from app.models.entities import GroupMember
from app.models.entities import User


def create_group(db: Session, *, name: str, created_by_user_id: UUID | str) -> Group:
    group = Group(name=name.strip(), created_by_user_id=created_by_user_id)
    db.add(group)
    db.flush()

    creator_membership = GroupMember(group_id=group.id, user_id=created_by_user_id, role="owner")
    db.add(creator_membership)

    db.commit()
    db.refresh(group)
    return group


def list_user_groups(db: Session, *, user_id: UUID | str) -> list[Group]:
    stmt = (
        select(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .where(GroupMember.user_id == user_id)
        .order_by(Group.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def ensure_group_member(db: Session, *, group_id: UUID | str, user_id: UUID | str) -> GroupMember:
    membership = db.scalar(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
    )
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a member of this group")
    return membership


def add_group_member(
    db: Session,
    *,
    group_id: UUID | str,
    requester_user_id: UUID | str,
    member_user_id: UUID | str,
    role: str,
) -> GroupMember:
    ensure_group_member(db, group_id=group_id, user_id=requester_user_id)

    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    user = db.get(User, member_user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    existing = db.scalar(
        select(GroupMember).where(GroupMember.group_id == group_id, GroupMember.user_id == member_user_id)
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a member")

    membership = GroupMember(group_id=group_id, user_id=member_user_id, role=role)
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def list_group_members(
    db: Session,
    *,
    group_id: UUID | str,
    requester_user_id: UUID | str,
) -> list[GroupMember]:
    ensure_group_member(db, group_id=group_id, user_id=requester_user_id)

    group = db.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    stmt = (
        select(GroupMember)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.joined_at.asc(), GroupMember.user_id.asc())
    )
    return list(db.scalars(stmt).all())
