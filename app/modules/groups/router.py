from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.service import get_current_user
from app.modules.groups.schemas import GroupCreateRequest
from app.modules.groups.schemas import GroupMemberAddRequest
from app.modules.groups.schemas import GroupMemberResponse
from app.modules.groups.schemas import GroupResponse
from app.modules.groups.service import add_group_member
from app.modules.groups.service import create_group
from app.modules.groups.service import list_group_members
from app.modules.groups.service import list_user_groups

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def post_group(
	payload: GroupCreateRequest,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user),
) -> GroupResponse:
	group = create_group(db, name=payload.name, created_by_user_id=current_user.id)
	return GroupResponse.model_validate(group, from_attributes=True)


@router.get("", response_model=list[GroupResponse])
def get_groups(db: Session = Depends(get_db), current_user=Depends(get_current_user)) -> list[GroupResponse]:
	groups = list_user_groups(db, user_id=current_user.id)
	return [GroupResponse.model_validate(group, from_attributes=True) for group in groups]


@router.post("/{group_id}/members", response_model=GroupMemberResponse, status_code=status.HTTP_201_CREATED)
def post_group_member(
	group_id: str,
	payload: GroupMemberAddRequest,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user),
) -> GroupMemberResponse:
	member = add_group_member(
		db,
		group_id=group_id,
		requester_user_id=current_user.id,
		member_user_id=payload.user_id,
		role=payload.role,
	)
	return GroupMemberResponse.model_validate(member, from_attributes=True)


@router.get("/{group_id}/members", response_model=list[GroupMemberResponse])
def get_group_members(
	group_id: str,
	db: Session = Depends(get_db),
	current_user=Depends(get_current_user),
) -> list[GroupMemberResponse]:
	members = list_group_members(db, group_id=group_id, requester_user_id=current_user.id)
	return [GroupMemberResponse.model_validate(member, from_attributes=True) for member in members]
