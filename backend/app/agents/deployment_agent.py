import uuid
from typing import Optional, Dict
from backend.app.core.audit import log_audit_event
from backend.app.core.config import settings


class DeploymentAgent:
    """
    Deployment Agent — uploads artifacts to AWS S3.
    Fails gracefully if AWS not configured.
    """

    async def deploy(
        self,
        task: str,
        code: str,
        documentation: str,
        tests: str,
        review: str,
        user: str,
        pipeline_state_id: str,
    ) -> Dict:
        task_id = str(uuid.uuid4())[:8]

        log_audit_event(
            action="deployment:start", user=user,
            resource=f"deployment/{task_id}",
            detail=f"task={task[:100]}",
        )

        artifacts = {}

        try:
            from backend.app.services.aws_s3 import upload_artifact

            artifacts["code"] = upload_artifact(
                content=code, artifact_type="code",
                task_id=task_id, metadata={"task": task[:100], "user": user},
            )
            artifacts["documentation"] = upload_artifact(
                content=documentation, artifact_type="documentation",
                task_id=task_id, metadata={"task": task[:100]},
            )
            artifacts["tests"] = upload_artifact(
                content=tests, artifact_type="tests",
                task_id=task_id, metadata={"task": task[:100]},
            )
            artifacts["review"] = upload_artifact(
                content=review, artifact_type="review",
                task_id=task_id, metadata={"task": task[:100]},
            )

            log_audit_event(
                action="deployment:success", user=user,
                resource=f"deployment/{task_id}",
                detail=f"artifacts={len(artifacts)}",
            )

            return {
                "status": "success",
                "task_id": task_id,
                "artifacts": artifacts,
                "message": f"Deployed {len(artifacts)} artifacts to S3",
            }

        except Exception as e:
            log_audit_event(
                action="deployment:failed", user=user,
                resource=f"deployment/{task_id}",
                status="error", detail=str(e),
            )
            return {
                "status": "partial",
                "task_id": task_id,
                "artifacts": artifacts,
                "error": str(e),
                "message": "Deployment completed with errors — check AWS config",
            }