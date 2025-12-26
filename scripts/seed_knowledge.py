import os

from sqlmodel import Session, create_engine, SQLModel
from zhipuai import ZhipuAI

import json
from app.core.config import settings
from app.models import KnowledgeVector, SubjectConfig

# 初始化智谱客户端
client = ZhipuAI(api_key=settings.ZHIPU_API_KEY)

# 创建引擎
engine = create_engine(settings.DATABASE_URL)


def get_embedding(text: str):
    """调用智谱 AI 获取向量"""
    response = client.embeddings.create(model="embedding-2", input=text)
    return response.data[0].embedding


def init_all_data():
    # 1. 自动根据模型创建表结构 (DDL)
    print("🚀 正在同步数据库表结构...")
    SQLModel.metadata.create_all(engine)

    # 获取当前脚本所在目录的绝对路径
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    base_json_dir = os.path.join(current_script_dir, 'json')

    with Session(engine) as session:
        # 2. 初始化学科配置 (Configs)
        config_dir = os.path.join(base_json_dir, 'configs')
        if os.path.exists(config_dir):
            for filename in os.listdir(config_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(config_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cfg_data = json.load(f)
                        print(f"📦 同步配置: {cfg_data['subject_name']}")

                        # Upsert 逻辑
                        db_cfg = session.get(SubjectConfig, cfg_data['subject_name'])
                        if db_cfg:
                            # 更新已有记录
                            db_cfg.role_name = cfg_data['role_name']
                            db_cfg.style_desc = cfg_data['style_desc']
                            db_cfg.focus_points = cfg_data['focus_points']
                        else:
                            # 插入新记录
                            db_cfg = SubjectConfig(**cfg_data)

                        session.add(db_cfg)

        # 3. 初始化知识点向量 (Knowledge)
        knowledge_dir = os.path.join(base_json_dir, 'knowledge')
        if os.path.exists(knowledge_dir):
            for filename in os.listdir(knowledge_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(knowledge_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        k_data = json.load(f)
                        for item in k_data:
                            print(f"🧠 向量化并同步: {item['name']}")

                            # 获取 Embedding
                            emb = get_embedding(item['content'])

                            # Upsert 逻辑
                            db_kv = session.get(KnowledgeVector, item['id'])
                            if db_kv:
                                db_kv.name = item['name']
                                db_kv.content = item['content']
                                db_kv.embedding = emb
                                db_kv.metadata_ = item['metadata']  # 注意这里使用 metadata_
                            else:
                                db_kv = KnowledgeVector(
                                    kp_code=item['id'],
                                    name=item['name'],
                                    content=item['content'],
                                    embedding=emb,
                                    metadata_=item['metadata']
                                )

                            session.add(db_kv)

        # 4. 提交所有变更
        session.commit()

    print("✅ PostgreSQL 数据初始化全量完成！")


if __name__ == "__main__":
    init_all_data()
