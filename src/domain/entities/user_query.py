from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class UserQuery:
    """用户查询实体

    用于在领域层记录和分析用户查询的关键数据点。
    """

    # 原始问题
    question: str

    # 归一化/增强后的问题（如果有）
    normalized_question: Optional[str] = None

    # 会话与用户信息
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    # 查询参数
    top_k: int = 5

    # 额外元数据（如语言、渠道、客户端等）
    metadata: Optional[Dict[str, Any]] = None

    # 时间戳
    created_at: Optional[datetime] = None

    # RAG 结果快照（来自 rag_pipeline_service 结果字典，去除循环引用）
    result_snapshot: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "normalized_question": self.normalized_question,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "top_k": self.top_k,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "result_snapshot": self.result_snapshot,
        }

    # ===== 与 QAContext 逻辑一致的内存会话管理（保存：原始问题 + RAG结果快照） =====
    def _filter_result_for_snapshot(self, result: Dict[str, Any]) -> Dict[str, Any]:
        # 复制并移除可能引起循环引用的字段（如 user_query）
        snap = dict(result or {})
        if "user_query" in snap:
            try:
                # 保留 user_query 的浅要点，避免递归
                uq = snap["user_query"]
                snap["user_query"] = {
                    "question": uq.get("question"),
                    "normalized_question": uq.get("normalized_question"),
                    "session_id": uq.get("session_id"),
                    "user_id": uq.get("user_id")
                }
            except Exception:
                # 如果结构异常，直接移除
                snap.pop("user_query", None)
        return snap

    def save(self, result: Optional[Dict[str, Any]] = None) -> None:
        # 统一入口：保存到当前会话（或 default）并维护活跃与修剪
        if result is not None:
            self.result_snapshot = self._filter_result_for_snapshot(result)
        self.save_in_session(self.session_id or "default", self.result_snapshot, self.user_id)

    def store_in_memory(self) -> None:
        # 兼容旧方法：无结果时也可保存，仅记录问题与元数据
        self.save(None)

    def store_in_memory_session(self, session_id, user_id=None) -> None:
        # 兼容旧方法：显式会话保存，无结果
        self.save_in_session(session_id, None, user_id)

    def save_with_result_session(self, session_id: str, result: Dict[str, Any], user_id: Optional[str] = None) -> None:
        # 新方法：显式会话保存并带结果
        self.result_snapshot = self._filter_result_for_snapshot(result)
        self.save_in_session(session_id, self.result_snapshot, user_id)

    def save_in_session(self, session_id: str, result_snapshot: Optional[Dict[str, Any]], user_id: Optional[str]) -> None:
        from datetime import datetime
        cls = self.__class__
        if not hasattr(cls, "_sessions"):
            cls._sessions = {}
        session = cls._sessions.get(session_id)
        now = datetime.now()
        if session is None:
            session = {
                "user_id": user_id or getattr(self, "user_id", None) or f"user_{session_id}",
                "queries": [],
                "context_data": {},
                "created_at": now,
                "last_activity": now,
            }
            cls._sessions[session_id] = session
        # 记录条目：原始问题 + 结果快照 + 元数据
        entry = {
            "question": self.question,
            "result": result_snapshot,
            "metadata": self.metadata,
            "created_at": now
        }
        session["queries"].append(entry)
        session["last_activity"] = now
        if len(session["queries"]) > 50:
            session["queries"] = session["queries"][-50:]

    @classmethod
    def get_recent_queries(cls, session_id, limit=10):
        sessions = getattr(cls, "_sessions", {})
        session = sessions.get(session_id)
        if not session:
            return []
        records = session["queries"]
        return records[-limit:] if limit > 0 else records

    @classmethod
    def clear_session(cls, session_id) -> bool:
        sessions = getattr(cls, "_sessions", {})
        if session_id in sessions:
            del sessions[session_id]
            return True
        return False

    @classmethod
    def get_active_sessions_count(cls, timeout_minutes=30) -> int:
        from datetime import datetime
        sessions = getattr(cls, "_sessions", {})
        now = datetime.now()
        def is_active(session):
            diff = now - session.get("last_activity", now)
            return diff.total_seconds() < timeout_minutes * 60
        return len([s for s in sessions.values() if is_active(s)])

    @classmethod
    def cleanup_inactive_sessions(cls, timeout_minutes=30) -> int:
        from datetime import datetime
        sessions = getattr(cls, "_sessions", {})
        now = datetime.now()
        inactive = []
        for sid, session in sessions.items():
            diff = now - session.get("last_activity", now)
            if diff.total_seconds() >= timeout_minutes * 60:
                inactive.append(sid)
        for sid in inactive:
            del sessions[sid]
        return len(inactive)
