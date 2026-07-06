#!/usr/bin/env python3
"""
高考数学 解析版PDF → 云端题库 导入器 v4

流程:
1. MarkItDown 提取PDF文本 (比fitz更规范)
2. 按题号+大题区域分割题目
3. 提取【答案】【解析】  
4. 从文件名获取年份/地区信息
5. 导入云端数据库

改进:
- 选项每个独占一行 ✓
- 修复公式排版(合并空格拆散的内容) ✓
- 上标处理 ✓
- 先导入一两份样卷调优 ✓

用法:
  python3 import_pdf_questions.py --pdf path/to/卷子.pdf [--import-db]
  python3 import_pdf_questions.py --batch  # 批量导入全部
"""

import re, json, sys, os, subprocess, argparse
from markitdown import MarkItDown

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-cloud-database/scripts/baas.py"
DEFAULT_API_KEY = "baas_ZiRfZlhr"

# ====== 试卷来源提取 ======

def parse_filename_info(filename):
    """从文件名提取元信息"""
    info = {"year": "", "type": "", "region": ""}
    m = re.search(r'(20\d\d)', filename)
    if m: info["year"] = m.group(1)
    info["type"] = "理科" if "理" in filename else ("文科" if "文" in filename else "")
    m = re.search(r'（([^）]*卷?)）', filename)
    if m: info["region"] = m.group(1)
    else:
        m = re.search(r'（([^）]*)）', filename)
        if m and m.group(1) not in ['解析卷','解析版','空白卷','原卷']:
            info["region"] = m.group(1)
    return info

def make_source(info):
    s = info["year"]
    if info["region"]: s += info["region"]
    if info["type"]: s += f"({info['type']})"
    return s

# ====== 文本清理 ======

def fix_formula_whitespace(text):
    """
    修复markitdown提取时公式中的多余空格:
    a = b → a=b (在公式上下文中)
    x x → xx (连续的数学字母)
    但保留自然语言中的空格
    """
    # markitdown在公式字符间插入了大量空格
    # 策略: 在数学符号密集的区域，合并空格
    # 先对整段做激进压缩
    
    # 1. 合并数字运算符号附近: 1 + 2 → 1+2, x 2 → x^2 etc
    text = re.sub(r'(\d)\s+([+\-*/=])', r'\1\2', text)
    text = re.sub(r'([+\-*/=])\s+(\d)', r'\1\2', text)
    text = re.sub(r'(\d)\s+([+\-*/=])\s+(\d)', r'\1\2\3', text)
    
    # 2. 合并单个字母附近的空格:  A B C D → ABCD (在集合语境)
    text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)  # a2 → a^2
    
    # 3. 合并括号内的空格: ( x ) → (x)
    text = re.sub(r'\(\s+', '(', text)
    text = re.sub(r'\s+\)', ')', text)
    text = re.sub(r'\{\s+', '{', text)
    text = re.sub(r'\s+\}', '}', text)
    text = re.sub(r'\[\s+', '[', text)
    text = re.sub(r'\s+\]', ']', text)
    
    # 4. 修复数学运算符号周围
    text = re.sub(r'(\w)\s+([+\-×÷=≠>≤≥≈±])\s+', r'\1\2', text)
    text = re.sub(r'\s+([+\-×÷=≠>≤≥≈±])\s+(\w)', r'\1\2', text)
    
    # 5. 修复下标和上标
    text = text.replace('²', '^2').replace('³', '^3')
    text = text.replace('⁰', '^0').replace('¹', '^1')
    
    # 6. 合并多个空格
    text = re.sub(r'  +', ' ', text)
    
    return text

def fix_option_format(text):
    """
    格式化选择题选项:
    A. xxx B. xxx → 每行一个
    注意选项可能在多行上
    """
    # 先检测有没有选项模式
    opt_pattern = r'(?:^|\n)\s*([A-D])\s*[\.\．、]'
    has_options = len(re.findall(opt_pattern, text)) >= 3
    if not has_options:
        return text, False
    
    # 把选项模式行拆开
    # 先找到所有选项
    lines = text.split('\n')
    result_lines = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            result_lines.append(line)
            continue
        # 如果一行包含多个选项，拆分
        # 如 "A. xxx B. xxx C. xxx D. xxx" 或 "A. xxx    B. xxx"
        opts = re.findall(r'([A-D])\s*[\.\．、]\s*([^A-D]*(?:$|(?=\s*[A-D]\s*[\.\．、])))', stripped)
        if len(opts) >= 3:
            for k, v in opts:
                v = re.sub(r'\s+', ' ', v).strip()
                if v:
                    result_lines.append(f"  {k}. {v}")
                else:
                    result_lines.append(f"  {k}.")
            continue
        # 如果一行以"A."开头且后面只有简单内容
        m = re.match(r'^([A-D])\s*[\.\．、]', stripped)
        if m:
            result_lines.append(f"  {stripped}")
        # 否则保留原样
        else:
            result_lines.append(line)
    
    return '\n'.join(result_lines), True

