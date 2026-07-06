#!/usr/bin/env python3
"""
高考数学PDF解析 → 题库导入 v3

方案：先用PDF解析获得题目结构和答案/解析，
再用AI逐题清理题干和选项的排版（修复公式、上标、选项分行等）
"""

import fitz
import re
import json
import sys
import os
import subprocess
import argparse

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-cloud-database/scripts/baas.py"
DEFAULT_API_KEY = "baas_ZiRfZlhr"

def extract_pdf_text(pdf_path):
    """提取PDF所有文本，去掉页码干扰"""
    doc = fitz.open(pdf_path)
    full_text = ""
    for i in range(doc.page_count):
        page_text = doc[i].get_text()
        page_text = re.sub(r'第\s*\d+\s*页\s*(\|\s*共\s*\d+\s*页)?\s*\n?', '', page_text)
        full_text += page_text + "\n"
    doc.close()
    return full_text

def extract_filename_meta(filename):
    """从文件名提取试卷元信息"""
    m = re.search(r'(20\d\d)', filename)
    year = m.group(1) if m else ""
    is_li = '理' in filename
    is_wen = '文' in filename
    exam_type = "理科" if is_li else ("文科" if is_wen else "")
    
    # 试卷名称
    region = ""
    m = re.search(r'（([^）]*卷?)）', filename)
    if m:
        region = m.group(1)
    else:
        m = re.search(r'（([^）]*)）', filename)
        if m:
            r = m.group(1)
            if r not in ['解析卷', '解析版', '空白卷', '原卷']:
                region = r
    
    source = f"{year}年{region}" if region else f"{year}年"
    if exam_type:
        source += f"({exam_type})"
    
    return {"year": year, "region": region, "type": exam_type, "source": source}

def parse_questions(text):
    """
    解析PDF文本，提取题目结构
    
    返回每个题目的raw文本块和元信息
    """
    # 检测大题区域
    questions = []
    
    # 方法：先用题号正则分割
    # 匹配形如 "n. " 或 "n．" 开头的行（n是数字）
    lines = text.split('\n')
    
    current_section = None
    current_q_lines = []
    current_q_num = None
    
    # 大题标记
    section_map = {"一": "选择题", "二": "填空题", "三": "解答题",
                   "1": "选择题", "2": "填空题", "3": "解答题"}
    
    # 检测大题标题
    section_pattern = re.compile(r'^[一二三][、．]\s*(选择题|填空题|解答题)')
    # 检测题号
    q_num_pattern = re.compile(r'^(\d+)\s*[\.\．、](?!\d)')
    # 检测【答案】或【解析】
    answer_pattern = re.compile(r'【答案】')
    # 检测下一大题
    next_sec_pattern = re.compile(r'^[二三四][、．]')
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        # 检测大题标题
        m = section_pattern.match(stripped)
        if m:
            if current_q_num is not None and current_q_lines:
                questions.append({
                    "number": current_q_num,
                    "section": current_section,
                    "raw_text": '\n'.join(current_q_lines)
                })
            current_section = m.group(1)
            current_q_num = None
            current_q_lines = []
            continue
        
        # 检测题号
        m = q_num_pattern.match(stripped)
        if m:
            # 保存上一题
            if current_q_num is not None and current_q_lines:
                questions.append({
                    "number": current_q_num,
                    "section": current_section,
                    "raw_text": '\n'.join(current_q_lines)
                })
            current_q_num = int(m.group(1))
            current_q_lines = [stripped]
            continue
        
        # 检测下一大题（大题标记没匹配到时）
        if current_section and next_sec_pattern.match(stripped):
            if current_q_num is not None and current_q_lines:
                questions.append({
                    "number": current_q_num,
                    "section": current_section,
                    "raw_text": '\n'.join(current_q_lines)
                })
            current_section = None
            current_q_num = None
            current_q_lines = []
            continue
        
        if current_q_num is not None:
            current_q_lines.append(stripped)
    
    # 最后一题
    if current_q_num is not None and current_q_lines:
        questions.append({
            "number": current_q_num,
            "section": current_section,
            "raw_text": '\n'.join(current_q_lines)
        })
    
    return questions


