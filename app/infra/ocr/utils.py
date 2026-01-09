# app/infra/ocr/utils.py
import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import List, Union, Optional

import cv2
import numpy as np
import requests
from PIL import Image, ImageOps
from fastapi import UploadFile, HTTPException

logger = logging.getLogger(__name__)


def preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    """
    内存图片预处理（工程优化版）：
    1. RGB -> BGR (OpenCV 默认格式)
    2. 智能放大 (解决小图/远图识别不清的问题)
    3. 增加白边 (解决文字贴边检测不到的问题)
    4. ❌ 已移除二值化 (二值化会导致细节丢失，降低 RapidOCR 准确率)
    """
    # 1. 读取图片并转为 OpenCV BGR 格式
    pil_img = Image.open(BytesIO(image_bytes)).convert("RGB")
    try:
        pil_img = ImageOps.exif_transpose(pil_img)
    except Exception as e:
        logger.warning(f"Image auto-rotation failed: {e}")

    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # 2. 智能放大
    # RapidOCR 对短边小于 960px 的图片识别效果一般
    # 如果图片较小，按比例放大短边到 960px
    h, w = img.shape[:2]
    short_side = min(h, w)
    target_short = 960

    if short_side < target_short:
        scale = target_short / short_side
        # 限制最大放大倍数，防止图片过大撑爆内存 (Max 3x)
        if scale > 3.0: scale = 3.0

        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # 3. 增加白边 (Padding)
    # 上下左右各加 50 像素白边，防止文字紧贴边缘被裁掉
    pad_size = 50
    img = cv2.copyMakeBorder(
        img,
        pad_size, pad_size, pad_size, pad_size,
        cv2.BORDER_CONSTANT,
        value=(255, 255, 255)
    )

    return img


def sort_ocr_results(results: list) -> list:
    """
    对 OCR 结果进行几何坐标排序 (从上到下，从左到右)
    解决 RapidOCR 返回顺序混乱、无法分行的问题

    RapidOCR item 格式: [box, text, score]
    box: [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    """
    if not results:
        return []

    # 1. 展平嵌套列表 (兼容 RapidOCR 可能返回的嵌套结构)
    flat_results = []

    def flatten(items):
        for item in items:
            if isinstance(item, (list, tuple)):
                # 有效结果判断: 长度>=3, 第一个元素是box列表(4个点)
                if len(item) >= 3 and isinstance(item[0], list) and len(item[0]) == 4:
                    flat_results.append(item)
                else:
                    flatten(item)

    flatten(results)

    if not flat_results:
        return []

    # 2. 按 Y 轴 (上边缘) 进行初步排序
    # item[0] 是 box，p[1] 是点的 y 坐标
    flat_results.sort(key=lambda item: min(p[1] for p in item[0]))

    # 3. 智能分行逻辑
    sorted_res = []
    _boxes = list(flat_results)

    while _boxes:
        # 取出当前最靠上的一个框作为“行基准”
        curr = _boxes.pop(0)
        curr_box = curr[0]
        curr_y_min = min(p[1] for p in curr_box)
        curr_y_max = max(p[1] for p in curr_box)
        curr_height = curr_y_max - curr_y_min

        # 这一行的所有框 (初始化放入基准框)
        line_boxes = [curr]

        # 判定同行的阈值：Y 轴差异小于行高的一半
        threshold = curr_height * 0.5

        next_iter_boxes = []
        for box_item in _boxes:
            box = box_item[0]
            y_min = min(p[1] for p in box)

            # 如果高度差在阈值内，视为同一行
            if abs(y_min - curr_y_min) < threshold:
                line_boxes.append(box_item)
            else:
                next_iter_boxes.append(box_item)

        # 对这一行的框，按 X 轴 (左边缘) 从左到右排序
        line_boxes.sort(key=lambda item: min(p[0] for p in item[0]))

        # 加入最终结果
        sorted_res.extend(line_boxes)

        # 处理下一批
        _boxes = next_iter_boxes

    return sorted_res


def extract_text_from_ocr_results(results: Union[list, tuple]) -> List[str]:
    """
    提取并排序文字的入口函数
    """
    # 1. 调用复杂的几何排序
    sorted_items = sort_ocr_results(results)

    # 2. 只提取文本部分
    return [item[1] for item in sorted_items if isinstance(item[1], str)]


async def read_file_bytes(
        file: UploadFile = None,
        image_base64: Optional[str] = None,
        file_url: Optional[str] = None,
        file_path: Optional[str] = None,
) -> bytes:
    """根据优先级返回图片字节"""
    if file is not None:
        return await file.read()

    if image_base64:
        try:
            return base64.b64decode(image_base64)
        except Exception:
            raise HTTPException(status_code=400, detail="Base64 解码失败")

    if file_url:
        try:
            resp = requests.get(file_url, timeout=5)
            resp.raise_for_status()
            return resp.content
        except Exception:
            raise HTTPException(status_code=400, detail="无法下载 file_url 图片")

    if file_path:
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise HTTPException(status_code=400, detail="file_path 不存在或不是文件")
        return path.read_bytes()

    raise HTTPException(status_code=400, detail="未提供有效图片来源")