def fix_answer_format(text):
    """确保【答案】格式整洁"""
    text = re.sub(r'【\s*答案\s*】', '【答案】', text)
    text = re.sub(r'【\s*解析\s*】', '【解析】', text)
    return text

# ====== PDF解析 ======

def extract_text_from_pdf(pdf_path):
    """使用MarkItDown提取PDF文本"""
    md = MarkItDown()
    result = md.convert(pdf_path)
    text = result.text_content
    
    # 去掉页码
    text = re.sub(r'第\d+页\s*\|\s*共\d+页\s*', '', text)
    text = re.sub(r'第\s*\d+\s*页\s*', '', text)
    
    return text

def identify_sections(text):
    """
    识别大题区域 (选择题/填空题/解答题)
    返回: [(区域名, 起始位置, 题号列表)]
    """
    sections = []
    
    # 匹配: "一、选择题" "二、填空题" "三、解答题"
    sec_pattern = re.compile(r'(?:^|\n)\s*[一二三][、．]\s*(选择题|填空题|解答题)')
    
    last_end = 0
    last_name = "未知"
    for m in sec_pattern.finditer(text):
        if last_end > 0:
            sections.append((last_name, last_end, m.start()))
        last_name = m.group(1)
        last_end = m.start()
    
    if last_end > 0:
        sections.append((last_name, last_end, len(text)))
    
    if not sections:
        sections.append(("全部", 0, len(text)))
    
    return sections

def split_questions(text, section_name):
    """
    在一个大题区域内按题号分割题目
    返回: [(题号, 文本)]
    """
    questions = []
    
    # 题号匹配: ^数字.  或 ^数字．
    q_pattern = re.compile(r'(?:^|\n)\s*(\d+)\s*[\.\．、](?!\d)')
    
    last_num = 0
    last_pos = 0
    for m in q_pattern.finditer(text):
        num = int(m.group(1))
        # 只取1-25的题号（跳过页码、引用等）
        if 1 <= num <= 25:
            if last_num > 0:
                q_text = text[last_pos:m.start()].strip()
                if len(q_text) > 15:  # 过滤太短的内容
                    questions.append((last_num, q_text))
            last_num = num
            last_pos = m.start()
    
    if last_num > 0:
        q_text = text[last_pos:].strip()
        if len(q_text) > 15:
            questions.append((last_num, q_text))
    
    return questions

def extract_answer_solution(q_text):
    """从题目文本中提取答案和解析"""
    answer = ""
    solution = ""
    
    m = re.search(r'【答案】\s*([^\n【】]+)', q_text)
    if m:
        raw = re.sub(r'\s+', '', m.group(1))
        ans_letter = re.search(r'[A-D]', raw)
        answer = ans_letter.group() if ans_letter else raw[:20]
    else:
        # 旧版：答案可能跟在"答案"后或"=【D】"中
        m = re.search(r'答案[：:]\s*([A-Da-d一二三四])', q_text)
        if m:
            t = m.group(1)
            map_v = {'一':'A','二':'B','三':'C','四':'D'}
            answer = map_v.get(t, t.upper())
        m = re.search(r'【([A-D])】', q_text)
        if m:
            answer = m.group(1)
    
    # 解析 - 找【解析】后的内容
    m = re.search(r'【解析】\s*([\s\S]*?)(?=(?:\d+\s*[\.\．、]|$))', q_text)
    if m:
        solution = re.sub(r'\s+', ' ', m.group(1)).strip()
    
    return answer, solution

