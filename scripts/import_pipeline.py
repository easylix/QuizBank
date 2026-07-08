#!/usr/bin/env python3
"""
高中数学试卷批量导入流水线
================================
第4份验证试卷：2023全国乙卷（理）

流程：
  0. PDF预处理（分片，重叠1页）
  1. 多模态OCR → 纯文本 + [图]标记（仅原始转录，不做结构化）
  2. 本地文本模型 → 结构化JSON（切题、分离选项/答案/解析、判断题型/难度/topicId）
  3. 图片提取（嵌入式位图 + 矢量图渲染PNG）
  4. 图片匹配（[图]→[figN]，OCR标记为主 + y坐标辅助 + 多模态校核）
  5. 自动校验（阻塞式）
  6. 本地保存到JSON + SQLite（供验证）

用法：
  python3 import_pipeline.py --pdf <解析卷PDF路径> --source "2023全国乙卷理"

中间产物保留：
  - OCR原始文本: {work_dir}/{pdf_name}_ocr/ocr_merged.txt
  - 结构化JSON:  {work_dir}/{pdf_name}_structured.json
  - 提取的图片:  {work_dir}/{pdf_name}_images/p*.png
  - 最终数据:    {work_dir}/{pdf_name}_ready.json
"""

import os, sys, json, re, uuid, base64, io, hashlib, time, copy, textwrap
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

import fitz
import requests

# ═══════════════════════════════════════════════════════════════════════════
#  配置
# ═══════════════════════════════════════════════════════════════════════════

VOLC_API_KEY = "ark-c966fdeb-e217-4092-8852-5688be15c6af-2f372"
VOLC_BASE_URL = "https://ark.cn-beijing.volces.com"
VOLC_MODEL = "doubao-seed-2-0-mini-260428"
OCR_CHUNK_SIZE = 1   # 单页OCR，每页单独调用
OVERLAP_PAGES = 0      # 单页无需重叠

# ═══════════════════════════════════════════════════════════════════════════
#  辅助函数
# ═══════════════════════════════════════════════════════════════════════════

def log(msg): print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)
def err(msg): print(f"[{time.strftime('%H:%M:%S')}] ❌ {msg}", flush=True)

def retry_post(url, headers, json_data, max_retries=3, timeout=180):
    last_err = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            wait = min(5 * (attempt + 1), 30)
            log(f"  请求失败(attempt {attempt+1}/{max_retries}): {e}，{wait}s后重试")
            time.sleep(wait)
    raise last_err


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 0: PDF预处理（分片）
# ═══════════════════════════════════════════════════════════════════════════

def step0_split_pdf(pdf_path: str, output_dir: str) -> List[str]:
    """将大PDF分片，每片最多OCR_CHUNK_SIZE页，相邻片重叠OVERLAP_PAGES页"""
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    total = doc.page_count
    log(f"【步骤0】PDF分片: 共{total}页，每片最多{OCR_CHUNK_SIZE}页，重叠{OVERLAP_PAGES}页")

    parts = []
    start = 0
    part_num = 1
    while start < total:
        end = min(start + OCR_CHUNK_SIZE, total)
        part_doc = fitz.open()
        part_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
        part_path = os.path.join(output_dir, f"part{part_num}.pdf")
        part_doc.save(part_path)
        part_doc.close()
        parts.append(part_path)
        log(f"  分片{part_num}: 页{start+1}-{end} → {os.path.basename(part_path)}")
        start = end - OVERLAP_PAGES if end < total else end
        if start < 0: start = 0
        part_num += 1

    doc.close()
    return parts


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 1: 多模态OCR → 纯文本 + [图]标记
#  ⚠️ 只做原始转录：保留换行、公式$包裹、图片位置标记[图]
#    不做任何结构化、不标注知识点、不判断难度
# ═══════════════════════════════════════════════════════════════════════════

def step1_upload_pdf(pdf_path: str) -> str:
    """上传PDF到火山引擎Files API，等待active，返回file_id"""
    log(f"  上传 {os.path.basename(pdf_path)} 到火山引擎...")
    upload_url = f"{VOLC_BASE_URL}/api/v3/files"
    headers = {"Authorization": f"Bearer {VOLC_API_KEY}"}

    with open(pdf_path, 'rb') as f:
        resp = requests.post(
            upload_url, headers=headers,
            files={"file": (os.path.basename(pdf_path), f, "application/pdf")},
            data={"purpose": "user_data"},
            timeout=120
        )
    data = resp.json()
    if 'error' in data:
        raise Exception(f"Upload failed: {data['error']}")

    file_id = data['id']
    log(f"  文件ID: {file_id}，等待active...")
    for _ in range(15):
        time.sleep(2)
        status_resp = requests.get(
            f"{VOLC_BASE_URL}/api/v3/files/{file_id}",
            headers=headers, timeout=15
        )
        status_data = status_resp.json()
        if status_data.get('status') == 'active':
            log(f"  文件active!")
            return file_id
        elif status_data.get('status') == 'error':
            raise Exception(f"File processing error: {status_data}")

    raise Exception(f"File {file_id} did not become active in time")


