# app/services/diagnosis_service.py
import logging
import os

import yaml
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.infra.llm import llm
# 导入内部依赖
from app.repositories import subject_repo, knowledge_repo
from app.schemas.diagnosis import DiagnosisResponse

logger = logging.getLogger(__name__)


class DiagnosisService:
    def __init__(self):
        """
        初始化 DiagnosisService
        1. 注入依赖 (Repo, LLM)
        2. 计算 Prompt 路径 (消除硬编码)
        3. 预加载 Prompt 模板 (优化性能)
        """
        # 依赖注入
        self.knowledge_repo = knowledge_repo
        self.subject_repo = subject_repo
        self.llm = llm

        # 初始化解析器
        self.parser = PydanticOutputParser(pydantic_object=DiagnosisResponse)

        # 1. 定义 Prompt 文件路径
        # 获取当前文件所在目录 (app/services) 的上级目录 (app)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_dir = os.path.dirname(current_dir)

        # 拼接目标路径: app/core/prompts/diagnosis_template.yaml
        self.prompt_yaml_path = os.path.join(app_dir, "core", "prompts", "diagnosis_template.yaml")

        # 2. 加载模板 (启动时只执行一次)
        self.prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> ChatPromptTemplate:
        """
        加载并解析 YAML Prompt 模板
        使用 self.prompt_yaml_path，依赖实例状态，避免 'static method' 警告
        """
        try:
            if not os.path.exists(self.prompt_yaml_path):
                # 这是一个严重的配置错误，应用启动时应该报错
                raise FileNotFoundError(f"Critical Error: Prompt template not found at {self.prompt_yaml_path}")

            logger.info(f"Loading diagnosis prompt template from: {self.prompt_yaml_path}")

            with open(self.prompt_yaml_path, 'r', encoding='utf-8') as f:
                prompt_config = yaml.safe_load(f)

            messages = []
            # 转换 YAML 结构为 LangChain Message Tuple
            for msg in prompt_config.get("messages", []):
                messages.append((msg.get("role"), msg.get("content")))

            return ChatPromptTemplate.from_messages(messages)

        except Exception as e:
            logger.error(f"Failed to load diagnosis prompt: {e}")
            raise e

    async def diagnose(self, kp_code: str, question: str, student_answer: str) -> DiagnosisResponse:
        """
        执行 AI 诊断逻辑 (RAG + LLM)
        """
        try:
            # --- 步骤 1: 检索知识背景 (RAG) ---
            # 直接使用 self.knowledge_repo
            knowledge_data = self.knowledge_repo.get_content_with_metadata(kp_code)

            subject_code = "default"

            if not knowledge_data:
                logger.warning(f"Knowledge point {kp_code} not found, using generic logic.")
                content = "通用逻辑与学术规范"
            else:
                # 解包 Tuple: (content, metadata_dict)
                content_text, metadata = knowledge_data
                content = content_text
                # 安全获取 subject_code
                meta_dict = metadata if isinstance(metadata, dict) else {}
                subject_code = meta_dict.get("subject_code", "default")

            # --- 步骤 2: 获取学科配置 (用于调整 AI 语气) ---
            config = self.subject_repo.get_config(subject_code)

            # --- 步骤 3: 构造并执行 LangChain 链 ---
            # Chain: Template -> LLM -> Parser
            chain = self.prompt_template | self.llm | self.parser

            # 异步调用 LLM
            result = await chain.ainvoke({
                "role_name": config.role_name,
                "style_desc": config.style_desc,
                "focus_points": config.focus_points,
                "content": content,
                "question": question,
                "student_answer": student_answer,
                "format_instructions": self.parser.get_format_instructions()
            })

            return result

        except Exception as e:
            logger.error(f"RAG Diagnosis failed for KP={kp_code}: {str(e)}", exc_info=True)

            # --- 兜底逻辑 ---
            # 如果 AI 挂了或者解析失败，返回一个合法的默认对象，防止前端崩溃
            return DiagnosisResponse(
                is_correct=False,
                error_type="SystemError",
                analysis="系统繁忙，AI 助教暂时无法连接。请稍后重试或联系管理员。",
                suggested_actions=["请检查网络连接", "尝试重新提交"]
            )


# 导出单例实例 (供 Controller 使用)
diagnosis_service = DiagnosisService()