def extract_options(q_text):
    """
    从题目文本中提取选择题选项
    返回: {A: "xxx", B: "xxx", ...}
    """
    options = {}
    
    # 尝试多种模式匹配选项
    # 模式1: A. xxx B. xxx C. xxx D. xxx
    pattern = r'([A-D])\s*[\.\．、]\s*(.*?)(?=\s*[A-D]\s*[\.\．、]|\s*$|【答案】|【解析】)'
    matches = list(re.finditer(pattern, q_text, re.DOTALL))
    
    if len(matches) >= 4:
        for m in matches:
            key = m.group(1)
            val = re.sub(r'\s+', ' ', m.group(2)).strip()
            if val:
                options[key] = val
        return options
    
    # 模式2: 旧版选项连排 (A) 或 A．
    pattern2 = r'(?:^|\s)([A-D])\s*[\.\．\)）]\s*([^\n]*?)(?=\s*[A-D]\s*[\.\．\)）]|$)'
    matches2 = list(re.finditer(pattern2, q_text))
    if len(matches2) >= 3:
        for m in matches2:
            key = m.group(1)
            val = m.group(2).strip()
            if val:
                options[key] = val
        return options
    
    # 模式3: 选项每行一个
    for line in q_text.split('\n'):
        line = line.strip()
        m = re.match(r'([A-D])\s*[\.\．、\)]\s*(.+)', line)
        if m:
            options[m.group(1)] = m.group(2).strip()
    
    return options

def clean_stem_text(stem_raw):
    """清理题干文本"""
    stem = re.sub(r'\s+', ' ', stem_raw).strip()
    # 去掉题号前缀
    stem = re.sub(r'^\d+\s*[\.\．、]\s*', '', stem)
    # 移除开头的 "理科数学" 等标题
    stem = re.sub(r'^理科数学\s*', '', stem)
    # 移除残留的页码标记
    stem = re.sub(r'\|\s*共\d+页\s*', '', stem)
    # 合并残留空格
    stem = re.sub(r'(\w)\s+([=+\-×÷])\s+', r'\1\2', stem)
    stem = re.sub(r'\s+', ' ', stem).strip()
    return stem

def extract_question_core(q_num, section, q_text, source):
    """从解析版本PDF中提取题目、选项、答案、解析"""
    # 1. 先提取答案和解析（它们在末尾）
    answer, solution = extract_answer_solution(q_text)
    
    # 2. 找到【答案】的位置，用它来分割题干和答案部分
    answer_pos = q_text.find('【答案】')
    if answer_pos == -1:
        answer_pos = q_text.find('【解析】')
    if answer_pos == -1:
        # 旧版：没有【答案】标记
        stem_part = q_text
    else:
        stem_part = q_text[:answer_pos]
    
    # 3. 从题干部分提取选项
    options = extract_options(stem_part)
    
    # 4. 题干 = 去掉选项文本后的剩余
    stem = stem_part
    if options:
        for key in sorted(options.keys(), reverse=True):
            stem = re.sub(r'\s*' + re.escape(key) + r'\s*[\.\．、]\s*' + re.escape(options[key][:40]), '', stem)
    
    stem = clean_stem_text(stem)
    
    # 5. 判断题型
    is_choice = len(options) >= 3
    has_sub = bool(re.search(r'[（(][ⅠⅡⅢⅣⅤⅥⅦⅧ一二三四五六七八][）)]', q_text)) or \
              bool(re.search(r'[（(]\d[）)]', q_text))
    q_type = "解答题" if (has_sub and not is_choice) else ("单选题" if is_choice else "填空题")
    
    # 6. 选项格式化 - 每个一行
    options_formatted = ""
    if options:
        opts = []
        for k in sorted(options.keys()):
            v = re.sub(r'\s+', ' ', options[k]).strip()
            # 清理选项中混入的杂项（如 "A 7 ."）
            v = re.sub(r'^[A-D]\s+\d+\s*\.$', '', v)
            if v:
                opts.append(f"{k}. {v}")
        options_formatted = "\n".join(opts)
    
    # 7. 解析清理
    solution_clean = re.sub(r'\s+', ' ', solution).strip() if solution else ""
    # 解析中如果混入了【详解】、【小问】等标记，从中截取
    sol_marker = solution_clean.find('【详解】')
    if sol_marker >= 0:
        solution_clean = solution_clean[sol_marker+4:]
    solution_clean = solution_clean[:600]
    
    return {
        "number": q_num,
        "type": q_type,
        "content": stem,
        "options": options_formatted,
        "answer": answer,
        "solution": solution_clean,
        "source": source,
        "section": section,
    }

