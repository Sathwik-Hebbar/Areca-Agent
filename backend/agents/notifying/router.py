from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.db.models.logs.notification import Notification, NotificationChannel, NotificationStatus

router = APIRouter(prefix="/agents/notifying", tags=["Notifying Agent"])


@router.post("/send")
def send_notification(farmer_id: str, content: str, channel: NotificationChannel = NotificationChannel.IN_APP, db: Session = Depends(get_db)):
    """
    Notifying/Monitoring Agent: Dispatches alert to SMS/Push/In-App queue.
    """
    notification = Notification(
        farmer_id=farmer_id,
        channel=channel,
        content=content,
        status=NotificationStatus.SENT
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