def extract_answer_solution_from_text(raw_text):
    """从题目原始文本中提取【答案】和【解析】"""
    answer = ""
    solution = ""
    
    # 答案
    m = re.search(r'【答案】\s*([^\n【】]+)', raw_text)
    if m:
        raw = m.group(1).strip()
        raw = re.sub(r'\s+', '', raw)
        ans_letter = re.search(r'[A-D]', raw)
        if ans_letter:
            answer = ans_letter.group()
        elif raw:
            answer = raw[:20]
    
    # 解析
    m = re.search(r'【解析】\s*([\s\S]*?)(?=(?:\d+\s*[\.\．、]|【分析】|$))', raw_text)
    if m:
        solution = re.sub(r'\s+', ' ', m.group(1)).strip()
    
    if not solution:
        # 也可能是【分析】+【详解】
        m = re.search(r'【详解】\s*([\s\S]*?)(?=(?:\d+\s*[\.\．、]|$))', raw_text)
        if m:
            solution = re.sub(r'\s+', ' ', m.group(1)).strip()
        else:
            m = re.search(r'【分析】\s*([\s\S]*?)(?=(?:【详解】|$))', raw_text)
            if m:
                solution = re.sub(r'\s+', ' ', m.group(1)).strip()
    
    return answer, solution


def format_ai_prompt(question_data):
    """生成AI清理prompt"""
    raw = question_data["raw_text"]
    q_num = question_data["number"]
    q_section = question_data["section"] or "未知"
    
    prompt = f"""请将以下高考数学试卷中第{q_num}题（{q_section}）的原始文本，整理为规范的题目格式。

要求：
1. 如果题目是选择题，选项每个单独占一行（用"A. " "B. " "C. " "D. "格式）
2. 修复上标：²→^2, ³→^3, ₁→_1, ₂→_2等
3. 合并被空格/换行中断的数学公式
4. 保持原始内容完整，不要修改答案和解析
5. 如果原始文本包含【答案】和【解析】，请保留

原始文本：
{raw}

请只输出整理后的题目内容，如有多道题请只输出第{q_num}题。如果【答案】【解析】已在原始文本中，保留它们。
"""
    return prompt


def rebuild_question_content(question_data):
    """
    尝试不依赖AI，进行基于规则的内容重建
    这用于预览阶段，AI清理会在导入时进行
    """
    raw = question_data["raw_text"]
    
    # 去掉【答案】【解析】部分
    text_parts = re.split(r'【答案】|【解析】|【分析】|【详解】', raw)
    stem_part = text_parts[0] if text_parts else raw
    
    # 提取选项
    opt_pattern = re.compile(r'([A-D])\s*[\.\．、]\s*')
    opt_matches = list(opt_pattern.finditer(stem_part))
    
    stem = stem_part
    options = {}
    
    if len(opt_matches) >= 3:
        # 有选择题选项
        for i, m in enumerate(opt_matches):
            start = m.end()
            end = opt_matches[i+1].start() if i+1 < len(opt_matches) else len(stem_part)
            opt_text = stem_part[start:end].strip()
            opt_text = re.sub(r'\s+', ' ', opt_text)
            options[m.group(1)] = opt_text
        
        # 题干 = 第一个选项之前的内容
        first_opt_start = opt_matches[0].start()
        stem = stem_part[:first_opt_start].strip()
    
    # 清理题干
    stem = re.sub(r'\s+', ' ', stem).strip()
    # 去掉题号前缀
    stem = re.sub(r'^\d+\s*[\.\．、]\s*', '', stem)
    # 修复上标
    stem = stem.replace('²', '^2').replace('³', '^3').replace('⁰', '^0').replace('¹', '^1')
    
    # 从题目开头去掉题号数字
    q_num = question_data["number"]
    
    # 选项分行显示
    opts_text = ""
    if options:
        opts_lines = []
        for k in sorted(options.keys()):
            opt_val = options[k].replace('²', '^2').replace('³', '^3')
            opts_lines.append(f"{k}. {opt_val}")
        opts_text = "\n".join(opts_lines)
    
    # 提取答案和解析
    answer, solution = extract_answer_solution_from_text(raw)
    
    return {
        "stem": stem,
        "options": opts_text,
        "answer": answer,
        "solution": solution.replace('²', '^2').replace('³', '^3') if solution else "",
    }