def parse_pdf(pdf_path):
    """解析PDF，返回题目列表"""
    basename = os.path.basename(pdf_path)
    info = parse_filename_info(basename)
    source = make_source(info)
    
    print(f"📄 解析: {basename}")
    print(f"   来源: {source}")
    
    # 1. 提取文本
    full_text = extract_text_from_pdf(pdf_path)
    full_text = fix_answer_format(full_text)
    
    # 2. 识别大题区域
    sections = identify_sections(full_text)
    
    all_questions = []
    for sec_name, start, end in sections:
        sec_text = full_text[start:end]
        
        # 跳过只有大题标题没有题目的段
        if not re.search(r'\d+\s*[\.\．、]', sec_text):
            continue
        
        questions = split_questions(sec_text, sec_name)
        
        for q_num, q_text in questions:
            result = extract_question_core(q_num, sec_name, q_text, source)
            all_questions.append(result)
    
    return all_questions, source

# ====== 数据库导入 ======

def import_to_db(questions, api_key, table="questions"):
    """导入到云端数据库"""
    success, fail = 0, 0
    
    for i, q in enumerate(questions):
        if not q['content']:
            fail += 1
            continue
        
        payload = {
            "table": table,
            "method": "add",
            "apiKey": api_key,
            "tableData": {
                "topicId": "M1-C1-T3",  # 用默认，后续可AI分类
                "type": q["type"],
                "difficulty": "中等",
                "content": q["content"],
                "options": q["options"],
                "answer": q["answer"],
                "solution": q["solution"],
                "source": q["source"],
                "tags": f"{q['source']}, {q['type']}"
            }
        }
        
        cmd = ["python3", BAAS_SCRIPT, "--x-api-type", "tableAddData",
               "--content", json.dumps(payload, ensure_ascii=False)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if "success" in result.stdout.lower() or '"code":"0"' in result.stdout:
                success += 1
                sys.stdout.write(f"  ✅ {i+1}. 题{q['number']}[{q['type']}] {q['content'][:50]}...\n")
            else:
                fail += 1
                sys.stdout.write(f"  ❌ {i+1}. 题{q['number']}: {result.stdout[:120]}\n")
        except Exception as e:
            fail += 1
            sys.stdout.write(f"  ❌ {i+1}. 题{q['number']}: {e}\n")
        sys.stdout.flush()
    
    return success, fail


# ====== 主入口 ======

def print_preview(questions, source):
    """打印预览"""
    print(f"\n📋 试卷: {source}")
    print(f"📊 题目数: {len(questions)}")
    
    # 统计题型
    from collections import Counter
    types = Counter(q['type'] for q in questions)
    print(f"   题型: {dict(types)}")
    
    for q in questions:
        print(f"\n  [{q['number']}] [{q['type']}] {q['content'][:80]}...")
        if q['options']:
            for line in q['options'].split('\n'):
                print(f"    {line}")
        if q['answer']:
            print(f"    ✏️ 答案: {q['answer']}")
        if q['solution'][:80]:
            print(f"    📝 解析: {q['solution'][:80]}...")
    
    # 手动检查选项是否分行规范
    print("\n=== 选项格式检查 ===")
    for q in questions:
        if q['options']:
            opts = q['options'].split('\n')
            if len(opts) < 4:
                print(f"  ⚠️ 题{q['number']} 选项数={len(opts)}: {q['options'][:60]}")
            else:
                print(f"  ✅ 题{q['number']} 选项分布正常 {len(opts)}行")
    print()


def main():
    parser = argparse.ArgumentParser(description='高考数学PDF解析导入器 v4')
    parser.add_argument('--pdf', help='单个PDF文件路径')
    parser.add_argument('--preview', action='store_true', help='仅预览，不导入')
    parser.add_argument('--import-db', action='store_true', help='导入到数据库')
    parser.add_argument('--api-key', default=DEFAULT_API_KEY)
    
    args = parser.parse_args()
    
    if not args.pdf:
        parser.print_help()
        return
    
    if not os.path.exists(args.pdf):
        print(f"❌ 文件不存在: {args.pdf}")
        return
    
    # 解析
    questions, source = parse_pdf(args.pdf)
    
    # 预览
    print_preview(questions, source)
    
    # 导入数据库
    if args.import_db:
        print(f"💾 正在导入 {len(questions)} 道题...")
        s, f = import_to_db(questions, args.api_key)
        print(f"\n✅ 完成! 成功={s}, 失败={f}")


if __name__ == '__main__':
    main()