def step1_ocr_pdf(pdf_path: str) -> str:
    """对单个PDF分片做多模态OCR，输出纯文本+[图]标记"""
    file_id = step1_upload_pdf(pdf_path)

    # 调用OCR
    chat_url = f"{VOLC_BASE_URL}/api/v3/chat/completions"
    chat_headers = {"Authorization": f"Bearer {VOLC_API_KEY}",
                    "Content-Type": "application/json"}

    prompt = textwrap.dedent("""\
你是高考数学试卷OCR专家。请将PDF中的文字原样转录为纯文本，严格遵守以下规则：

**核心规则（必须遵守）：**
1. **保留原始排版**：保持原文的换行位置和段落分隔，不要重新排版。
2. **公式用$包裹**：行内公式用 $...$，独立公式用 $$...$$。
3. **图片用[图]标记**：仅在遇到真正独立的图片（几何图、函数图、示意图）时，在图片位置打 [图]。
   ⚠️ 注意区分：
   - 文本中出现的"如图""图1""图2""图所示"等文字中的"图"字，**不是图片标记**，原样转录即可。
   - 表格、统计图表等结构化数据**不要打[图]**，请用文本形式原样转录（表格保留行列结构）。
   - 图片的编号文字（如"图1""图2"）在图片外部的话，保留文本，不要与[图]合并。
4. **保留试题编号**：如"1." "2." "（1）" "（2）" 等原题编号必须保留。
5. **知识点与难度单独输出**：所有题目转录完毕后，另起一行"---"作为分隔，然后按题号列出每道题的知识点和难度。

**难度标准：** 基础 / 中等 / 困难

**输出格式示例：**
...（题目转录结束）

---
知识点与难度：
1. 知识：集合的基本运算 难度：基础
2. 知识：复数的四则运算 难度：基础
3. 知识：平面向量的数量积 难度：中等
...

注意："---"分隔线前的部分只做文本转录，不要混入知识点标注。开始转录：""")

    payload = {
        "model": VOLC_MODEL,
        "messages": [
            {"role": "user", "content": [
                {"type": "file", "file": {"file_id": file_id}},
                {"type": "text", "text": prompt}
            ]}
        ],
        "max_tokens": 16384
    }

    log(f"  调用OCR模型...")
    # 12页PDF的OCR可能耗时3-5分钟，使用较长超时
    result = retry_post(chat_url, headers=chat_headers, json_data=payload, timeout=600)
    text = result["choices"][0]["message"]["content"]
    log(f"  完成，获取{len(text)}字符")
    return text


def step1_ocr_all(parts: List[str], output_dir: str) -> str:
    """对所有分片做OCR，合并，保留原始文件"""
    os.makedirs(output_dir, exist_ok=True)
    all_text_parts = []
    for i, part_path in enumerate(parts):
        log(f"  OCR分片 {i+1}/{len(parts)}...")
        text = step1_ocr_pdf(part_path)
        raw_path = os.path.join(output_dir, f"ocr_part{i+1}_raw.txt")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"    原始文本保存: {raw_path}")
        all_text_parts.append(text)

    merged = _merge_ocr_texts(all_text_parts)
    # 清理换行等OCR排版问题
    merged = _clean_ocr_text(merged)
    merged_path = os.path.join(output_dir, "ocr_merged.txt")
    with open(merged_path, "w", encoding="utf-8") as f:
        f.write(merged)
    log(f"  合并OCR结果: {merged_path} ({len(merged)}字符)")
    return merged


def _merge_ocr_texts(texts: List[str]) -> str:
    """合并多个分片，去重叠"""
    if len(texts) <= 1:
        return texts[0] if texts else ""
    result = texts[0]
    for i in range(1, len(texts)):
        cur = texts[i]
        tail = result[-200:]
        best_pos = -1
        for length in range(min(200, len(tail)), 20, -10):
            frag = tail[-length:]
            idx = cur.find(frag)
            if idx >= 0 and idx < len(cur) // 4:
                best_pos = idx + length
                break
        if best_pos > 0:
            result += cur[best_pos:]
        else:
            result += cur
    return result


def _clean_ocr_text(text: str) -> str:
    """清理OCR文本中的排版问题
    
    1. 合并PDF断行：行末不是标点/公式且下一行小写/连续 → 合并
    2. 保留分页标记但移除"第X页 | 共Y页"文本
    3. 保持[图]标记独立成行
    """
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        # 移除分页标记行，如 "第1页 | 共25页"
        if re.match(r'^第\d+页\s*\|?\s*共\d+页$', line.strip()):
            continue
        cleaned.append(line.rstrip())
    
    # 合并断行：如果上一行末尾不是句号/问号/叹号/公式结束符
    # 且下一行不是空行、不是标题、不是题号开头、不是[图]
    merged_lines = []
    i = 0
    while i < len(cleaned):
        curr = cleaned[i]
        if not curr:
            merged_lines.append('')
            i += 1
            continue
        # 保留这些行，不合并：空行、[图]标记、题号开头（如"1." "2."）、标题（").、"一、"等）
        if (re.match(r'^\[图\]', curr) or
            re.match(r'^[一二三四五六七八九十]+[、.]', curr) or
            re.match(r'^\d+\.\s', curr) or
            re.match(r'^（\d+）', curr) or
            re.match(r'^【', curr) or
            re.match(r'^[A-Ea-e][.．、]', curr) or
            not curr.endswith((',', '，', '；', '；', '$'))):
            # 行末没有继续的标记，独立成行
            merged_lines.append(curr)
            i += 1
            continue
        
        # 行末有逗号或公式结束符，可能还有后续内容
        # 看下一行是否小写字母/数学符号继续
        result = curr
        while i + 1 < len(cleaned):
            nxt = cleaned[i + 1]
            if not nxt:
                break
            # 下一行是题号、标题、[图]、选项开头 → 不合并
            if (re.match(r'^\[图\]', nxt) or
                re.match(r'^[一二三四五六七八九十]+[、.]', nxt) or
                re.match(r'^\d+\.\s', nxt) or
                re.match(r'^（\d+）', nxt) or
                re.match(r'^【', nxt) or
                re.match(r'^[A-Ea-e][.．、]', nxt)):
                break
            # 行末以公式 $ 结尾，且下一行也以公式或小写开头 → 合并
            if result.endswith('$') and (nxt.startswith('$') or nxt[0].islower()):
                result += nxt
                i += 1
                continue
            break
        merged_lines.append(result)
        i += 1
    
    return '\n'.join(merged_lines)


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 2: 本地文本模型 → 结构化JSON
#  输入：步骤1输出的纯文本（含[图]标记）
#  输出：JSON数组，每题含 type/difficulty/content/options/answer/solution/topicId
# ═══════════════════════════════════════════════════════════════════════════

