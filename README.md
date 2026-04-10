# 🚀 AI Interview Assistant (智能面试助手)

基于 FastAPI + Vue3 + LangChain 全栈架构开发的 AI 模拟面试系统。通过多 Agent 协同工作流，实现从“智能出题”到“多维评估”再到“难度自适应”的自动化闭环。

**在线演示 | [GitHub 仓库](https://github.com/your-username/interview-assistant)**

---

## ✨ 核心亮点 (Key Features)

*   **🤖 多 Agent 协同架构**：基于 LangChain 设计题目生成、答案评估、记忆管理及难度调整四个独立 Agent，实现复杂的逻辑链式调用。
*   **💻 交互式代码沙箱**：前端集成 **Monaco Editor** (VS Code 内核)，支持 Python/Java/Go 等多语言语法高亮；后端基于 `subprocess` 实现安全的代码实时运行环境。
*   **⚡ 高性能工程化实践**：
    *   采用 **FastAPI** 异步架构处理高并发请求。
    *   利用 SQLAlchemy `joinedload` 预加载机制解决 **N+1 查询问题**，接口吞吐量提升约 40%。
    *   引入 **Redis** 存储会话上下文，支持断点续练与高频数据缓存。
*   **📊 自适应难度算法**：基于滑动窗口算法分析用户历史得分趋势，动态在 Beginner 到 Expert 四阶难度间跃迁，提供个性化匹配。
*   **🐳 全链路容器化部署**：编写 **Docker Compose** 编排文件，一键启动 Frontend (Nginx), Backend (Uvicorn), PostgreSQL, Redis，实现标准化交付。
*   **🔍 可观测性监控**：集成 **Prometheus** 监控接口，实时追踪 API 延迟、请求计数及系统健康状态。

---

## 🛠️ 技术栈 (Tech Stack)

| 分类 | 技术选型 |
| :--- | :--- |
| **后端框架** | Python, FastAPI, Uvicorn, LangChain |
| **前端框架** | Vue3, TypeScript, Pinia, Element Plus, Monaco Editor |
| **数据存储** | PostgreSQL (持久化), Redis (会话/缓存) |
| **AI 模型** | DeepSeek API (DeepSeek-Chat) |
| **运维部署** | Docker, Docker Compose, Nginx, Prometheus |

---


