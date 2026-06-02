"""Publication Service — grade broadcast and snapshot lifecycle.

Core invariant:
    No grade becomes visible in the student portal before the professor's
    explicit broadcast action creates a current PublicationSnapshot.

    Portal read model (AC-5):
    - ONLY reads publication_snapshots WHERE is_current = 1.
    - NEVER joins or reads grade_entries or calculation_results.

Rollback / preflight policy (task 9):
    If preflight validation fails (e.g. no validated grades, missing
    recipients), the service raises PreflightError and sets the
    BroadcastJob.status = 'failed' — no snapshots are created.

    Legacy Node.js upload → match → send routes run independently and are
    not affected by this service.  They must NOT be modified here.

Observability (task 10):
    Every audit event includes broadcast_job_id and aggregated totals.
    request_id is propagated when provided by the caller.
    Per-channel counts are available from BroadcastJob.total_success /
    total_failed and from NotificationDelivery rows grouped by channel.

Dry-run (task 6):
    compute_dry_run_counts() returns recipient counts without persisting
    any database rows.

Re-publication (task 7):
    republish() creates a new BroadcastJob and new snapshot versions.
    Previous snapshots are marked is_current=False but kept intact for
    the audit trail.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from backend.app.models.academic import AuditLog
from backend.app.models.publication import (
    DELIVERY_STATUS_FAILED,
    DELIVERY_STATUS_SENT,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    BroadcastJob,
    NotificationDelivery,
    PublicationSnapshot,
)

LOGGER = logging.getLogger("backend.publication.service")


# ---------------------------------------------------------------------------
# Audit action constants
# ---------------------------------------------------------------------------

ACTION_PUBLICATION_START = "publication_start"
ACTION_PUBLICATION_CONFIRMED = "publication_confirmed"
ACTION_SNAPSHOT_CREATED = "snapshot_created"
ACTION_DELIVERY_COMPLETED = "delivery_completed"
ACTION_DELIVERY_FAILED = "delivery_failed"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PreflightError(ValueError):
    """Raised when broadcast preflight validation fails.

    The BroadcastJob is set to status='failed' before this exception is raised.
    No snapshots are created.
    """


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class PublicationService:
    """Orchestrates the grade publication lifecycle.

    All methods accept an explicit ``session`` argument; the caller is
    responsible for transaction management (commit / rollback).

    Observability (task 10):
    - All audit events include broadcast_job_id as entity_id.
    - totals (total_recipients, total_success, total_failed) are stored on
      BroadcastJob and included in audit after_json.
    - request_id is forwarded to audit records when provided.
    """

    # ------------------------------------------------------------------
    # 1. Create broadcast job
    # ------------------------------------------------------------------

    def create_broadcast_job(
        self,
        session: Session,
        teaching_assignment_id: int,
        actor_user_id: int,
        job_type: str,
        channels: list[str],
        *,
        class_group_id: int | None = None,
    ) -> BroadcastJob:
        """Create a new BroadcastJob in ``pending`` status.

        The job is the publication trigger (AC-2).  Snapshots are NOT created
        here — call ``create_publication_snapshots`` after this.

        Parameters
        ----------
        session:
            Active SQLAlchemy session.
        teaching_assignment_id:
            The teaching assignment being published.
        actor_user_id:
            The professor (or delegate) triggering the broadcast.
        job_type:
            Descriptive label, e.g. ``"grade_publication"`` or ``"dry_run"``.
        channels:
            List of channel identifiers, e.g. ``["whatsapp"]``.
        class_group_id:
            Optional scope restriction to a single class group.
        """
        job = BroadcastJob(
            teaching_assignment_id=teaching_assignment_id,
            actor_user_id=actor_user_id,
            job_type=job_type,
            channels_json=json.dumps(channels),
            class_group_id=class_group_id,
            status=JOB_STATUS_PENDING,
        )
        session.add(job)
        session.flush()  # populate job.id

        LOGGER.info(
            "broadcast_job_created",
            extra={
                "broadcast_job_id": job.id,
                "job_type": job_type,
                "teaching_assignment_id": teaching_assignment_id,
                "actor_user_id": actor_user_id,
                "channels": channels,
            },
        )
        return job

    # ------------------------------------------------------------------
    # 2. Create publication snapshots
    # ------------------------------------------------------------------

    def create_publication_snapshots(
        self,
        session: Session,
        job: BroadcastJob,
        grade_data: list[dict[str, Any]],
        *,
        request_id: str | None = None,
    ) -> list[PublicationSnapshot]:
        """Create immutable publication snapshots for each student in grade_data.

        Implements AC-1, AC-2, AC-4:
        - Each snapshot is linked to ``job``.
        - Previous is_current=True snapshots for the same (student_id,
          teaching_assignment_id) are set to is_current=False BEFORE
          the new snapshot is inserted.
        - snapshot_version is incremented from the latest existing version
          for each student (starts at 1).
        - Logs ``snapshot_created`` audit event.

        Parameters
        ----------
        session:
            Active SQLAlchemy session.
        job:
            The BroadcastJob triggering this publication.
        grade_data:
            List of dicts with keys:
                - student_id (int)
                - published_score (float | None)
                - published_state (str)
                - payload (dict)  — full grade payload including formula_version
        request_id:
            Optional request correlation ID for audit logging.

        Raises
        ------
        PreflightError
            If grade_data is empty (no recipients to publish to).
        """
        if not grade_data:
            job.status = JOB_STATUS_FAILED
            session.flush()
            raise PreflightError(
                f"broadcast_job_id={job.id}: grade_data is empty — no snapshots created"
            )

        # Mark job as running
        job.status = JOB_STATUS_RUNNING
        session.flush()

        self.record_audit_event(
            session,
            actor_user_id=job.actor_user_id,
            action=ACTION_PUBLICATION_START,
            entity_type="broadcast_job",
            entity_id=str(job.id),
            request_id=request_id,
            after_json=json.dumps(
                {
                    "broadcast_job_id": job.id,
                    "job_type": job.job_type,
                    "total_recipients": len(grade_data),
                    "channels": json.loads(job.channels_json or "[]"),
                }
            ),
        )

        snapshots: list[PublicationSnapshot] = []
        teaching_assignment_id = job.teaching_assignment_id

        for entry in grade_data:
            student_id: int = entry["student_id"]

            # Determine next snapshot version
            max_version_row = session.execute(
                select(func.max(PublicationSnapshot.snapshot_version)).where(
                    PublicationSnapshot.student_id == student_id,
                    PublicationSnapshot.teaching_assignment_id == teaching_assignment_id,
                )
            ).scalar()
            next_version = (max_version_row or 0) + 1

            # Invalidate previous current snapshot for this student/context
            session.execute(
                update(PublicationSnapshot)
                .where(
                    PublicationSnapshot.student_id == student_id,
                    PublicationSnapshot.teaching_assignment_id == teaching_assignment_id,
                    PublicationSnapshot.is_current.is_(True),
                )
                .values(is_current=False)
            )

            snapshot = PublicationSnapshot(
                student_id=student_id,
                teaching_assignment_id=teaching_assignment_id,
                broadcast_job_id=job.id,
                snapshot_version=next_version,
                published_score=entry.get("published_score"),
                published_state=entry["published_state"],
                published_payload_json=json.dumps(entry.get("payload", {})),
                is_current=True,
                published_at=datetime.now(UTC),
            )
            session.add(snapshot)
            session.flush()
            snapshots.append(snapshot)

            self.record_audit_event(
                session,
                actor_user_id=job.actor_user_id,
                action=ACTION_SNAPSHOT_CREATED,
                entity_type="publication_snapshot",
                entity_id=str(snapshot.id),
                request_id=request_id,
                after_json=json.dumps(
                    {
                        "broadcast_job_id": job.id,
                        "student_id": student_id,
                        "snapshot_version": next_version,
                        "published_state": entry["published_state"],
                    }
                ),
            )

        # Update job totals
        job.total_recipients = len(snapshots)
        job.status = JOB_STATUS_COMPLETED
        job.completed_at = datetime.now(UTC)
        session.flush()

        self.record_audit_event(
            session,
            actor_user_id=job.actor_user_id,
            action=ACTION_PUBLICATION_CONFIRMED,
            entity_type="broadcast_job",
            entity_id=str(job.id),
            request_id=request_id,
            after_json=json.dumps(
                {
                    "broadcast_job_id": job.id,
                    "total_recipients": job.total_recipients,
                    "total_success": job.total_success,
                    "total_failed": job.total_failed,
                    "channels": json.loads(job.channels_json or "[]"),
                }
            ),
        )

        LOGGER.info(
            "publication_snapshots_created",
            extra={
                "broadcast_job_id": job.id,
                "snapshot_count": len(snapshots),
                "request_id": request_id,
            },
        )
        return snapshots

    # ------------------------------------------------------------------
    # 3. Record delivery outcome
    # ------------------------------------------------------------------

    def record_delivery_outcome(
        self,
        session: Session,
        job_id: int,
        student_id: int,
        channel: str,
        destination: str,
        success: bool,
        *,
        error_code: str | None = None,
        error_message: str | None = None,
        request_id: str | None = None,
    ) -> NotificationDelivery:
        """Record the outcome of a single delivery attempt (AC-3).

        Updates BroadcastJob.total_success or total_failed atomically.
        Logs ``delivery_completed`` or ``delivery_failed`` audit event.

        Parameters
        ----------
        session:
            Active SQLAlchemy session.
        job_id:
            ID of the parent BroadcastJob.
        student_id:
            Recipient student ID.
        channel:
            Channel used, e.g. ``"whatsapp"``.
        destination:
            Phone / email destination (opaque string from caller).
        success:
            True if delivered; False if failed.
        error_code:
            Provider error code (only when success=False).
        error_message:
            Human-readable error detail (only when success=False).
        request_id:
            Optional correlation ID for audit logging.
        """
        status = DELIVERY_STATUS_SENT if success else DELIVERY_STATUS_FAILED
        delivery = NotificationDelivery(
            broadcast_job_id=job_id,
            student_id=student_id,
            channel=channel,
            destination=destination,
            status=status,
            error_code=error_code,
            error_message=error_message,
            attempt=1,
        )
        session.add(delivery)
        session.flush()

        # Update job totals
        if success:
            session.execute(
                update(BroadcastJob)
                .where(BroadcastJob.id == job_id)
                .values(total_success=BroadcastJob.total_success + 1)
            )
            audit_action = ACTION_DELIVERY_COMPLETED
        else:
            session.execute(
                update(BroadcastJob)
                .where(BroadcastJob.id == job_id)
                .values(total_failed=BroadcastJob.total_failed + 1)
            )
            audit_action = ACTION_DELIVERY_FAILED

        self.record_audit_event(
            session,
            actor_user_id=None,
            action=audit_action,
            entity_type="notification_delivery",
            entity_id=str(delivery.id),
            request_id=request_id,
            after_json=json.dumps(
                {
                    "broadcast_job_id": job_id,
                    "student_id": student_id,
                    "channel": channel,
                    "status": status,
                    "error_code": error_code,
                }
            ),
        )

        LOGGER.info(
            audit_action,
            extra={
                "broadcast_job_id": job_id,
                "student_id": student_id,
                "channel": channel,
                "status": status,
                "request_id": request_id,
            },
        )
        return delivery

    # ------------------------------------------------------------------
    # 4. Get current snapshots for portal (AC-5 read model)
    # ------------------------------------------------------------------

    def get_current_snapshots_for_portal(
        self,
        session: Session,
        student_id: int,
        teaching_assignment_id: int | None = None,
    ) -> list[PublicationSnapshot]:
        """Return current published snapshots for the student portal (AC-5).

        READ MODEL CONSTRAINT:
        - ONLY returns rows WHERE is_current = True.
        - NEVER reads grade_entries or calculation_results.
        - NEVER returns is_current=False (historical) snapshots.

        Parameters
        ----------
        session:
            Active SQLAlchemy session.
        student_id:
            The student whose grades are being requested.
        teaching_assignment_id:
            Optional filter to a single teaching assignment.
        """
        stmt = select(PublicationSnapshot).where(
            PublicationSnapshot.student_id == student_id,
            PublicationSnapshot.is_current.is_(True),
        )
        if teaching_assignment_id is not None:
            stmt = stmt.where(
                PublicationSnapshot.teaching_assignment_id == teaching_assignment_id
            )
        return list(session.execute(stmt).scalars().all())

    # ------------------------------------------------------------------
    # 5. Dry-run counts (task 6)
    # ------------------------------------------------------------------

    def compute_dry_run_counts(
        self,
        session: Session,
        teaching_assignment_id: int,
        class_group_id: int | None = None,
    ) -> dict[str, Any]:
        """Return expected recipient counts WITHOUT creating any DB rows.

        Counts validated grade_entries for the given context.  This method
        does NOT persist anything — it is safe to call multiple times.

        Returns a dict with:
            total_recipients (int)
            teaching_assignment_id (int)
            class_group_id (int | None)
            existing_current_snapshots (int)  — students already published
        """
        from backend.app.models.academic import GRADE_STATUS_VALIDATED, GradeEntry

        stmt = select(func.count(GradeEntry.id)).where(
            GradeEntry.teaching_assignment_id == teaching_assignment_id,
            GradeEntry.status == GRADE_STATUS_VALIDATED,
        )
        total_recipients = session.execute(stmt).scalar() or 0

        existing_stmt = select(func.count(PublicationSnapshot.id)).where(
            PublicationSnapshot.teaching_assignment_id == teaching_assignment_id,
            PublicationSnapshot.is_current.is_(True),
        )
        existing_current = session.execute(existing_stmt).scalar() or 0

        return {
            "total_recipients": total_recipients,
            "teaching_assignment_id": teaching_assignment_id,
            "class_group_id": class_group_id,
            "existing_current_snapshots": existing_current,
        }

    # ------------------------------------------------------------------
    # 6. Re-publication (task 7)
    # ------------------------------------------------------------------

    def republish(
        self,
        session: Session,
        teaching_assignment_id: int,
        actor_user_id: int,
        grade_data: list[dict[str, Any]],
        channels: list[str],
        *,
        class_group_id: int | None = None,
        request_id: str | None = None,
    ) -> BroadcastJob:
        """Re-publish grades after changes (AC-4).

        Creates a new BroadcastJob and new snapshot versions.  Previous
        is_current=True snapshots are superseded by the new versions —
        they remain in the database for the audit trail.

        Parameters
        ----------
        session:
            Active SQLAlchemy session.
        teaching_assignment_id:
            The teaching assignment being re-published.
        actor_user_id:
            The professor initiating the re-publication.
        grade_data:
            Same format as ``create_publication_snapshots``.
        channels:
            Broadcast channels.
        class_group_id:
            Optional class group scope.
        request_id:
            Optional correlation ID for audit logging.

        Returns
        -------
        BroadcastJob
            The new BroadcastJob created for this re-publication.
        """
        job = self.create_broadcast_job(
            session,
            teaching_assignment_id=teaching_assignment_id,
            actor_user_id=actor_user_id,
            job_type="grade_publication",
            channels=channels,
            class_group_id=class_group_id,
        )
        self.create_publication_snapshots(session, job, grade_data, request_id=request_id)
        return job

    # ------------------------------------------------------------------
    # 7. Audit event recorder (task 8)
    # ------------------------------------------------------------------

    def record_audit_event(
        self,
        session: Session,
        actor_user_id: int | None,
        action: str,
        entity_type: str,
        entity_id: str | None,
        *,
        request_id: str | None = None,
        before_json: str | None = None,
        after_json: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Append an entry to the audit_log table.

        Used for: publication_start, publication_confirmed, snapshot_created,
        delivery_completed, delivery_failed.

        Parameters
        ----------
        session:
            Active SQLAlchemy session.
        actor_user_id:
            User who triggered the action (None for system events).
        action:
            Event label, e.g. ``"publication_start"``.
        entity_type:
            Type of entity affected, e.g. ``"broadcast_job"``.
        entity_id:
            String ID of the affected entity.
        request_id:
            Optional HTTP request correlation ID.
        before_json:
            JSON string of state before the change (optional).
        after_json:
            JSON string of state after the change (optional).
        reason:
            Human-readable summary (optional).
        """
        entry = AuditLog(
            actor_user_id=actor_user_id,
            request_id=request_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_json=before_json,
            after_json=after_json,
            reason=reason,
        )
        session.add(entry)
        session.flush()
