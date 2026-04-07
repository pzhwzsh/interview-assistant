import hashlib
import random
from typing import Dict
from datetime import datetime


class PromptEntropyEngine:
    def __init__(self):
        self.used_hashes = set()
        self.entropy_templates = [
            "从{angle}角度分析这个问题",
            "结合实际场景，{scenario}情况下如何处理",
            "对比{method_a}和{method_b}的优劣",
            "请解释{concept}在{context}中的应用",
            "如果{condition}发生变化，结果会如何"
        ]

    def generate_entropy_seed(self, language: str, project: str,
                              difficulty: str, user_id: str) -> str:
        timestamp = datetime.now().isoformat()
        random_factor = random.random()
        raw_input = f"{language}_{project}_{difficulty}_{user_id}_{timestamp}_{random_factor}"
        return hashlib.sha256(raw_input.encode()).hexdigest()[:16]

    def check_uniqueness(self, question_hash: str) -> bool:
        if question_hash in self.used_hashes:
            return False
        self.used_hashes.add(question_hash)
        return True

    def add_entropy_modifier(self, base_prompt: str, context: Dict) -> str:
        template = random.choice(self.entropy_templates)
        modifiers = {
            'angle': random.choice(['理论', '实践', '性能', '安全', '可维护性']),
            'scenario': random.choice(['高并发', '分布式', '微服务', '云原生']),
            'method_a': random.choice(['方案A', '传统方法', '同步方式']),
            'method_b': random.choice(['方案B', '现代方法', '异步方式']),
            'concept': random.choice(['核心概念', '关键机制', '底层原理']),
            'context': random.choice(['实际项目', '生产环境', '大规模系统']),
            'condition': random.choice(['需求', '约束条件', '资源限制'])
        }
        entropy_text = template.format(**modifiers)
        return f"{base_prompt}\n\n熵值增强要求：{entropy_text}"

    def clear_old_hashes(self, max_size: int = 1000):
        if len(self.used_hashes) > max_size:
            self.used_hashes = set(list(self.used_hashes)[-max_size // 2:])


entropy_engine = PromptEntropyEngine()
