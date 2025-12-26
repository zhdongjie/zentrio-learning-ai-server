import logging
import os

import yaml
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.repositories import subject_repo, knowledge_repo
from app.schemas.diagnosis import DiagnosisResponse
from app.infra.llm import llm  # 导入封装好的 LLM

logger = logging.getLogger(__name__)

# 定义解析器
parser = PydanticOutputParser(pydantic_object=DiagnosisResponse)

# 模板路径 (建议放到 Config 或常量文件，这里先不动)
PROMPT_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "../core/prompts",  # 注意：根据你的目录结构调整相对路径
    "diagnosis_template.yaml"
)


async def generate_diagnosis(kp_code: str, question: str, student_answer: str) -> DiagnosisResponse:
    """
    RAG 诊断引擎 (Async 版本)
    """

    # --- 步骤 1: 检索知识背景 (RAG) ---
    # repositories 层目前是同步的，可以直接调用。
    # 如果 repo 改为了 async，这里要加 await
    knowledge_data = knowledge_repo.get_content_with_metadata(kp_code)

    if not knowledge_data:
        logger.warning(f"未找到知识点 {kp_code}，进入通用诊断模式")
        content = "通用逻辑与学术规范"
        subject_code = "default"
    else:
        # 解包 Tuple
        content, metadata = knowledge_data
        # 确保 metadata 是字典，防止 None 报错
        meta_dict = metadata if metadata else {}
        subject_code = meta_dict.get("subject_code", "default")

    # --- 步骤 2: 获取学科配置 ---
    config = subject_repo.get_config(subject_code)

    # --- 步骤 3: 构造并执行 LangChain 链 ---
    try:
        if not os.path.exists(PROMPT_FILE_PATH):
            # 这里的路径很容易出错，建议打印出来调试一下
            raise FileNotFoundError(f"Prompt 模板文件不存在: {PROMPT_FILE_PATH}")

        # 读取 YAML (I/O 操作)
        with open(PROMPT_FILE_PATH, 'r', encoding='utf-8') as f:
            prompt_config = yaml.safe_load(f)

        messages = []
        for msg in prompt_config.get("messages", []):
            messages.append((msg.get("role"), msg.get("content")))

        prompt_template = ChatPromptTemplate.from_messages(messages)

        # 构造链
        chain = prompt_template | llm | parser

        # 【核心修改】使用 ainvoke 进行异步调用
        result = await chain.ainvoke({
            "role_name": config.role_name,
            "style_desc": config.style_desc,
            "focus_points": config.focus_points,
            "content": content,
            "question": question,
            "student_answer": student_answer,
            "format_instructions": parser.get_format_instructions()
        })

        return result

    except Exception as e:
        logger.error(f"RAG 链路执行异常: {str(e)}", exc_info=True)

        # 【核心修改】兜底对象必须包含 schema 定义的所有必填字段 (is_correct)
        return DiagnosisResponse(
            is_correct=False,  # 必填
            error_type="SystemError",
            analysis="AI 导师连接不稳定，暂时无法分析。请稍后再试或联系老师。",
            suggested_actions=[]
        )
