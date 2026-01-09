from sqlmodel import SQLModel, Field


class SubjectConfig(SQLModel, table=True):
    __tablename__ = "edu_subject_config"
    subject_name: str = Field(primary_key=True)
    role_name: str
    style_desc: str
    focus_points: str
