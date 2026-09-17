"""
Enhanced Human Approval System
Tracks, evaluates, and manages approval-requiring decisions
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ApprovalLevel(Enum):
    """Risk/approval levels for decisions"""
    LOW = "low"           # No approval needed (informational)
    MEDIUM = "medium"     # Should get human input (analysis)
    HIGH = "high"         # Must get approval (recommendations)
    CRITICAL = "critical" # Must get manager approval (investments)


class ApprovalStatus(Enum):
    """Status of an approval request"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class ApprovalRequest:
    """Represents a request that needs human approval"""

    def __init__(self,
                 question: str,
                 response: str,
                 level: ApprovalLevel,
                 agent_used: str,
                 confidence: float,
                 risk_factors: List[str]):
        self.id = self._generate_id()
        self.question = question
        self.response = response
        self.level = level
        self.agent_used = agent_used
        self.confidence = confidence
        self.risk_factors = risk_factors
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now().isoformat()
        self.reviewed_at = None
        self.reviewed_by = None
        self.reviewer_notes = None

    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())[:8]

    def approve(self, reviewer: str, notes: str = ""):
        """Mark as approved"""
        self.status = ApprovalStatus.APPROVED
        self.reviewed_at = datetime.now().isoformat()
        self.reviewed_by = reviewer
        self.reviewer_notes = notes
        logger.info(f"Approval {self.id} APPROVED by {reviewer}")

    def reject(self, reviewer: str, notes: str = ""):
        """Mark as rejected"""
        self.status = ApprovalStatus.REJECTED
        self.reviewed_at = datetime.now().isoformat()
        self.reviewed_by = reviewer
        self.reviewer_notes = notes
        logger.warning(f"Approval {self.id} REJECTED by {reviewer}")

    def escalate(self, reviewer: str, reason: str = ""):
        """Escalate to manager"""
        self.status = ApprovalStatus.ESCALATED
        self.reviewed_at = datetime.now().isoformat()
        self.reviewed_by = reviewer
        self.reviewer_notes = f"Escalated: {reason}"
        logger.warning(f"Approval {self.id} ESCALATED by {reviewer}")

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "question": self.question,
            "response": self.response,
            "level": self.level.value,
            "agent": self.agent_used,
            "confidence": self.confidence,
            "risk_factors": self.risk_factors,
            "status": self.status.value,
            "created_at": self.created_at,
            "reviewed_at": self.reviewed_at,
            "reviewed_by": self.reviewed_by,
            "notes": self.reviewer_notes,
        }


class ApprovalManager:
    """Manages approval requests and tracking"""

    def __init__(self, storage_dir: str = ".approvals"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.requests: Dict[str, ApprovalRequest] = {}
        self._load_requests()

    def _load_requests(self):
        """Load existing approval requests"""
        try:
            for file in self.storage_dir.glob("*.json"):
                with open(file, "r") as f:
                    data = json.load(f)
                    request = ApprovalRequest(
                        question=data["question"],
                        response=data["response"],
                        level=ApprovalLevel(data["level"]),
                        agent_used=data["agent"],
                        confidence=data["confidence"],
                        risk_factors=data["risk_factors"],
                    )
                    request.id = data["id"]
                    request.status = ApprovalStatus(data["status"])
                    request.created_at = data["created_at"]
                    request.reviewed_at = data.get("reviewed_at")
                    request.reviewed_by = data.get("reviewed_by")
                    request.reviewer_notes = data.get("notes")
                    self.requests[request.id] = request
        except Exception as e:
            logger.warning(f"Could not load approval requests: {e}")

    def _save_request(self, request: ApprovalRequest):
        """Save request to disk"""
        try:
            file_path = self.storage_dir / f"{request.id}.json"
            with open(file_path, "w") as f:
                json.dump(request.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Could not save approval request: {e}")

    def create_request(self,
                      question: str,
                      response: str,
                      agent_used: str,
                      confidence: float = 0.7,
                      risk_factors: List[str] = None) -> ApprovalRequest:
        """
        Create a new approval request.

        Args:
            question: The user's question
            response: The AI's response
            agent_used: Which agent generated the response
            confidence: Confidence score (0-1)
            risk_factors: List of identified risk factors

        Returns:
            The created ApprovalRequest
        """
        if risk_factors is None:
            risk_factors = []

        # Determine approval level based on risk factors and confidence
        level = self._determine_level(confidence, len(risk_factors))

        request = ApprovalRequest(
            question=question,
            response=response,
            level=level,
            agent_used=agent_used,
            confidence=confidence,
            risk_factors=risk_factors,
        )

        self.requests[request.id] = request
        self._save_request(request)

        logger.info(f"Created approval request {request.id} (level: {level.value})")
        return request

    def _determine_level(self, confidence: float, risk_count: int) -> ApprovalLevel:
        """Determine approval level based on factors"""
        if confidence < 0.5 or risk_count >= 5:
            return ApprovalLevel.CRITICAL
        elif confidence < 0.7 or risk_count >= 3:
            return ApprovalLevel.HIGH
        elif risk_count >= 1:
            return ApprovalLevel.MEDIUM
        else:
            return ApprovalLevel.LOW

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Get a specific approval request"""
        return self.requests.get(request_id)

    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return [r for r in self.requests.values()
                if r.status == ApprovalStatus.PENDING]

    def get_requests_by_level(self, level: ApprovalLevel) -> List[ApprovalRequest]:
        """Get requests by approval level"""
        return [r for r in self.requests.values() if r.level == level]

    def get_statistics(self) -> Dict:
        """Get approval statistics"""
        total = len(self.requests)
        pending = len(self.get_pending_requests())
        approved = len([r for r in self.requests.values()
                       if r.status == ApprovalStatus.APPROVED])
        rejected = len([r for r in self.requests.values()
                       if r.status == ApprovalStatus.REJECTED])
        escalated = len([r for r in self.requests.values()
                        if r.status == ApprovalStatus.ESCALATED])

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "escalated": escalated,
            "approval_rate": round((approved / total * 100), 1) if total > 0 else 0,
        }


# Global instance
_manager = None


def get_approval_manager() -> ApprovalManager:
    """Get or create global approval manager"""
    global _manager
    if _manager is None:
        _manager = ApprovalManager()
    return _manager


def create_approval_request(question: str,
                          response: str,
                          agent: str,
                          confidence: float = 0.7,
                          risk_factors: List[str] = None) -> ApprovalRequest:
    """Create an approval request"""
    return get_approval_manager().create_request(
        question=question,
        response=response,
        agent_used=agent,
        confidence=confidence,
        risk_factors=risk_factors or [],
    )


def get_pending_approvals() -> List[ApprovalRequest]:
    """Get all pending approvals"""
    return get_approval_manager().get_pending_requests()


def approve_request(request_id: str, reviewer: str, notes: str = ""):
    """Approve a request"""
    manager = get_approval_manager()
    request = manager.get_request(request_id)
    if request:
        request.approve(reviewer, notes)
        manager._save_request(request)


def reject_request(request_id: str, reviewer: str, notes: str = ""):
    """Reject a request"""
    manager = get_approval_manager()
    request = manager.get_request(request_id)
    if request:
        request.reject(reviewer, notes)
        manager._save_request(request)


def get_stats() -> Dict:
    """Get approval statistics"""
    return get_approval_manager().get_statistics()
