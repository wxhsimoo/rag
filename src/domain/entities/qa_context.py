from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

@dataclass
class Message:
    """对话消息"""
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建消息"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.now().isoformat())),
            metadata=data.get("metadata", {})
        )

@dataclass
class UserProfile:
    """用户档案"""
    user_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """从字典创建用户档案"""
        return cls(
            user_id=data["user_id"],
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now().isoformat()))
        )

@dataclass
class ConversationSession:
    """对话会话"""
    session_id: str
    user_profile: UserProfile
    messages: List[Message] = field(default_factory=list)
    context_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: MessageRole, content: str, metadata: Dict[str, Any] = None) -> None:
        """添加消息
        
        Args:
            role: 消息角色
            content: 消息内容
            metadata: 消息元数据
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.last_activity = datetime.now()
        
        # 保持消息历史在合理范围内
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """获取最近的消息
        
        Args:
            count: 消息数量
            
        Returns:
            最近的消息列表
        """
        return self.messages[-count:] if count > 0 else self.messages
    
    def get_conversation_history(self, include_system: bool = False) -> List[Dict[str, str]]:
        """获取对话历史（适用于LLM API格式）
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            对话历史列表
        """
        history = []
        for message in self.messages:
            if not include_system and message.role == MessageRole.SYSTEM:
                continue
            history.append({
                "role": message.role.value,
                "content": message.content
            })
        return history
    
    def update_context(self, key: str, value: Any) -> None:
        """更新上下文数据
        
        Args:
            key: 键名
            value: 值
        """
        self.context_data[key] = value
        self.last_activity = datetime.now()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据
        
        Args:
            key: 键名
            default: 默认值
            
        Returns:
            上下文值
        """
        return self.context_data.get(key, default)
    
    def extract_user_intent(self) -> Dict[str, Any]:
        """提取用户意图
        
        Returns:
            用户意图信息
        """
        if not self.messages:
            return {}
        
        # 获取最后一条用户消息
        last_user_message = None
        for message in reversed(self.messages):
            if message.role == MessageRole.USER:
                last_user_message = message
                break
        
        if not last_user_message:
            return {}
        
        intent = {
            "query": last_user_message.content,
            "timestamp": last_user_message.timestamp,
            "extracted_info": {}
        }
        
        return intent
    
    def is_active(self, timeout_minutes: int = 30) -> bool:
        """检查会话是否活跃
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            是否活跃
        """
        now = datetime.now()
        time_diff = now - self.last_activity
        return time_diff.total_seconds() < timeout_minutes * 60
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "user_profile": self.user_profile.to_dict(),
            "messages": [msg.to_dict() for msg in self.messages],
            "context_data": self.context_data,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """从字典创建对话会话"""
        return cls(
            session_id=data["session_id"],
            user_profile=UserProfile.from_dict(data["user_profile"]),
            messages=[Message.from_dict(msg) for msg in data.get("messages", [])],
            context_data=data.get("context_data", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now().isoformat())),
            last_activity=datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat()))
        )

class QAContext:
    """问答上下文管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationSession] = {}
    
    def create_session(self, session_id: str, user_id: str) -> ConversationSession:
        """创建新会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            新创建的会话
        """
        user_profile = UserProfile(user_id=user_id)
        session = ConversationSession(
            session_id=session_id,
            user_profile=user_profile
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，如果不存在则返回None
        """
        return self.sessions.get(session_id)
    
    def get_or_create_session(self, session_id: str, user_id: str) -> ConversationSession:
        """获取或创建会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            会话对象
        """
        session = self.get_session(session_id)
        if session is None:
            session = self.create_session(session_id, user_id)
        return session
    
    def cleanup_inactive_sessions(self, timeout_minutes: int = 30) -> int:
        """清理不活跃的会话
        
        Args:
            timeout_minutes: 超时时间（分钟）
            
        Returns:
            清理的会话数量
        """
        inactive_sessions = []
        for session_id, session in self.sessions.items():
            if not session.is_active(timeout_minutes):
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del self.sessions[session_id]
        
        return len(inactive_sessions)
    
    def get_active_sessions_count(self) -> int:
        """获取活跃会话数量
        
        Returns:
            活跃会话数量
        """
        return len([s for s in self.sessions.values() if s.is_active()])
    
    def add_message(self, session_id: str, role: MessageRole, content: str, 
                   user_profile: Optional[UserProfile] = None, 
                   metadata: Dict[str, Any] = None) -> None:
        """向会话添加消息
        
        Args:
            session_id: 会话ID
            role: 消息角色
            content: 消息内容
            user_profile: 用户档案（用于创建会话）
            metadata: 消息元数据
        """
        # 获取或创建会话
        session = self.get_session(session_id)
        if session is None:
            if user_profile:
                session = ConversationSession(
                    session_id=session_id,
                    user_profile=user_profile
                )
                self.sessions[session_id] = session
            else:
                # 如果没有用户档案，创建一个默认的
                default_profile = UserProfile(user_id=f"user_{session_id}")
                session = ConversationSession(
                    session_id=session_id,
                    user_profile=default_profile
                )
                self.sessions[session_id] = session
        
        # 添加消息到会话
        session.add_message(role, content, metadata)
    
    def get_conversation_history(self, session_id: str, limit: int = 10) -> List[Message]:
        """获取会话的对话历史
        
        Args:
            session_id: 会话ID
            limit: 返回的消息数量限制
            
        Returns:
            消息列表
        """
        session = self.get_session(session_id)
        if session is None:
            return []
        
        return session.get_recent_messages(limit)
    
    def clear_session(self, session_id: str) -> bool:
        """清除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功清除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False