def step2_structure_text(raw_text: str, source: str) -> List[dict]:
    """本地文本模型将OCR纯文本解析为结构化JSON"""
    chat_url = f"{VOLC_BASE_URL}/api/v3/chat/completions"
    chat_headers = {"Authorization": f"Bearer {VOLC_API_KEY}",
                    "Content-Type": "application/json"}

    prompt = textwrap.dedent(f"""\
你是一名高考数学试卷解析专家。请将以下OCR文本解析为结构化JSON数组。

试卷来源：{source}

每个对象格式（严格遵循）：
{{
  "type": "单选题" | "填空题" | "解答题",
  "difficulty": "基础" | "中等" | "困难",
  "content": "题干文本（不含选项字母），保留[figX]标记（如果有的话）",
  "options": "选项（每行一个，如A. xxx\\nB. xxx\\nC. xxx\\nD. xxx），填空题和解答题留空",
  "answer": "纯答案字母或答案文本，不要【答案】前缀",
  "solution": "解析文本（保留换行，【点睛】放在末尾），保留[figX]标记",
  "topicId": "从以下知识点ID中选择最匹配的，跨多个用逗号分隔"
}}

**严格要求：**
1. 按题号切分，每道题一个对象
2. content中如果内嵌了选项（如"A. xxx B. xxx C. xxx D. xxx"），剥离到options字段
3. answer只含答案本身，不含"【答案】"等前缀
4. solution不含"【答案】"行，只含解析和点睛
5. difficulty根据题目内容语义判断
6. topicId选择题目前最匹配的知识点ID：

知识点ID列表：
M1-C1-T1 集合的概念与表示
M1-C1-T2 集合间的基本关系（子集、真子集）
M1-C1-T3 集合的基本运算（交、并、补）
M1-C1-T4 命题与充要条件
M1-C1-T5 全称量词与存在量词
M1-C2-T1 不等式的性质
M1-C2-T2 基本不等式（均值不等式）
M1-C2-T3 二次函数与一元二次方程、不等式
M1-C3-T1 函数的概念及其表示
M1-C3-T2 函数的单调性与最值
M1-C3-T3 函数的奇偶性
M1-C3-T4 幂函数
M1-C3-T5 函数的综合应用
M1-C4-T1 指数运算与指数函数
M1-C4-T2 对数运算与对数函数
M1-C4-T3 函数的零点与二分法
M1-C4-T4 函数模型及其应用
M1-C5-T1 任意角与弧度制
M1-C5-T2 三角函数的概念
M1-C5-T3 同角三角函数基本关系与诱导公式
M1-C5-T4 三角函数的图像与性质
M1-C5-T5 函数 y=Asin(ωx+φ) 的图像
M1-C5-T6 三角恒等变换（和差角、倍角公式）
M2-C1-T1 平面向量的概念与线性运算
M2-C1-T2 平面向量的数量积
M2-C1-T3 平面向量基本定理与坐标表示
M2-C1-T4 平面向量的应用
M2-C2-T1 复数的概念与几何意义
M2-C2-T2 复数的四则运算
M2-C3-T1 基本立体图形与直观图
M2-C3-T2 空间点、直线、平面的位置关系
M2-C3-T3 直线、平面的平行判定与性质
M2-C3-T4 直线、平面的垂直判定与性质
M2-C3-T5 简单几何体的表面积与体积
M2-C4-T1 随机抽样
M2-C4-T2 用样本估计总体
M2-C5-T1 随机事件与概率
M2-C5-T2 事件的相互独立性
M2-C5-T3 频率与概率
M3-C1-T1 空间向量及其运算
M3-C1-T2 空间向量基本定理
M3-C1-T3 空间向量运算的坐标表示
M3-C1-T4 用空间向量研究位置关系
M3-C1-T5 用空间向量研究距离与夹角
M3-C2-T1 直线的倾斜角、斜率与方程
M3-C2-T2 两条直线的位置关系与距离公式
M3-C2-T3 圆的方程
M3-C2-T4 直线与圆、圆与圆的位置关系
M3-C3-T1 椭圆
M3-C3-T2 双曲线
M3-C3-T3 抛物线
M4-C1-T1 数列的概念与表示
M4-C1-T2 等差数列
M4-C1-T3 等比数列
M4-C1-T4 数列的综合应用
M4-C2-T1 导数的概念与几何意义
M4-C2-T2 导数的运算
M4-C2-T3 导数与函数的单调性
M4-C2-T4 导数与函数的极值、最值
M4-C2-T5 导数的综合应用
M5-C1-T1 分类加法与分步乘法计数原理
M5-C1-T2 排列与组合
M5-C1-T3 二项式定理
M5-C2-T1 条件概率与全概率公式
M5-C2-T2 离散型随机变量的分布列与数字特征
M5-C2-T3 二项分布与超几何分布
M5-C2-T4 正态分布
M5-C3-T1 成对数据的相关关系与回归分析
M5-C3-T2 列联表与独立性检验

OCR文本：
---
{raw_text[:100000]}
---

只输出JSON数组，不要其他说明。""")

    log(f"【步骤2】调用文本模型做结构化...")
    try:
        payload = {
            "model": VOLC_MODEL,
            "messages": [
                {"role": "system", "content": "你是高考数学试卷解析专家，只输出严格JSON。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 16384,
            "temperature": 0.1
        }
        result = retry_post(chat_url, headers=chat_headers, json_data=payload, timeout=300)
        text = result["choices"][0]["message"]["content"]
    except Exception as e:
        err(f"文本模型调用失败: {e}")
        return []

    # 提取JSON
    json_match = re.search(r'\[.*\]', text, re.DOTALL)
    json_str = json_match.group() if json_match else text
    # 清理可能的markdown代码块
    json_str = re.sub(r'^```(json)?\s*', '', json_str.strip())
    json_str = re.sub(r'\s*```$', '', json_str)

    try:
        questions = json.loads(json_str)
        log(f"  解析出 {len(questions)} 道题")
        return questions
    except json.JSONDecodeError as e:
        err(f"JSON解析失败: {e}")
        log(f"  模型输出前500字:\n{text[:500]}")
        return []


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 3: 图片提取（嵌入式位图 + 矢量图渲染PNG）
#  全部保留原始图片文件和中间文件
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ExtractedImage:
    page_num: int
    index: int
    image_data: bytes
    bbox: tuple
    source_type: str       # "embedded" | "vector"
    content_hash: str
    file_path: str = ""    # 本地文件路径


def step3_extract_images(pdf_path: str, output_dir: str) -> List[ExtractedImage]:
    """从PDF提取所有图片（嵌入式位图 + 矢量图渲染PNG），全部保留原文件"""
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    images: List[ExtractedImage] = []
    seen_hashes: set = set()

    for page_idx in range(doc.page_count):
        page = doc[page_idx]
        page_num = page_idx + 1
        page_rect = page.rect

        # ── 3a. 嵌入式位图 ──
        img_list = page.get_images(full=True)
        for img_idx, img_info in enumerate(img_list):
            xref = img_info[0]
            base_img = doc.extract_image(xref)
            img_bytes = base_img["image"]
            ext = base_img["ext"]
            img_hash = hashlib.sha256(img_bytes).hexdigest()[:16]
            if img_hash in seen_hashes:
                continue
            seen_hashes.add(img_hash)

            # 获取bbox（尝试多种方式）
            bbox = (0, 0, 0, 0)
            try:
                # 从图像的显示列表中找位置
                img_blocks = page.get_image_info()
                for ib in img_blocks:
                    if ib.get('xref') == xref or not bbox or bbox == (0,0,0,0):
                        bbox = ib.get('bbox', (0,0,0,0))
            except Exception:
                pass

            # 跳过极小图片（<50x50，通常是数学符号如补集符、根号等）
            if base_img["width"] < 50 and base_img["height"] < 50:
                log(f"    跳过小符号: p{page_num} xref={xref} {base_img['width']}x{base_img['height']}")
                continue

            # 统一保存为PNG
            try:
                from PIL import Image as PILImage
                pil = PILImage.open(io.BytesIO(img_bytes))
                buf = io.BytesIO()
                pil.save(buf, format="PNG")
                png_data = buf.getvalue()
            except ImportError:
                if ext.lower() == "png":
                    png_data = img_bytes
                else:
                    png_data = img_bytes  # 保留原始格式

            img_filename = f"p{page_num:02d}_e{img_idx+1}_{ext}.png"
            img_path = os.path.join(output_dir, img_filename)
            with open(img_path, "wb") as f:
                f.write(png_data)

            images.append(ExtractedImage(
                page_num=page_num, index=img_idx + 1,
                image_data=png_data, bbox=bbox,
                source_type="embedded", content_hash=img_hash,
                file_path=img_path
            ))
            log(f"    嵌入式: p{page_num} #{img_idx+1} {os.path.getsize(img_path)//1024}KB {img_path}")

        # ── 3b. 矢量图渲染 ──
        # 仅当页面没有嵌入式图片时提取矢量图（避免公式片段重复）
        if images:
            same_page = [x for x in images if x.page_num == page_num and x.source_type == 'embedded']
            if same_page:
                continue  # 已有嵌入式图片，无需再提取矢量图

        # 检测显著的矢量图形区域
        try:
            paths = page.get_drawings()
            significant = [p for p in paths
                          if p['rect'].width > 50 and p['rect'].height > 50]
        except Exception:
            significant = []

        if not significant:
            continue

        # 合并所有图形的bbox
        combined = fitz.Rect()
        for p in significant:
            combined |= p['rect']
        margin = 10
        clip = fitz.Rect(
            max(0, combined.x0 - margin),
            max(0, combined.y0 - margin),
            min(page_rect.width, combined.x1 + margin),
            min(page_rect.height, combined.y1 + margin)
        )
        if clip.width <= 40 or clip.height <= 40:
            continue

        # 2x分辨率渲染
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip)
        vdata = pix.tobytes("png")
        vhash = hashlib.sha256(vdata).hexdigest()[:16]
        if vhash in seen_hashes:
            continue
        seen_hashes.add(vhash)

        vec_idx = len([x for x in images
                       if x.page_num == page_num and x.source_type == "vector"]) + 1
        v_filename = f"p{page_num:02d}_v{vec_idx}.png"
        v_path = os.path.join(output_dir, v_filename)
        with open(v_path, "wb") as f:
            f.write(vdata)

        images.append(ExtractedImage(
            page_num=page_num, index=vec_idx,
            image_data=vdata,
            bbox=(clip.x0, clip.y0, clip.x1, clip.y1),
            source_type="vector", content_hash=vhash,
            file_path=v_path
        ))
        log(f"    矢量图: p{page_num} v{vec_idx} @({clip.x0:.0f},{clip.y0:.0f},{clip.x1:.0f},{clip.y1:.0f}) "
            f"{os.path.getsize(v_path)//1024}KB {v_path}")

    doc.close()
    # 保存图片清单
    manifest = []
    for img in images:
        manifest.append({
            "page": img.page_num, "index": img.index,
            "type": img.source_type,
            "bbox": list(img.bbox) if isinstance(img.bbox, tuple) else list(img.bbox),
            "file": os.path.basename(img.file_path),
            "size_bytes": len(img.image_data),
            "hash": img.content_hash
        })
    manifest_path = os.path.join(output_dir, "image_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    log(f"  图片清单: {manifest_path}")
    n_emb = sum(1 for x in images if x.source_type == 'embedded')
    n_vec = sum(1 for x in images if x.source_type == 'vector')
    log(f"  共提取 {len(images)} 张图片（{n_emb}嵌入式 + {n_vec}矢量）")
    return images


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 4: 图片匹配（[图]→[figN]）
#  以OCR文本中的[图]标记位置为准，y坐标辅助
#  低置信度走多模态校核
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ImageMapping:
    fig_index: str
    image: Optional[ExtractedImage]
    confidence: float
    method: str   # "y_coord" | "multimodal_verify" | "fallback"


def step4_match_images(ocr_text: str, images: List[ExtractedImage],
                        pdf_path: str,
                        work_dir: str = "/tmp/import_pipeline_v2") -> Tuple[str, List[ImageMapping]]:
    """匹配图片到[图]标记，生成[figN]
    
    匹配策略：
    1. [图]数与图片数一致 → 按顺序一一对应
    2. 不一致 → 调多模态视觉理解确认匹配
    3. 仍无法解决 → 记录并跳过
    """
    fig_matches = list(re.finditer(r'\[图\]', ocr_text))
    n_figs = len(fig_matches)
    n_imgs = len(images)
    log(f"【步骤4】OCR文本中找到 {n_figs} 个 [图] 标记，提取 {n_imgs} 张图片")

    if n_figs == 0:
        return ocr_text, []

    # [图]总数 == 图片总数 → 全局顺序匹配（不分页，避免分页标记丢失导致的问题）
    if n_figs > 0 and n_figs == n_imgs:
        log(f"    [图]总数 {n_figs} == 图片总数 {n_imgs} → 全局顺序匹配")
        mappings = []
        result_text = ocr_text
        total_shift = 0
        for idx, fm in enumerate(fig_matches):
            fig_num = idx + 1
            matched = images[idx]
            conf = 0.85 if matched.source_type == "embedded" else 0.7
            mappings.append(ImageMapping(
                fig_index=str(fig_num),
                image=matched,
                confidence=conf,
                method="sequential"
            ))
            adj_pos = fm.start() + total_shift
            result_text = result_text[:adj_pos] + f"[fig{fig_num}]" + result_text[adj_pos + 3:]
            total_shift += len(str(fig_num)) - 2
        return result_text, mappings

    # 读取每页原始OCR文件来精确分配 [图] 所属页码
    # 每页原始文件包含 "第X页 | 共Y页" 标记行，用于分页
    import glob
    raw_dir = os.path.join(os.path.dirname(ocr_text[:1]) if False else 
               os.path.dirname(work_dir if os.path.isdir(work_dir) else work_dir+'_dummy'), 'ocr')
    # 尝试从 work_dir 定位 ocr 目录
    ocr_dir = None
    for guess in [os.path.join(work_dir, 'ocr'), os.path.join(os.path.dirname(work_dir or '.'), 'ocr')]:
        if os.path.isdir(guess) and any(f.startswith('page_') and f.endswith('_raw.txt') for f in os.listdir(guess)):
            ocr_dir = guess
            break
    if ocr_dir is None:
        # 降级：从合并文本行数估算
        total_lines = ocr_text.count('\n')
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
        lines_per_page = total_lines / total_pages if total_pages > 0 else 50

    # 图片按页分组
    img_by_page: Dict[int, List[ExtractedImage]] = {}
    for img in images:
        img_by_page.setdefault(img.page_num, []).append(img)

    # [图] 分配到页码
    fig_by_page: Dict[int, list] = {}
    if ocr_dir:
        # 用每页原始文件计数，精确分配
        for m in fig_matches:
            pos_in_merged = m.start()
            # 根据原始文件的内容长度估算页码
            page_starts = [0]  # byte offset of each page's start in ocr_text
            for pn in range(1, 26):
                raw_path = os.path.join(ocr_dir, f'page_{pn:02d}_raw.txt')
                if os.path.exists(raw_path):
                    with open(raw_path) as f:
                        raw_text = f.read()
                    # Apply same cleanup to get the cleaned page text
                    page_len = len(_clean_ocr_text(raw_text)) + 1  # +1 for newline separator
                    page_starts.append(page_starts[-1] + page_len)
            # Now find which page this [图] belongs to
            est_page = 1
            for i in range(len(page_starts) - 1):
                if page_starts[i] <= pos_in_merged < page_starts[i + 1]:
                    est_page = i + 1
                    if est_page > 25:
                        est_page = 25
                    break
            fig_by_page.setdefault(est_page, []).append(m)
    else:
        # 降级：从行号估算
        for m in fig_matches:
            line_num = ocr_text[:m.start()].count('\n')
            est_page = min(total_pages, max(1, int(line_num / lines_per_page) + 1))
            candidates = [p for p in range(max(1, est_page-1), min(total_pages, est_page+1)+1)
                          if p in img_by_page]
            if candidates:
                est_page = min(candidates, key=lambda p: abs(p - est_page))
            fig_by_page.setdefault(est_page, []).append(m)

    mismatches_log = []  # 记录无法解决的页

    mappings = []
    fig_counter = 0
    result_text = ocr_text
    total_shift = 0

    for page_num in sorted(set(list(fig_by_page.keys()) + list(img_by_page.keys()))):
        page_figs = fig_by_page.get(page_num, [])
        page_imgs = img_by_page.get(page_num, [])
        log(f"    第{page_num}页: {len(page_figs)}个[图]标记, {len(page_imgs)}张图片")

        # 核心判断：标记数与图片数是否一致
        n_figs = len(page_figs)
        n_imgs = len(page_imgs)

        if n_figs == n_imgs and n_figs > 0:
            # 一致 → 按顺序一一对应
            for idx, fm in enumerate(page_figs):
                fig_counter += 1
                matched = page_imgs[idx]
                conf = 0.85 if matched.source_type == "embedded" else 0.7
                mappings.append(ImageMapping(fig_index=str(fig_counter),
                    image=matched, confidence=conf, method="sequential"))
                adj_pos = fm.start() + total_shift
                result_text = result_text[:adj_pos] + f"[fig{fig_counter}]" + result_text[adj_pos + 3:]
                total_shift += len(str(fig_counter)) - 2
        elif n_figs == 0 and n_imgs > 0:
            # OCR未标出图片，但实际有图片 → 忽略
            log(f"    ⚠️ 第{page_num}页有{n_imgs}张图片但无[图]标记，跳过")
            mismatches_log.append(f"第{page_num}页有{n_imgs}张图片但无标记")
        elif n_figs > 0 and n_imgs == 0:
            # 有标记但无图片 → 全部标记为无图
            log(f"    ⚠️ 第{page_num}页有{n_figs}个[图]但无提取图片，跳过")
            for fm in page_figs:
                fig_counter += 1
                adj_pos = fm.start() + total_shift
                result_text = result_text[:adj_pos] + f"[fig{fig_counter}]" + result_text[adj_pos + 3:]
                total_shift += len(str(fig_counter)) - 2
                mappings.append(ImageMapping(fig_index=str(fig_counter),
                    image=None, confidence=0.1, method="no_image"))
            mismatches_log.append(f"第{page_num}页有{n_figs}个标记但无提取图片")
        else:
            # 数量不一致 → 调多模态视觉理解
            log(f"    🔍 第{page_num}页数量不一致({n_figs}标记 vs {n_imgs}图片)，启动视觉理解")
            match_result = _visual_match_page(page_num, page_figs, page_imgs,
                                              ocr_text, pdf_path, work_dir)
            for item in match_result:
                fig_counter += 1
                fig_idx = str(fig_counter)
                if item["image"] is not None:
                    mappings.append(ImageMapping(fig_index=fig_idx,
                        image=item["image"], confidence=item["confidence"],
                        method=item["method"]))
                else:
                    mappings.append(ImageMapping(fig_index=fig_idx,
                        image=None, confidence=0.1, method="no_image"))
                fm = item["match"]
                adj_pos = fm.start() + total_shift
                result_text = result_text[:adj_pos] + f"[fig{fig_idx}]" + result_text[adj_pos + 3:]
                total_shift += len(str(fig_idx)) - 2
            if item.get("unsolved"):
                mismatches_log.append(f"第{page_num}页: {item['reason']}")

    if mismatches_log:
        log(f"\n⚠️ 以下页面的图片匹配存在问题（已记录，继续处理）：")
        for m in mismatches_log:
            log(f"  - {m}")

    # 对有图但低置信度的做多模态校核
    for m in mappings:
        if 0.1 < m.confidence < 0.7 and m.image:
            new_conf = _multimodal_verify(m, result_text)
            if new_conf >= 0.9:
                m.confidence = new_conf
                m.method = "multimodal_verify"
                log(f"    ✅ 多模态校核通过: fig{m.fig_index} → {new_conf:.2f}")
            elif new_conf <= 0.3:
                log(f"    ⚠️ 多模态校核不匹配: fig{m.fig_index} → {new_conf:.2f}")

    return result_text, mappings


def _visual_match_page(page_num: int, fig_matches: list, page_imgs: list,
                        ocr_text: str, pdf_path: str,
                        work_dir: str = "/tmp/import_pipeline_v2") -> list:
    """当标记数与图片数不一致时，保存现场供AI视觉理解处理
    降级为顺序匹配，同时保存截图和上下文到mismatches目录
    返回[{"match": fm, "image": img|None, "confidence": float, "method": str, "unsolved": bool, "reason": str}]
    """
    # 从work_dir获取mismatches保存路径
    # work_dir 从参数传入，来自 run_pipeline
    mm_dir = os.path.join(work_dir, 'mismatches', f'page_{page_num:03d}')
    os.makedirs(mm_dir, exist_ok=True)

    # 1. 保存该页PDF截图
    doc = fitz.open(pdf_path)
    if page_num <= doc.page_count:
        pg = doc[page_num - 1]
        pix = pg.get_pixmap(dpi=200)
        screenshot_path = os.path.join(mm_dir, 'page_screenshot.png')
        pix.save(screenshot_path)
    doc.close()

    # 2. 保存提取的图片
    saved_img_paths = []
    for idx, img in enumerate(page_imgs):
        img_path = os.path.join(mm_dir, f'extracted_img_{idx+1}.png')
        if img.image_data:
            with open(img_path, 'wb') as f:
                f.write(img.image_data)
            saved_img_paths.append(img_path)

    # 3. 保存此页的文本上下文
    page_text = ""
    for fm in fig_matches:
        start = max(0, fm.start() - 150)
        end = min(len(ocr_text), fm.end() + 250)
        snippet = ocr_text[start:end]
        page_text += f"...{snippet}...\n"

    context_path = os.path.join(mm_dir, 'context.txt')
    with open(context_path, 'w', encoding='utf-8') as f:
        f.write(f"第{page_num}页 - 图片匹配冲突\n")
        f.write(f"[图]标记数: {len(fig_matches)}\n")
        f.write(f"提取图片数: {len(page_imgs)}\n\n")
        f.write(f"OCR上下文:\n{page_text}\n")
        f.write(f"提取的图片: {saved_img_paths}\n")

    log(f"    已保存到 {mm_dir}/")
    log(f"    请用视觉理解查看确认后手动修正")

    # 降级：按顺序匹配，标记低置信度
    result_items = []
    for i, fm in enumerate(fig_matches):
        if i < len(page_imgs):
            result_items.append({
                "match": fm,
                "image": page_imgs[i],
                "confidence": 0.5,
                "method": "sequential_fallback",
                "unsolved": True,
                "reason": f"第{page_num}页[图]标记({len(fig_matches)})≠图片数({len(page_imgs)}), 待视觉确认"
            })
        else:
            result_items.append({
                "match": fm,
                "image": None,
                "confidence": 0.1,
                "method": "sequential_fallback_overflow",
                "unsolved": True,
                "reason": f"第{page_num}页标记多于图片"
            })
    return result_items


def _multimodal_verify(mapping: ImageMapping, ocr_text: str) -> float:
    """多模态校核图片与上下文是否匹配"""
    tag = f"[fig{mapping.fig_index}]"
    pos = ocr_text.find(tag)
    if pos < 0:
        return mapping.confidence

    start = max(0, pos - 150)
    end = min(len(ocr_text), pos + 250)
    context = ocr_text[start:end]

    chat_url = f"{VOLC_BASE_URL}/api/v3/chat/completions"
    chat_headers = {"Authorization": f"Bearer {VOLC_API_KEY}",
                    "Content-Type": "application/json"}
    img_b64 = base64.b64encode(mapping.image.image_data).decode()
    data_uri = f"data:image/png;base64,{img_b64}"

    prompt = textwrap.dedent(f"""\
你是一位数学试卷质检员。

文本上下文（图片标记位置）：
```
{context}
```

请判断：上面这张图是否与该文本描述的图形/图表一致？
只输出一个词：OK / MISMATCH / UNCERTAIN""")

    payload = {
        "model": VOLC_MODEL,
        "messages": [
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": data_uri}},
                {"type": "text", "text": prompt}
            ]}
        ],
        "max_tokens": 10
    }
    try:
        result = retry_post(chat_url, headers=chat_headers,
                            json_data=payload, max_retries=2, timeout=60)
        ans = result["choices"][0]["message"]["content"].strip().upper()
        return 0.95 if ans == "OK" else (0.2 if ans == "MISMATCH" else 0.5)
    except Exception as e:
        log(f"    多模态校核失败: {e}")
        return mapping.confidence


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 5: 自动校验（阻塞式）
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationReport:
    passed: bool
    errors: List[str]
    warnings: List[str]
    question_reports: List[Dict[str, Any]]


