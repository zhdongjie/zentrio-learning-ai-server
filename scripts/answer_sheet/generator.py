from io import BytesIO
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

from .handwriting import disturb_text, random_offset
from .layout import draw_question_block


class StudentAnswerSheetGenerator:
    """
    高考答题卡（学生作答）生成器
    支持动态画布 + 文字 + LaTeX公式 + 手写扰动
    """

    def __init__(self, output_dir: str = None, font_path: str = None, font_size: int = 28):
        # 输出目录
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parents[1] / "output"
        self.output_dir.mkdir(exist_ok=True, parents=True)

        # 字体
        if font_path:
            self.font_path = Path(font_path)
        else:
            self.font_path = Path(__file__).parents[2] / "assets/fonts/NotoSansSC-Thin.ttf"

        self.font_size = font_size
        self.font = self._load_font()

    def _load_font(self):
        if self.font_path.exists():
            try:
                font = ImageFont.truetype(str(self.font_path), self.font_size)
                print(f"✅ 成功加载字体: {self.font_path}")
                return font
            except Exception as e:
                print(f"⚠️ 字体加载失败: {self.font_path}, 错误: {e}")
        print(f"⚠️ 字体文件不存在: {self.font_path}, 使用默认字体")
        return ImageFont.load_default()

    @staticmethod
    def render_formula_to_image(formula: str, font_size: int = 28) -> Image.Image:
        """
        将 LaTeX 公式渲染成 PIL Image
        """
        fig = plt.figure()
        text = fig.text(0, 0, f"${formula}$", fontsize=font_size)
        fig.canvas.draw()
        bbox = text.get_window_extent()
        width, height = int(bbox.width) + 10, int(bbox.height) + 10
        plt.close(fig)

        fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
        text = fig.text(0, 0, f"${formula}$", fontsize=font_size)
        buf = BytesIO()
        fig.savefig(buf, format="png", transparent=True, bbox_inches='tight', pad_inches=0.05)
        plt.close(fig)
        buf.seek(0)
        return Image.open(buf)

    @staticmethod
    def _calculate_text_size(draw: ImageDraw.Draw, lines: List[str], font: ImageFont.FreeTypeFont, line_spacing: int):
        """
        根据文字和公式内容计算总宽高
        """
        width, height = 0, 0
        for line in lines:
            if line.startswith("FORMULA:"):
                formula_img = StudentAnswerSheetGenerator.render_formula_to_image(
                    line.replace("FORMULA:", ""),
                    font_size=int(font.size)
                )
                w, h = formula_img.size
            else:
                bbox = draw.textbbox((0, 0), line, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            width = max(width, w)
            height += h + line_spacing
        return width, height

    def generate_answer_sheet(
            self,
            question_no: int,
            score: int,
            student_steps: List[str],
            question_text: str = "",
            answer_text: str = "",
            filename: str = "answer_sheet.png",
            line_spacing: int = 15,
            padding_x: int = 40,
            padding_y: int = 40
    ) -> str:
        """
        生成答题卡图片
        """
        lines = []
        if question_text:
            lines.append(f"题目：{question_text}")
            lines.append("")
        lines.append("解：")
        lines.extend(student_steps)
        if answer_text:
            lines.append("")
            lines.append(f"答：{answer_text}")

        # 计算动态画布大小
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        width, height = self._calculate_text_size(draw, lines, self.font, line_spacing)
        img_width = width + 2 * padding_x
        img_height = height + 2 * padding_y

        # 创建画布
        img = Image.new("RGB", (img_width, img_height), "white")
        draw = ImageDraw.Draw(img)

        # 答题框
        block_x, block_y = padding_x - 20, padding_y - 20
        block_w, block_h = width + 40, height + 40
        draw_question_block(draw, block_x, block_y, block_w, block_h, question_no, score)

        # 绘制内容
        text_x, text_y = padding_x, padding_y
        for line in lines:
            dx, dy = random_offset()
            if line.startswith("FORMULA:"):
                formula_img = self.render_formula_to_image(line.replace("FORMULA:", ""), self.font_size)
                img.paste(formula_img, (text_x + dx, text_y + dy), formula_img)
                text_y += formula_img.height + line_spacing
            else:
                draw.text((text_x + dx, text_y + dy), disturb_text(line), fill="black", font=self.font)
                bbox = draw.textbbox((0, 0), line, font=self.font)
                text_height = bbox[3] - bbox[1]
                text_y += text_height + line_spacing

        out_path = self.output_dir / filename
        img.save(out_path)
        print(f"🖼️ 答题卡已生成: {out_path}")
        return str(out_path)
