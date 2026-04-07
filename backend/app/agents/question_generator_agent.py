from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict
import hashlib
import os
from app.utils.prompt_entropy import entropy_engine
from app.models.schemas import QuestionRequest, QuestionResponse
from app.utils.metrics import monitor_performance, metrics


class QuestionGeneratorAgent:
    def __init__(self):
        api_key = os.getenv("DEEPSEEK_API_KEY")
        api_base = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1")

        self.llm = ChatOpenAI(
            model="deepseek-chat",
            temperature=0.8,
            max_tokens=1500,
            openai_api_key=api_key,
            openai_api_base=api_base
        )

        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的技术面试官。

要求：
1. 题目要具体、有深度
2. 结合指定的编程语言和项目类型
3. 难度要符合要求
4. 提供3个渐进式提示
5. 列出期望考察的知识点
6. **必须只返回纯JSON格式，不要包含任何markdown代码块标记(如)**

{entropy_instruction}"""),
            ("human", """生成面试题目：

编程语言：{language}
项目类型：{project_type}
难度级别：{difficulty}
重点关注：{topic_focus}

**严格以以下JSON格式返回（不要添加任何其他文字）：**
{{
  "question": "题目内容字符串",
  "hints": ["提示1", "提示2", "提示3"],
  "expected_topics": ["知识点1", "知识点2"],
  "estimated_time_minutes": 15
}}""")
        ])
    def generate_question(self, request: QuestionRequest) -> QuestionResponse:
        entropy_seed = entropy_engine.generate_entropy_seed(
            request.language.value,
            request.project_type.value,
            request.difficulty.value,
            request.user_id
        )

        entropy_instruction = entropy_engine.add_entropy_modifier(
            "确保题目的独特性和多样性",
            {"seed": entropy_seed}
        )

        chain = self.prompt_template | self.llm

        response = chain.invoke({
            "language": request.language.value,
            "project_type": request.project_type.value,
            "difficulty": request.difficulty.value,
            "topic_focus": request.topic_focus or "无特定要求",
            "entropy_instruction": entropy_instruction
        })

        question_data = self._parse_response(response.content)
        question_id = self._generate_unique_id(request, question_data['question'])

        return QuestionResponse(
            question_id=question_id,
            question=question_data['question'],
            difficulty=request.difficulty,
            hints=question_data.get('hints', []),
            expected_topics=question_data.get('expected_topics', []),
            estimated_time_minutes=question_data.get('estimated_time_minutes', 15)
        )

    def _parse_response(self, content: str) -> Dict:
        import json
        try:
            if "json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except (json.JSONDecodeError, IndexError, AttributeError):
            return {
                "question": content,
                "hints": ["思考核心要点", "结合实际经验", "考虑边界情况"],
                "expected_topics": ["基础知识"],
                "estimated_time_minutes": 15
            }

    def _generate_unique_id(self, request: QuestionRequest, question: str) -> str:
        raw_id = f"{request.language}_{request.project_type}_{question[:50]}"
        question_hash = hashlib.md5(raw_id.encode()).hexdigest()[:12]
        return f"q_{question_hash}"