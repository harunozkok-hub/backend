from datetime import datetime, timezone
from sqlalchemy.orm import Session
from models import RefreshToken
from dependencies.deps import get_db


def cleanup_expired_refresh_tokens():
    now = datetime.now(timezone.utc)

    # use generator to get DB session (like FastAPI does)
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        deleted = (
            db.query(RefreshToken)
            .filter((RefreshToken.expires_at < now) | (RefreshToken.used == True) | (RefreshToken.revoked == True))
            .delete(synchronize_session=False)
        )
        db.commit()
        print(f"[CLEANUP] Deleted {deleted} expired refresh tokens.")
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")
        db.rollback()
    finally:
        db_gen.close()
