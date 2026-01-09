from PIL import ImageDraw


def draw_question_block(
        draw: ImageDraw.Draw,
        x: int,
        y: int,
        width: int,
        height: int,
        question_no: int,
        score: int
):
    """
    绘制答题区域框和题号、分值
    """
    # 边框
    draw.rectangle(
        [x, y, x + width, y + height],
        outline="black",
        width=2
    )
    # 题号和分值
    draw.text(
        (x + 10, y - 30),
        f"题号: {question_no}",
        fill="black"
    )
    draw.text(
        (x + width - 80, y - 30),
        f"分值: {score}",
        fill="black"
    )
