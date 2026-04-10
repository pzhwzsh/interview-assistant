from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Optional
import hashlib
import os
from app.utils.prompt_entropy import entropy_engine
from app.models.schemas import QuestionRequest, QuestionResponse
from app.utils.metrics import monitor_performance, metrics
import time
import logging

logger = logging.getLogger(__name__)

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

        # 内存缓存配置
        self._cache = {}
        self._cache_ttl = 300
        self._cache_timestamps = {}

    def _get_cache_key(self, request: QuestionRequest) -> str:
        topic = request.topic_focus or "无特定要求"
        return f"{request.language.value}_{request.project_type.value}_{request.difficulty.value}_{topic}"

    def _get_from_cache(self, cache_key: str) -> Optional[QuestionResponse]:
        if cache_key in self._cache:
            timestamp = self._cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < self._cache_ttl:
                logger.info(f"[CACHE] Hit for key: {cache_key}")
                cached_question = self._cache[cache_key]
                cached_question.question_id = self._generate_unique_id_from_cache(cache_key, cached_question.question)
                return cached_question
            else:
                logger.info(f"[CACHE] Expired for key: {cache_key}")
                del self._cache[cache_key]
                del self._cache_timestamps[cache_key]
        return None

    def _save_to_cache(self, cache_key: str, question: QuestionResponse):
        self._cache[cache_key] = question
        self._cache_timestamps[cache_key] = time.time()
        logger.info(f"[CACHE] Saved for key: {cache_key}, TTL: {self._cache_ttl}s")

    def _generate_unique_id_from_cache(self, cache_key: str, question: str) -> str:
        raw_id = f"{cache_key}_{question[:50]}_{int(time.time())}"
        question_hash = hashlib.md5(raw_id.encode()).hexdigest()[:12]
        return f"q_{question_hash}"

    def generate_question(self, request: QuestionRequest) -> QuestionResponse:
        cache_key = self._get_cache_key(request)

        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
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

            logger.info(f"Raw LLM response: {response.content[:200]}...")

            question_data = self._parse_response(response.content)

            if not question_data.get('question'):
                raise ValueError("Failed to extract valid question from LLM response")

            question_id = self._generate_unique_id(request, question_data['question'])

            question_response = QuestionResponse(
                question_id=question_id,
                question=question_data['question'],
                difficulty=request.difficulty,
                hints=question_data.get('hints', []),
                expected_topics=question_data.get('expected_topics', []),
                estimated_time_minutes=question_data.get('estimated_time_minutes', 15)
            )

            self._save_to_cache(cache_key, question_response)

            return question_response
        except Exception as e:
            logger.error(f"Question generation failed: {str(e)}", exc_info=True)
            raise

    def _parse_response(self, content: str) -> Dict:
        import json
        import re

        try:
            cleaned_content = content.strip()

            # 提取 JSON 内容
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            cleaned_content = content.strip()
            data = json.loads(cleaned_content)

            # 验证必需字段
            required_fields = ['question', 'hints', 'expected_topics']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")

            return data

        except (json.JSONDecodeError, IndexError, AttributeError, ValueError) as e:
            logger.warning(f"JSON parsing failed: {str(e)}. Content: {content[:300]}")

            # 尝试用正则提取 JSON
            json_pattern = r'\{[^{}]*"question"[^{}]*\}'
            match = re.search(json_pattern, content, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                    return data
                except:
                    pass

            raise Exception(f"题目生成失败：AI响应格式异常。请稍后重试或联系管理员。")
    def _generate_unique_id(self, request: QuestionRequest, question: str) -> str:
        raw_id = f"{request.language}_{request.project_type}_{question[:50]}"
        question_hash = hashlib.md5(raw_id.encode()).hexdigest()[:12]
        return f"q_{question_hash}"