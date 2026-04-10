from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List, Optional
import os
import json
import logging

logger = logging.getLogger(__name__)


class MockInterviewAgent:
    MODES = {
        "behavioral": {
            "name": "行为面试",
            "description": "基于STAR法则的行为面试题",
            "system_prompt": """你是资深HR面试官，专注于行为面试。
使用STAR法则（情境、任务、行动、结果）评估候选人。
每次只问一个问题，等待回答后追问细节。
关注候选人的沟通能力、团队协作、问题解决能力。"""
        },
        "system_design": {
            "name": "系统设计",
            "description": "分布式系统架构设计",
            "system_prompt": """你是首席架构师，进行系统设计面试。
关注可扩展性、可靠性、性能优化、安全性。
引导候选人分析需求、画出架构图、解释设计决策。
讨论技术选型权衡和边界情况。"""
        },
        "algorithm": {
            "name": "算法题",
            "description": "LeetCode风格算法题",
            "system_prompt": """你是算法面试官，提供编程挑战。
关注时间复杂度、空间复杂度、边界条件、代码规范。
鼓励候选人先讲思路再写代码。
提示测试用例和最优解法。"""
        },
        "pressure": {
            "name": "压力面试",
            "description": "快速问答测试抗压能力",
            "system_prompt": """你是严厉的面试官，进行压力面试。
问题节奏快，会质疑候选人的答案。
测试候选人在压力下的表现和应变能力。
保持专业但具有挑战性。"""
        }
    }

    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")

        self.llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0.7,
            max_tokens=1000,
            openai_api_key=api_key,
            openai_api_base=api_base
        )

        self.conversation_history = {}

    def initialize_conversation(self, session_id: str, mode: str, context: Dict):
        mode_config = self.MODES.get(mode, self.MODES["behavioral"])

        self.conversation_history[session_id] = {
            "mode": mode,
            "context": context,
            "messages": [],
            "system_prompt": mode_config["system_prompt"]
        }

        initial_question = self.generate_initial_question(mode, context)
        self.conversation_history[session_id]["messages"].append({
            "role": "assistant",
            "content": initial_question
        })

        return initial_question

    def generate_initial_question(self, mode: str, context: Dict) -> str:
        mode_config = self.MODES.get(mode, self.MODES["behavioral"])

        prompt = ChatPromptTemplate.from_messages([
            ("system", mode_config["system_prompt"]),
            ("human", """生成{mode}面试的第一个问题：

背景信息：
- 技术栈：{language}
- 经验级别：{experience_level}
- 目标岗位：{target_role}

请直接返回问题内容，不要包含JSON或其他格式。""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "mode": mode_config["name"],
            "language": context.get("language", "通用"),
            "experience_level": context.get("experience_level", "中级"),
            "target_role": context.get("target_role", "软件工程师")
        })

        return response.content

    async def process_answer_stream(self, session_id: str, user_answer: str):
        if session_id not in self.conversation_history:
            raise ValueError("会话不存在")

        conversation = self.conversation_history[session_id]
        mode = conversation["mode"]
        messages = conversation["messages"]

        messages.append({"role": "user", "content": user_answer})

        history_text = "\n".join([
            f"{'面试官' if m['role'] == 'assistant' else '候选人'}: {m['content']}"
            for m in messages[-6:]
        ])

        mode_config = self.MODES.get(mode, self.MODES["behavioral"])

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""{mode_config['system_prompt']}

当前是对话的一部分，请根据候选人的回答：
1. 给出简短评价（50字以内）
2. 提出下一个问题或追问

保持对话连贯性。"""),
            ("human", """对话历史：
{history}

候选人最新回答：{answer}

请返回JSON格式：
{{
  "evaluation": "简短评价",
  "score": 75,
  "next_question": "下一个问题",
  "continue_interview": true
}}""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({
            "history": history_text,
            "answer": user_answer
        })

        try:
            content = response.content
            if "json" in content:
                content = content.split("```")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content)

            if not isinstance(result, dict):
                raise ValueError("Response is not a dictionary")

            if "next_question" not in result:
                result["next_question"] = response.content[:200]

            if "evaluation" not in result:
                result["evaluation"] = "回答已收到"

            if "score" not in result or not isinstance(result["score"], (int, float)):
                result["score"] = 70

            if "continue_interview" not in result:
                result["continue_interview"] = True

        except Exception as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            result = {
                "evaluation": "回答已收到",
                "score": 70,
                "next_question": response.content[:200] if len(response.content) > 200 else response.content,
                "continue_interview": True
            }

        messages.append({
            "role": "assistant",
            "content": result["next_question"]
        })

        return result

    def end_conversation(self, session_id: str) -> Dict:
        if session_id not in self.conversation_history:
            raise ValueError("会话不存在")

        conversation = self.conversation_history[session_id]
        messages = conversation["messages"]

        scores = []
        for msg in messages:
            if msg.get("score"):
                scores.append(msg["score"])

        avg_score = sum(scores) / len(scores) if scores else 0

        summary_prompt = ChatPromptTemplate.from_messages([
            ("system", "你是面试评估专家。根据整个对话历史，给出综合评估。"),
            ("human", """对话历史：
        {history}

        请返回JSON格式的综合评估：
        {{
          "overall_score": 85,
          "summary": "总体评价",
          "strengths": ["优点1", "优点2"],
          "weaknesses": ["不足1", "不足2"],
          "recommendations": ["建议1", "建议2"]
        }}""")
        ])

        history_text = "\n".join([
            f"{'面试官' if m['role'] == 'assistant' else '候选人'}: {m['content']}"
            for m in messages
        ])

        chain = summary_prompt | self.llm
        response = chain.invoke({"history": history_text})

        try:
            content = response.content
            if "json" in content:
                content = content.split("```")[1].split("```")[0]
            summary = json.loads(content.strip())
        except:
            summary = {"overall_score": avg_score, "summary": response.content[:300], "strengths": ["完成了面试"],
                       "weaknesses": ["需要改进"], "recommendations": ["继续练习"]}
        del self.conversation_history[session_id]

        return summary

    def get_conversation_state(self, session_id: str) -> Dict:
        if session_id not in self.conversation_history:
            raise ValueError("会话不存在")

        conversation = self.conversation_history[session_id]
        return {
            "mode": conversation["mode"],
            "message_count": len(conversation["messages"]),
            "last_message": conversation["messages"][-1] if conversation["messages"] else None
        }

mock_interview_agent = MockInterviewAgent()


