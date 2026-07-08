#!/usr/bin/env python3
"""
PDF解析卷 → 题库JSON 导入脚本
流程：切分PDF(2页重叠) → Files API上传 → Chat API识别 → 合并 → 知识点标注 → 输出JSON
"""

import sys, os, json, time, tempfile, re, argparse
import requests
import fitz  # PyMuPDF

# ─── 配置 ──────────────────────────────────────────────────
API_KEY = "ark-c966fdeb-e217-4092-8852-5688be15c6af-2f372"
API_BASE = "https://ark.cn-beijing.volces.com"
MODEL = "doubao-seed-2-0-mini-260428"

CHUNK_SIZE = 11        # 每部分页数
OVERLAP = 2             # 重叠页数
MAX_TOKENS = 32768      # 输出上限（模型支持的最大值）

# ─── 工具函数 ──────────────────────────────────────────────

def split_pdf(pdf_path, chunk_size=CHUNK_SIZE, overlap=OVERLAP):
    """将PDF拆分为两部分，每部分之间重叠 overlap 页"""
    doc = fitz.open(pdf_path)
    total = doc.page_count
    print(f"  [PDF] 总页数: {total}")

    parts = []
    # Part 1: 0 → chunk_size
    mid = chunk_size if chunk_size < total else total
    parts.append((0, mid))

    # Part 2: (mid - overlap) → total (至少保证1页内容)
    start2 = max(mid - overlap, 1)
    if start2 < total:
        parts.append((start2, total))

    result_paths = []
    for idx, (start, end) in enumerate(parts):
        part_doc = fitz.open()
        for i in range(start, end):
            part_doc.insert_pdf(doc, from_page=i, to_page=i)
        out_path = pdf_path.replace('.pdf', f'_part{idx+1}.pdf')
        if out_path == pdf_path:
            out_path = f'{pdf_path}_part{idx+1}.pdf'
        part_doc.save(out_path)
        part_doc.close()
        result_paths.append(out_path)
        print(f"  [SPLIT] Part{idx+1}: pages {start+1}-{end} → {out_path}")

    doc.close()
    return result_paths


def upload_file(file_path):
    """上传文件到火山引擎 Files API，返回 file_id"""
    url = f"{API_BASE}/api/v3/files"
    headers = {"Authorization": f"Bearer {API_KEY}"}

    with open(file_path, 'rb') as f:
        resp = requests.post(
            url, headers=headers,
            files={"file": (os.path.basename(file_path), f, "application/pdf")},
            data={"purpose": "user_data"},
            timeout=60
        )

    data = resp.json()
    if 'error' in data:
        raise Exception(f"Upload failed: {data['error']}")

    file_id = data['id']
    # 等待文件变为active
    for _ in range(10):
        time.sleep(2)
        status_resp = requests.get(
            f"{API_BASE}/api/v3/files/{file_id}",
            headers=headers,
            timeout=15
        )
        status_data = status_resp.json()
        if status_data.get('status') == 'active':
            print(f"  [UPLOAD] {os.path.basename(file_path)} → {file_id} (active)")
            return file_id
        elif status_data.get('status') == 'error':
            raise Exception(f"File processing error: {status_data}")

    raise Exception(f"File {file_id} did not become active in time")


def call_api(file_id, is_part2=False, previous_count=0):
    """调用Chat API识别PDF内容，返回JSON对象列表"""
    url = f"{API_BASE}/api/v3/chat/completions"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    if is_part2:
        system_prompt = (
            "这是2024年高考数学新课标I卷（解析卷）的下半部分。注意："
            "前一部分已经识别了上半部分的题目，请继续从上一部分未完成的题目开始识别。"
            "逐题输出JSON数组，确保与上半部分不重复、不遗漏。"
        )
    else:
        system_prompt = (
            "这是2024年高考数学新课标I卷（解析卷）的上半部分，请逐题识别。"
        )

    user_text = (
        "请逐题识别，输出为JSON数组。规则：\n"
        "1) 所有数学公式用标准LaTeX，inline用\\(...\\)\n"
        "2) type: 单选题|多选题|填空题|解答题\n"
        "3) difficulty: 基础|中等|困难\n"
        "4) content: 题干全文（含选项，公式用LaTeX）\n"
        "5) solution: 【答案】...\\n【解析】...（含【点睛】）\n"
        "6) tags: [\"number:X\"] 标注题号\n\n"
        "只输出纯JSON数组，不要markdown代码块：\n"
        '[{"type":"...","difficulty":"...","content":"...","solution":"...","tags":["number:X"]}]'
    )

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "file", "file": {"file_id": file_id}},
                    {"type": "text", "text": system_prompt + "\n\n" + user_text}
                ]
            }
        ],
        "max_tokens": MAX_TOKENS
    }

    print(f"  [API] 调用模型识别... (max_tokens={MAX_TOKENS})")
    start = time.time()
    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    elapsed = time.time() - start
    data = resp.json()

    if 'error' in data:
        raise Exception(f"API error: {data['error']}")

    usage = data.get('usage', {})
    det = usage.get('completion_tokens_details', {})
    print(f"  [API] 耗时: {elapsed:.1f}s, "
          f"input_tokens={usage.get('prompt_tokens')}, "
          f"output_tokens={usage.get('completion_tokens')}, "
          f"reasoning_tokens={det.get('reasoning_tokens', 0)}")

    content = data['choices'][0]['message']['content']

    # 提取JSON数组
    content = content.strip()
    # 去掉可能的 markdown 包裹
    if content.startswith('```'):
        content = re.sub(r'^```(?:json)?\s*', '', content)
        content = re.sub(r'\s*```$', '', content)

    try:
        questions = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  [ERROR] JSON解析失败: {e}")
        print(f"  [ERROR] 原始内容前500字符: {content[:500]}")
        # 尝试提取方括号内的内容
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            try:
                questions = json.loads(match.group())
            except:
                raise
        else:
            raise

    print(f"  [API] 识别到 {len(questions)} 道题")
    return questions


