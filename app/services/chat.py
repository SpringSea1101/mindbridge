from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.agents.harness import MindBridgeAgentHarness
from app.core.config import Settings
from app.models.entities import UserAccount
from app.schemas.dtos import ChatRequest, ChatStreamEvent
from app.services.ai import AiClient


logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        # self.ai：负责按配置调用真实模型或 Mock。
        self.ai = AiClient(settings)
        # self.agent_harness：负责组织一轮 Agent 处理以及相关数据保存；管理会话、消息和工具调用。
        self.agent_harness = MindBridgeAgentHarness(db, settings)

    async def stream_chat(self, user: UserAccount, request: ChatRequest):
        # 1. 准备本轮结果，包括用于生成回复的 messages
        # Harness 组织 Agent 处理，得到意图、风险、按需检索的知识等，并准备好接下来交给模型的消息列表。
        outcome = self.agent_harness.run(user, request)
        # 2. 告诉浏览器本轮属于哪个聊天会话
        # yield： 区别于return，可以在一个函数中多次返回值，适合流式输出。
        yield sse("meta", ChatStreamEvent(type="meta", sessionId=outcome.session.public_id).model_dump(by_alias=True))
        assistant = []
        # 3. AiClient 接收这个消息列表，才开始生成面向学生的回答。
        async for token in self.ai.stream(outcome.response_messages):
            assistant.append(token)
            yield sse("token", ChatStreamEvent(type="token", sessionId=outcome.session.public_id, content=token).model_dump())
        if assistant:
            self.agent_harness.save_assistant_message(
                user, outcome.session, "".join(assistant))
        try:
            await self.agent_harness.dispatch_tools(outcome.tool_plan)
        except Exception as exc:
            logger.warning(
                "Post-response tool dispatch failed for session=%s report_id=%s: %s",
                outcome.session.public_id,
                outcome.report_id,
                exc,
                exc_info=True,
            )
        yield sse("done", ChatStreamEvent(type="done", sessionId=outcome.session.public_id).model_dump())


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"