def step5_validate(questions: List[dict], image_mappings: List[ImageMapping]) -> ValidationReport:
    """自动校验：格式检查 + 内容完整性，不通过则终止"""
    errors = []
    warnings = []
    q_reports = []
    all_fig_refs = set()
    img_indices = {m.fig_index for m in image_mappings}

    for i, q in enumerate(questions):
        q_errors = []
        q_warnings = []
        content = q.get("content", "")
        options = q.get("options", "")
        answer = q.get("answer", "")
        solution = q.get("solution", "")
        q_type = q.get("type", "")
        topic_id = q.get("topicId", "")

        # 1. content非空
        if not content or len(content.strip()) < 5:
            q_errors.append("content为空或过短")

        # 2. 收集[figN]引用
        for m in re.finditer(r'\[fig(\d+)\]', content + "\n" + solution):
            all_fig_refs.add(m.group(1))

        # 3. 题型特化校验
        if q_type in ("单选题",):
            lines = [l.strip() for l in options.split('\n') if l.strip()]
            letters = []
            for line in lines:
                mm = re.match(r'^([A-D])[.．、]', line)
                if mm:
                    letters.append(mm.group(1))
            if len(letters) < 4:
                q_errors.append(f"单选选项不足4个（{len(letters)}个）: {options[:60]}")
            if not answer:
                q_errors.append("缺少answer")
            elif not re.match(r'^[A-D]$', answer.strip()):
                q_warnings.append(f"answer格式非纯字母: {answer}")

        elif q_type in ("填空题",):
            if not answer:
                q_errors.append("填空缺少answer")

        elif q_type in ("解答题",):
            if not solution or len(solution.strip()) < 10:
                q_errors.append("解答题缺少solution或过短")

        # 4. topicId必须存在
        if not topic_id:
            q_warnings.append("topicId为空")

        q_reports.append({"index": i + 1, "type": q_type,
                          "errors": q_errors, "warnings": q_warnings})
        errors.extend(q_errors)
        warnings.extend(q_warnings)

    # 5. [figN]引用检查
    for fn in all_fig_refs:
        if fn not in img_indices:
            warnings.append(f"[fig{fn}] 引用不存在的图片（图片映射中无此编号）")

    # 6. 图片未被引用
    for im in image_mappings:
        if im.fig_index not in all_fig_refs and im.confidence > 0.5:
            warnings.append(f"图片{im.fig_index}未在文本中被引用")

    passed = len(errors) == 0
    report = ValidationReport(passed=passed, errors=errors,
                              warnings=warnings, question_reports=q_reports)

    log(f"【步骤5】校验结果:")
    ok = len([r for r in q_reports if not r['errors']])
    log(f"  通过 {ok}/{len(q_reports)} 题, 错误 {len(errors)}, 警告 {len(warnings)}")
    for e in errors:
        log(f"    ❌ {e}")
    for w in warnings[:8]:
        log(f"    ⚠️ {w}")

    return report


