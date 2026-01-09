import random


def disturb_text(line: str) -> str:
    """
    模拟学生不规范书写
    """
    if random.random() < 0.3:
        line = line.replace("=", " = ")
    if random.random() < 0.2:
        line += " "
    return line


def random_offset(max_offset: int = 2):
    """
    随机偏移(x, y)像素
    """
    dx = random.randint(-max_offset, max_offset)
    dy = random.randint(-max_offset, max_offset)
    return dx, dy