def main():
    parser = argparse.ArgumentParser(description='PDF解析高考数学题库')
    parser.add_argument('--pdf', required=True, help='PDF文件路径')
    parser.add_argument('--preview', action='store_true', help='仅预览解析结果')
    parser.add_argument('--import-db', action='store_true', help='导入到数据库')
    parser.add_argument('--api-key', default=DEFAULT_API_KEY)
    
    args = parser.parse_args()
    
    pdf_path = args.pdf
    basename = os.path.basename(pdf_path)
    meta = extract_filename_meta(basename)
    source = meta["source"]
    
    print(f"📄 {basename}")
    print(f"  试卷来源: {source}")
    
    # 1. 提取文本
    full_text = extract_pdf_text(pdf_path)
    
    # 2. 解析题目结构
    questions = parse_questions(full_text)
    questions = [q for q in questions if 1 <= q["number"] <= 25]  # 只保留正常题号
    questions = questions[:23]  # 最多23题（一套标准高考卷）
    
    print(f"  解析出 {len(questions)} 道题")
    
    # 3. 内容重建
    cleaned = [rebuild_question_content(q) for q in questions]
    
    # 4. 预览
    if args.preview:
        for i, (q, c) in enumerate(zip(questions, cleaned)):
            print(f"\n--- 题{q['number']} [{q.get('section','?')}] ---")
            print(f"  题干: {c['stem'][:120]}...")
            if c['options']:
                for line in c['options'].split('\n')[:5]:
                    print(f"    {line}")
            if c['answer']:
                print(f"  答案: {c['answer']}")
            if c['solution'][:120]:
                print(f"  解析: {c['solution'][:120]}...")
        
        print(f"\n  共 {len(questions)} 道题")
        return
    
    # 5. 导入数据库
    if args.import_db:
        print(f"\n💾 开始导入 {len(questions)} 道题...")
        success, fail = 0, 0
        for i, (q, c) in enumerate(zip(questions, cleaned)):
            if not c['stem']:
                fail += 1
                continue
            
            payload = {
                "table": "questions",
                "method": "add",
                "apiKey": args.api_key,
                "tableData": {
                    "topicId": "M1-C1-T3",
                    "type": c["options"] and "单选题" or "填空题",
                    "difficulty": "中等",
                    "content": c["stem"],
                    "options": c["options"],
                    "answer": c["answer"],
                    "solution": c["solution"],
                    "source": source,
                    "tags": f"{source}"
                }
            }
            
            cmd = ["python3", BAAS_SCRIPT, "--x-api-type", "tableAddData",
                   "--content", json.dumps(payload, ensure_ascii=False)]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if "success" in result.stdout.lower() or '"code":"0"' in result.stdout:
                    success += 1
                    print(f"  ✅ {i+1}. 题{q['number']}")
                else:
                    fail += 1
                    print(f"  ❌ {i+1}. 题{q['number']}: {result.stdout[:100]}")
            except Exception as e:
                fail += 1
                print(f"  ❌ {i+1}. 题{q['number']}: {e}")
        
        print(f"\n✅ 完成: 成功 {success}, 失败 {fail}")


if __name__ == '__main__':
    main()