# ═══════════════════════════════════════════════════════════════════════════
#  步骤 6: 本地保存（JSON + SQLite）
#  图片以 base64 data URI 存入 image/answerImage 字段
# ═══════════════════════════════════════════════════════════════════════════

def step6_save_local(questions: List[dict], source: str,
                      image_mappings: List[ImageMapping],
                      work_dir: str) -> str:
    """保存结构化数据到本地JSON文件 + SQLite

    关键处理：
    1. [figN] 按题重排：每道题内的[figN]从1开始编号
    2. 图片字段用JSON数组格式存储，避免data URI中的逗号冲突
    3. 选择题答案从内容转为选项字母
    """
    records = []
    for i, q in enumerate(questions):
        content = q.get("content", "")
        solution = q.get("solution", "")
        answer = q.get("answer", "")
        options = q.get("options", "")
        q_type = q.get("type", "")

        # 收集该题中所有[figN]标记（按出现顺序）
        content_figs_raw = re.findall(r'\[fig(\d+)\]', content)
        solution_figs_raw = re.findall(r'\[fig(\d+)\]', solution)

        # 全局编号 → 题内编号映射
        ordered_raw = []
        seen = set()
        # 先content出现顺序，再solution
        for fn in content_figs_raw:
            if fn not in seen:
                seen.add(fn)
                ordered_raw.append(fn)
        for fn in solution_figs_raw:
            if fn not in seen:
                seen.add(fn)
                ordered_raw.append(fn)

        # 建立映射：全局编号 → 题内编号 (1-based)
        renumber_map = {}
        for new_idx, old_fn in enumerate(ordered_raw):
            renumber_map[old_fn] = new_idx + 1

        # 替换文本中的[figN]
        def renumber_text(text):
            if not text:
                return text
            result = text
            for old_fn, new_fn in sorted(renumber_map.items(), key=lambda x: -len(x[0])):
                result = result.replace(f'[fig{old_fn}]', f'[fig{new_fn}]')
            return result

        new_content = renumber_text(content)
        new_solution = renumber_text(solution)

        # 构建图片字段（JSON数组：第N个元素对应[figN]的图片）
        def fig_to_b64(fn):
            m = next((x for x in image_mappings if x.fig_index == fn), None)
            if m and m.image:
                return f"data:image/png;base64,{base64.b64encode(m.image.image_data).decode()}"
            return ""

        # 按题内编号顺序排列图片
        img_list = []
        ans_img_list = []
        for old_fn in content_figs_raw:
            if old_fn in renumber_map:
                new_fn = renumber_map[old_fn]
                b64 = fig_to_b64(old_fn)
                # 确保数组长度足够，有空位补空字符串
                while len(img_list) < new_fn:
                    img_list.append("")
                img_list[new_fn - 1] = b64
        for old_fn in solution_figs_raw:
            if old_fn in renumber_map:
                new_fn = renumber_map[old_fn]
                b64 = fig_to_b64(old_fn)
                while len(ans_img_list) < new_fn:
                    ans_img_list.append("")
                ans_img_list[new_fn - 1] = b64

        # 用JSON数组序列化（避免data URI中的逗号干扰）
        image_field = json.dumps(img_list, ensure_ascii=False)
        answer_image_field = json.dumps(ans_img_list, ensure_ascii=False)

        # 选择题答案：从内容匹配选项字母
        # 选项格式: "A. $1-2i$" → 去掉前缀字母+分隔符[.．、]和空格后得到内容
        new_answer = answer
        if q_type in ("单选题", "多选题") and options:
            ans_clean = re.sub(r'[\s\$]', '', answer)
            opt_lines = [l.strip() for l in options.split('\n') if l.strip()]
            matched = []
            for o in opt_lines:
                letter = o[0]
                # 去掉 "A. " 或 "A、" 或 "A．" 等前缀
                oc = re.sub(r'^[A-Da-d][.．、]\s*', '', o)
                oc_clean = re.sub(r'[\s\$]', '', oc)
                if ans_clean == oc_clean:
                    matched.append(letter)
            if len(matched) == 1:
                new_answer = matched[0]

        record = {
            "content": new_content,
            "options": options,
            "answer": new_answer,
            "solution": new_solution,
            "type": q_type,
            "difficulty": q.get("difficulty", "中等"),
            "source": source,
            "topicId": q.get("topicId", ""),
            "tags": f"number:{i+1}",
            "image": image_field,
            "answerImage": answer_image_field
        }
        records.append(record)

    # 保存JSON
    safe_name = source.replace(" ", "_").replace("（", "_").replace("）", "_")
    json_path = os.path.join(work_dir, f"{safe_name}_ready.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    log(f"【步骤6】JSON → {json_path} ({len(records)}条)")

    # 写入本地SQLite
    db_path = os.path.join(work_dir, f"{safe_name}_local.db")
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS questions_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, content TEXT, options TEXT,
                answer TEXT, answerImage TEXT, solution TEXT,
                image TEXT, difficulty TEXT, topicId TEXT,
                source TEXT, tags TEXT,
                createdAt TEXT, ext1 TEXT, ext2 TEXT
            )
        """)
        for rec in records:
            conn.execute("""
                INSERT INTO questions_v2
                (type, content, options, answer, answerImage, solution,
                 image, difficulty, topicId, source, tags, createdAt)
                VALUES (?,?,?,?,?,?,?,?,?,?,?, datetime('now'))
            """, (
                rec["type"], rec["content"], rec["options"],
                rec["answer"], rec["answerImage"], rec["solution"],
                rec["image"], rec["difficulty"], rec["topicId"],
                rec["source"], rec["tags"]
            ))
        conn.commit()
        conn.close()
        log(f"  SQLite → {db_path}")
    except Exception as e:
        log(f"  SQLite写入失败（JSON仍可用）: {e}")

    return json_path


# ═══════════════════════════════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════════════════════════════

def run_pipeline(pdf_path: str, source: str,
                 work_dir: str = "/tmp/import_pipeline") -> bool:
    log(f"{'='*60}")
    log(f"📚 开始导入: {source}")
    log(f"📄 PDF: {pdf_path}")
    log(f"📁 工作目录: {work_dir}")
    log(f"{'='*60}")

    os.makedirs(work_dir, exist_ok=True)
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0].replace(" ", "_")

    # ── 步骤0: PDF分片 ──
    parts_dir = os.path.join(work_dir, f"{pdf_name}_parts")
    parts = step0_split_pdf(pdf_path, parts_dir)

    # ── 步骤1: 多模态OCR ──
    log(f"\n{'─'*50}")
    log(f"【步骤1】多模态OCR → 纯文本 + [图]标记")
    ocr_dir = os.path.join(work_dir, f"{pdf_name}_ocr")
    merged_text = step1_ocr_all(parts, ocr_dir)

    # ── 步骤2: 图片提取 ──
    log(f"\n{'─'*50}")
    log(f"【步骤2】图片提取（嵌入式 + 矢量图）")
    img_dir = os.path.join(work_dir, f"{pdf_name}_images")
    images = step3_extract_images(pdf_path, img_dir)

    # ── 步骤3: 图片匹配 ──
    log(f"\n{'─'*50}")
    log(f"【步骤3】图片匹配 [图]→[figN]")
    marked_text, mappings = step4_match_images(merged_text, images, pdf_path, work_dir)
    marked_path = os.path.join(ocr_dir, "ocr_marked.txt")
    with open(marked_path, "w", encoding="utf-8") as f:
        f.write(marked_text)
    log(f"  标记后文本 → {marked_path}")

    # ── 步骤4: 结构化 ──
    log(f"\n{'─'*50}")
    log(f"【步骤4】结构化（已含 [figN] 标记）")
    questions = step2_structure_text(marked_text, source)
    if not questions:
        err("步骤4失败，终止")
        return False
    struct_path = os.path.join(work_dir, f"{pdf_name}_structured.json")
    with open(struct_path, "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    log(f"  结构化JSON → {struct_path}")

    # ── 步骤5: 自动校验 ──
    log(f"\n{'─'*50}")
    log(f"【步骤5】自动校验")
    report = step5_validate(questions, mappings)
    if not report.passed:
        err("校验未通过，终止")
        rpt_path = os.path.join(work_dir, f"{pdf_name}_validation.json")
        with open(rpt_path, "w", encoding="utf-8") as f:
            json.dump({
                "passed": False, "errors": report.errors,
                "warnings": report.warnings,
                "question_reports": report.question_reports
            }, f, ensure_ascii=False, indent=2)
        log(f"  校验报告 → {rpt_path}")
        return False

    # ── 步骤6: 本地保存 ──
    log(f"\n{'─'*50}")
    log(f"【步骤6】本地保存")
    json_path = step6_save_local(questions, source, mappings, work_dir)

    log(f"\n{'='*60}")
    log(f"🎉 流水线运行完成!")
    log(f"📄 最终数据: {json_path}")
    log(f"📁 中间产物: {work_dir}")
    log(f"  - OCR原始文本: {ocr_dir}/")
    log(f"  - 提取图片:    {img_dir}/")
    log(f"  - 结构化JSON:  {struct_path}")
    log(f"  - 带标记文本:  {marked_path}")
    log(f"请用户验证后，再决定是否导入云端")
    log(f"{'='*60}")
    return True


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="数学试卷批量导入流水线")
    parser.add_argument("--pdf", required=True, help="解析卷PDF路径")
    parser.add_argument("--source", default="未知来源", help="试卷来源标识")
    parser.add_argument("--work-dir", default="/tmp/import_pipeline", help="工作目录")
    args = parser.parse_args()

    run_pipeline(
        pdf_path=args.pdf,
        source=args.source,
        work_dir=args.work_dir
    )