def add_knowledge_tags(questions, subject="math"):
    """为题目添加知识点标签（基于规则匹配的简化版）"""
    # TODO: 后续接入更完善的知识点匹配
    # 目前先标一个默认章节，后续根据题目内容匹配知识树
    for q in questions:
        if 'tags' not in q:
            q['tags'] = []
    return questions


def merge_parts(part1, part2):
    """合并两个part的题目，去重"""
    seen_numbers = set()
    merged = []

    for q in part1 + part2:
        # 提取题号
        numbers = [t for t in q.get('tags', []) if t.startswith('number:')]
        if numbers:
            num = int(numbers[0].split(':')[1])
        else:
            num = None

        # 如果题号已存在，跳过（保留第一个出现的版本）
        if num is not None:
            if num in seen_numbers:
                print(f"  [MERGE] 跳过重复题号: {num}")
                continue
            seen_numbers.add(num)

        merged.append(q)

    # 按题号排序
    def sort_key(q):
        nums = [t for t in q.get('tags', []) if t.startswith('number:')]
        if nums:
            return int(nums[0].split(':')[1])
        return 999

    merged.sort(key=sort_key)
    print(f"  [MERGE] 合并后共 {len(merged)} 道题")
    return merged


def process_pdf(pdf_path, output_path=None):
    """处理单个PDF解析卷，输出可入库的JSON"""
    basename = os.path.basename(pdf_path)
    year_match = re.search(r'(\d{4})', basename)
    year = year_match.group(1) if year_match else "unknown"

    print(f"\n{'='*60}")
    print(f"处理: {basename} (年份: {year})")
    print(f"{'='*60}")

    # Step 1: 切分PDF
    print("\n[Step 1] 切分PDF...")
    parts = split_pdf(pdf_path)

    # Step 2: 上传
    print("\n[Step 2] 上传到Files API...")
    file_ids = []
    for p in parts:
        fid = upload_file(p)
        file_ids.append(fid)

    # Step 3: 调用API识别
    print("\n[Step 3] 调用Chat API...")
    all_questions = []
    for idx, fid in enumerate(file_ids):
        is_part2 = (idx > 0)
        questions = call_api(fid, is_part2=is_part2)
        all_questions.append(questions)

    # Step 4: 合并
    print("\n[Step 4] 合并题目...")
    if len(all_questions) > 1:
        questions = merge_parts(all_questions[0], all_questions[1])
    else:
        questions = all_questions[0]

    # Step 5: 知识点标注
    print("\n[Step 5] 知识点标注...")
    questions = add_knowledge_tags(questions)

    # Step 6: 输出
    if output_path is None:
        output_path = pdf_path.replace('.pdf', '_questions.json')

    result = {
        "source": basename,
        "year": year,
        "total_questions": len(questions),
        "questions": questions
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ 完成! 共 {len(questions)} 道题")
    print(f"   输出: {output_path}")
    print(f"{'='*60}")

    return questions


# ─── 主入口 ────────────────────────────────────────────────

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PDF解析卷 → 题库JSON')
    parser.add_argument('pdf', help='PDF文件路径')
    parser.add_argument('-o', '--output', help='输出JSON路径（默认替换.pdf为_questions.json）')
    args = parser.parse_args()

    process_pdf(args.pdf, args.output)
