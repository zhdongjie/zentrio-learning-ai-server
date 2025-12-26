
---

# Zentrio Learning AI Server

> **知衡 Edu · 智能诊断与 RAG 分析引擎**

本项目是 Zentrio Learning (知衡 Edu) 系统的 **智能层 (AI Layer)**，基于 FastAPI 框架构建。它作为系统的“智能外挂”，负责处理核心的教育学逻辑：知识点语义检索、学生错因分析以及个性化学习建议。

---

## 核心功能

* **RAG 检索增强生成**：利用向量数据库 (ChromaDB) 存储原子化知识点标准与易错画像，为大模型提供精准的教育学背景。
* **深度诊断分析**：调用智谱 AI (ChatGLM-4) 对学生提交的答案进行结构化拆解。
* **原子化画像支持**：输出结果严格符合 JSON 契约，直接支撑 Java 业务层更新学生能力画像。

---

## 技术架构

* **后端框架**: FastAPI
* **向量数据库**: ChromaDB (本地持久化存储)
* **大模型底座**: 智谱 AI (GLM-4)
* **开发语言**: Python 3.11+

---

## 目录结构说明

```text
zentrio-learning-ai-service/
├── app/
│   ├── main.py              # FastAPI 路由入口
│   ├── api/
│   │   └── diagnosis.py     # 诊断分析 API 接口
│   ├── core/
│   │   ├── config.py        # 智谱 AI 与系统环境变量管理
│   │   └── rag_engine.py    # RAG 核心逻辑 (检索 + Prompt 组装)
│   └── data/
│       └── vector_store.py  # ChromaDB 操作封装
├── db/                      # 向量数据库持久化文件目录
├── scripts/
│   └── seed_knowledge.py    # 知识点易错画像初始化脚本
├── .env                     # 敏感配置文件 (API Key)
└── requirements.txt         # 项目依赖清单

```

---

## 快速起步

### 1. 环境准备

确保已安装 Python 3.11，并创建虚拟环境：

```bash
python -m venv .venv
.\.venv\Scripts\activate  # Windows

```

### 2. 安装依赖

```bash
pip install -r requirements.txt

```

### 3. 配置环境变量

在项目根目录创建 `.env` 文件，并填写你的密钥：

```env
ZHIPU_API_KEY=你的智谱API密钥
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ANONYMOUS_TELEMETRY=False

```

### 4. 初始化向量知识库

运行脚本导入你提供的初中数学易错点画像数据：

```bash
python -m scripts.seed_knowledge

```

### 5. 启动服务

```bash
uvicorn app.main:app --reload

```

---

## 接口规范 (API Spec)

### 错因分析接口

* **URL**: `/api/v1/analyze`
* **Method**: `POST`
* **Request Body**:
```json
{
  "kp_id": "KP_MATH_EQUATION_BRACKET",
  "question": "解方程：3(x+2) = 12",
  "student_answer": "3x + 2 = 12"
}

```


* **Response**:
```json
{
  "error_type": "CONCEPT_CONFUSION",
  "analysis": "学生在分配律应用上出现错误，漏乘了常数项...",
  "suggested_actions": ["复习分配律的概念", "练习针对性题目"]
}

```



---

## 开发原则 (底线)

1. **非刷题导向**：AI 必须从能力维度出发，关注逻辑断层而非单纯对错。
2. **结构化输出**：所有分析必须可被 Java 业务层解析存储。
3. **不干预教学决策**：AI 仅提供建议，最终决策权在教师手中。

---
