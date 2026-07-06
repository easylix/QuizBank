#!/usr/bin/env python3
"""
高考数学PDF解析版 → 题库导入脚本 v2

改进点：
1. 正确按题号分割题目（不再把一道题切两半）
2. 选项每个独占一行（不再混在题干后）
3. 上标用 ^ 标记（x² → x^2）
4. 清理公式排版（合并被空格拆散的内容）

兼容两种PDF格式：
- 旧版 (2008-2012)：选项 A、B、C、D 连排在题干后，无【答案】标记，答案在文本中
- 新版 (2013+)：有【答案】【解析】标记，选项 A. B. C. D. 单独列出

用法：
  python3 parse_pdf_questions.py --pdf path/to/pdf.pdf
  或指定年份和地区
  python3 parse_pdf_questions.py --pdf path/to/pdf.pdf --import-db
"""

import fitz
import re
import json
import sys
import os
import subprocess
import argparse
from collections import defaultdict

# ====== 知识点映射（简化版，根据题目内容智能匹配）======

TOPIC_KEYWORDS = [
    # (topicId, keywords list)
    ("M1-C1-T1", ["集合的概念", "元素", "属于"]),
    ("M1-C1-T3", ["交集", "并集", "补集", "∩", "∪", "集合的运算"]),
    ("M1-C1-T4", ["充分", "必要", "充要", "充分必要"]),
    ("M1-C2-T2", ["基本不等式", "均值不等式", "≥", "最小值", "最大值", "1\\/x"]),
    ("M1-C3-T2", ["单调", "最值"]),
    ("M1-C3-T3", ["奇函数", "偶函数", "奇偶", "对称"]),
    ("M1-C4-T1", ["指数", "2^x", "3^x", "a^x"]),
    ("M1-C4-T2", ["对数", "log", "ln"]),
    ("M1-C4-T4", ["函数模型", "增长"]),
    ("M1-C5-T1", ["弧度", "角度", "π"]),
    ("M1-C5-T4", ["三角函数", "sin", "cos", "tan", "图像", "周期"]),
    ("M1-C5-T5", ["Asin", "ωx", "φ"]),
    ("M1-C5-T6", ["恒等变换", "sin2", "cos2", "倍角", "和差"]),
    ("M2-C1-T1", ["向量", "线性运算", "a+b", "a-b"]),
    ("M2-C1-T2", ["数量积", "点积", "a·b"]),
    ("M2-C1-T3", ["坐标表示", "坐标", "基底"]),
    ("M2-C2-T1", ["复数", "虚数", "i", "i\\^2", "模"]),
    ("M2-C2-T2", ["复数的", "四则", "i)", "i\\("]),
    ("M2-C3-T5", ["体积", "表面积", "柱", "锥", "台", "球"]),
    ("M2-C3-T1", ["立体图形", "直观图"]),
    ("M2-C3-T3", ["平行", "面面平行", "线面平行"]),
    ("M2-C3-T4", ["垂直", "面面垂直", "线面垂直"]),
    ("M2-C4-T1", ["中位数", "众数", "平均数", "方差", "标准差", "频率"]),
    ("M2-C4-T2", ["古典概型", "概率"]),
    ("M3-C1-T1", ["等差数列", "等差"]),
    ("M3-C1-T2", ["等比数列", "等比"]),
    ("M3-C1-T3", ["数列求和", "前n项", "S_n", "Sn"]),
    ("M3-C2-T1", ["直线方程", "斜率", "截距", "直线与"]),
    ("M3-C2-T3", ["圆", "圆心", "半径", "圆的方程"]),
    ("M3-C3-T1", ["椭圆", "焦点", "离心率"]),
    ("M3-C3-T2", ["双曲线", "渐近线"]),
    ("M3-C3-T3", ["抛物线", "准线", "焦点", "y\\^2=", "x\\^2="]),
    ("M4-C1-T2", ["导数", "切线", "单调区间", "极值"]),
    ("M4-C1-T4", ["定积分", "积分"]),
    ("M4-C2-T2", ["二项分布", "正态分布", "期望", "方差", "分布列"]),
    ("M5-C1-T1", ["计数原理", "分类", "分步"]),
    ("M5-C1-T2", ["排列", "组合", "C_n", "A_n"]),
    ("M5-C1-T3", ["二项式", "(a+b)", "展开", "系数"]),
    ("M5-C2-T1", ["随机变量", "概率"]),
]

def guess_topic(content, options=""):
    """根据题目内容猜测知识点"""
    combined = (content + " " + options).lower()
    scores = []
    for tid, kws in TOPIC_KEYWORDS:
        score = 0
        for kw in kws:
            if kw.lower() in combined:
                score += 1
        if score > 0:
            scores.append((score, tid))
    scores.sort(reverse=True)
    if scores:
        return scores[0][1]
    return "M1-C1-T3"  # 默认用集合

def clean_whitespace(text):
    """清理多余空白，合并被空格打断的内容"""
    # 合并换行产生的空格
    text = re.sub(r'\n+', '\n', text)
    # 连续的空白→单个空格
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def fix_superscript(text):
    """
    修复上标标记:
    - 数字跟在字母/括号/运算符后 → 上标
    - 检测常见的上标模式
    """
    # 先用 ^ 标记显式上标
    text = text.replace('²', '^2')
    text = text.replace('³', '^3')
    text = text.replace('⁴', '^4')
    text = text.replace('⁵', '^5')
    text = text.replace('⁰', '^0')
    text = text.replace('¹', '^1')
    text = text.replace('²', '^2')
    text = text.replace('³', '^3')
    text = text.replace('⁺', '^+')
    text = text.replace('⁻', '^-')
    text = text.replace('ⁱ', '^i')
    
    # 对公式中明显的指数模式进行标记: x2, x3, a2 等
    # 在公式上下文中，字母后的数字很可能是上标
    # (但要注意不是数字编号)
    text = re.sub(r'(\w)\^?2\b', lambda m: f"{m.group(1)}^2" if not m.group(0).endswith('^2') else m.group(0), text)
    text = re.sub(r'(\w)\^?3\b', lambda m: f"{m.group(1)}^3" if not m.group(0).endswith('^3') else m.group(0), text)
    
    # 恢复不需要上标的常见词
    text = text.replace('S^2', 'S^2')  # 方差
    
    return text

def extract_options(text):
    """
    从文本中提取选择题选项。
    支持格式:
    - A. xxx B. xxx C. xxx D. xxx (新版)
    - A．xxx B．xxx C．xxx D．xxx (旧版中文标点)
    - A) xxx B) xxx C) xxx D) xxx
    - A、xxx B、xxx C、xxx D、xxx
    """
    # 匹配选项模式
    patterns = [
        # A. xxx B. xxx C. xxx D. xxx
        r'(?:^|\s)([A-D])[\.\．\、\)]\s*(.*?)(?=\s*[A-D][\.\．\、\)]|$)',
        # 更宽松：A) xxx B) xxx  
        r'(?:^|\s)([A-D])[\)）]\s*(.*?)(?=\s*[A-D][\)）]|$)',
    ]
    
    options = {}
    for pattern in patterns:
        options = {}
        for m in re.finditer(pattern, text, re.DOTALL):
            key = m.group(1)
            val = clean_whitespace(m.group(2))
            if val:
                options[key] = val
        if len(options) >= 3:
            break
    
    return options

def extract_answer_solution_new(text):
    """新版格式：从【答案】【解析】中提取"""
    answer = ""
    solution = ""
    
    # 答案
    m = re.search(r'【答案】\s*([^\n【】]+)', text)
    if m:
        raw = m.group(1).strip()
        # 清理多余的格式字符
        answer = raw.replace(' ', '')
        # 如果是字母直接取字母
        ans_letter = re.search(r'[A-D]', answer)
        if ans_letter:
            answer = ans_letter.group()
    
    # 解析
    m = re.search(r'【解析】\s*([\s\S]*?)(?=(?:\d+\.|\n+(?:二[、．]|三[、．]|【|$)))', text)
    if m:
        solution = clean_whitespace(m.group(1))
    
    return answer, solution

def extract_answer_solution_old(text):
    """旧版格式：从文本末尾或上下文中提取答案"""
    answer = ""
    solution = ""
    
    # 通常答案在题后直接给出，如"【答案】C"或直接在括号里
    m = re.search(r'【答案】\s*([A-Da-d])', text)
    if m:
        answer = m.group(1).upper()
        return answer, solution
    
    # 或者有答案解析
    m = re.search(r'答案[：:]\s*([A-Da-d一二三四])', text)
    if m:
        t = m.group(1)
        if t in '一二三四':
            t = {'一': 'A', '二': 'B', '三': 'C', '四': 'D'}.get(t, t)
        answer = t.upper()
    
    return answer, solution

def split_into_questions_new(text):
    """
    新版格式（带【答案】标记）的题目分割
    先按大题分段，再按题号分割
    """
    sections = {}
    
    # 检测大题区域
    # 一、选择题 / 二、填空题 / 三、解答题
    section_pattern = r'([一二三])[、．]\s*(选择题|填空题|解答题)'
    
    # 先分段
    parts = re.split(section_pattern, text)
    
    current_section = None
    section_texts = {}
    
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        if part in '一二三' and i + 1 < len(parts) and parts[i+1] in ['选择题', '填空题', '解答题']:
            current_section = part
            continue
        if part in ['选择题', '填空题', '解答题']:
            continue
        if current_section:
            section_texts[current_section] = part
    
    questions = []
    
    for section_num, stext in section_texts.items():
        # 按题号分割
        # 匹配: 1. / 1、/ 1．后跟内容
        q_blocks = re.split(r'(?=\n\s*\d+\s*[\.\．、])', stext)
        
        for qb in q_blocks:
            qb = qb.strip()
            if not qb:
                continue
            if len(qb) < 10:
                continue
            
            # 提取题号
            m = re.match(r'(\d+)\s*[\.\．、]\s*', qb)
            if not m:
                continue
            q_num = int(m.group(1))
            
            # 去掉题号前缀
            q_text = qb[m.end():]
            
            # 提取答案和解析
            answer, solution = extract_answer_solution_new(q_text)
            
            # 去掉【答案】【解析】部分，保留题干和选项
            # 先找到【答案】的位置
            answer_pos = q_text.find('【答案】')
            stem_and_options = q_text[:answer_pos] if answer_pos > 0 else q_text
            
            # 检测是否有子问题 (如 (Ⅰ)(Ⅱ))
            has_sub_questions = bool(re.search(r'[（(][ⅠⅡⅢⅣⅤⅥ一二三四五六][）)]', q_text))
            # 或 (1)(2)
            if not has_sub_questions:
                has_sub_questions = bool(re.search(r'[（(]\d[）)]', q_text))
            
            # 提取选项
            options = extract_options(stem_and_options)
            
            # 清理题干
            stem = clean_whitespace(stem_and_options)
            
            # 移除选项文本（从题干中移除已经提取的选项）
            for key, val in sorted(options.items(), reverse=True):
                # 尝试移除 A. xxx 这种模式
                stem = re.sub(r'\s*' + re.escape(key) + r'[\.\．\、\)]\s*' + re.escape(val[:30]), '', stem)
            
            stem = clean_whitespace(stem)
            
            # 修复上标
            stem = fix_superscript(stem)
            
            # 格式化选项
            opts_formatted = ""
            if options:
                opts_formatted = "\n".join([f"{k}. {v}" for k, v in sorted(options.items())])
                opts_formatted = fix_superscript(opts_formatted)
            
            q_type = "单选题" if options else ("填空题" if not has_sub_questions and len(q_text) < 500 else "解答题")
            difficulty = "中等"
            
            questions.append({
                "number": q_num,
                "type": q_type,
                "stem": stem,
                "options": opts_formatted,
                "answer": answer,
                "solution": fix_superscript(clean_whitespace(solution)),
                "has_sub_questions": has_sub_questions,
                "section": section_num,
            })
    
    return questions

def split_into_questions_old(text):
    """
    旧版格式（无【答案】标记，选项连排）的题目分割
    """
    questions = []
    
    # 先找大题区域
    sections = {}
    
    # 匹配: 一、选择题 (5' × 12 = 60')
    pattern = r'([一二三])[、．]\s*(.*?)(?=(?:二[、．]|三[、．]|$))'
    
    sec_matches = list(re.finditer(pattern, text, re.DOTALL))
    
    if sec_matches:
        # 有明确大题区块
        for i, m in enumerate(sec_matches):
            sec_num = m.group(1)
            sec_text = m.group(0)
            
            # 按题号分割
            q_blocks = re.split(r'(?=\n\s*\d+\s*[\.\．、](?!\d))', sec_text)
            
            # 每道题内的选项提取
            for qb in q_blocks:
                qb = qb.strip()
                if not qb or len(qb) < 15:
                    continue
                m_q = re.match(r'(\d+)\s*[\.\．、]\s*', qb)
                if not m_q:
                    continue
                q_num = int(m_q.group(1))
                q_text = qb[m_q.end():]
                
                # 提取选项（连排格式: A．{2,3} B．{1,4,5} C．{4,5} D．{1,5}）
                options = extract_options(q_text)
                
                # 题干 = 去掉选项后
                stem = q_text
                for key, val in sorted(options.items(), reverse=True):
                    stem = re.sub(r'\s*' + re.escape(key) + r'[\.\．\、\)]\s*' + re.escape(val[:30]), '', stem)
                stem = clean_whitespace(stem)
                stem = fix_superscript(stem)
                
                # 选项格式化
                opts_formatted = ""
                if options:
                    opts_formatted = "\n".join([f"{k}. {v}" for k, v in sorted(options.items())])
                    opts_formatted = fix_superscript(opts_formatted)
                
                # 检查是否有 (Ⅰ)(Ⅱ) 子问题
                has_sub = bool(re.search(r'[（(][ⅠⅡⅢⅣⅤⅥ][）)]|\（\d\）', q_text))
                
                q_type = "解答题" if has_sub else ("单选题" if options else "填空题")
                difficulty = "中等"
                
                # 看题目开头几个字判断
                first_line = qb.split('\n')[0] if '\n' in qb else qb
                if '解答' in first_line or '本大题' in first_line or '共' in first_line and '分' in first_line:
                    continue
                
                questions.append({
                    "number": q_num,
                    "type": q_type,
                    "stem": stem,
                    "options": opts_formatted,
                    "answer": "",
                    "solution": "",
                    "has_sub_questions": has_sub,
                    "section": sec_num,
                })
    else:
        # 没有明确大题分区，按题号直接分割
        q_blocks = re.split(r'(?=\n\s*\d+\s*[\.\．、](?!\d))', text)
        for qb in q_blocks:
            qb = qb.strip()
            if not qb or len(qb) < 15:
                continue
            m_q = re.match(r'(\d+)\s*[\.\．、]\s*', qb)
            if not m_q:
                continue
            q_num = int(m_q.group(1))
            q_text = qb[m_q.end():]
            options = extract_options(q_text)
            stem = q_text
            for key, val in sorted(options.items(), reverse=True):
                stem = re.sub(r'\s*' + re.escape(key) + r'[\.\．\、\)]\s*' + re.escape(val[:30]), '', stem)
            stem = clean_whitespace(stem)
            stem = fix_superscript(stem)
            opts_formatted = ""
            if options:
                opts_formatted = "\n".join([f"{k}. {v}" for k, v in sorted(options.items())])
                opts_formatted = fix_superscript(opts_formatted)
            questions.append({
                "number": q_num,
                "type": "单选题" if options else "填空题",
                "stem": stem,
                "options": opts_formatted,
                "answer": "",
                "solution": "",
                "has_sub_questions": False,
                "section": "一",
            })
    
    return questions

def detect_format(text):
    """检测PDF是新版还是旧版格式"""
    if '【答案】' in text or '【解析】' in text:
        return 'new'
    return 'old'

def extract_filename_info(filename):
    """从文件名提取年份、地区、文理科信息"""
    info = {"year": "", "region": "", "type": ""}
    
    # 年份
    m = re.search(r'(20\d\d)', filename)
    if m:
        info["year"] = m.group(1)
    
    # 文理科
    if '理' in filename:
        info["type"] = "理科"
    elif '文' in filename:
        info["type"] = "文科"
    
    # 试卷名称
    # 如 （新课标Ⅰ）、（全国甲卷）、（四川）
    m = re.search(r'（([^）]*卷?)）', filename)
    if m:
        info["region"] = m.group(1)
    else:
        m = re.search(r'（([^）]*)）', filename)
        if m:
            info["region"] = m.group(1)
    
    return info

def extract_source_from_filename(filename):
    """从文件名提取试卷来源"""
    info = extract_filename_info(filename)
    year = info["year"]
    region = info["region"] if info["region"] else ""
    qtype = info["type"]
    
    if region:
        return f"{year}年{region}({qtype})" if qtype else f"{year}年{region}"
    else:
        return f"{year}年高考数学({qtype})" if qtype else f"{year}年高考数学"

def parse_pdf(pdf_path):
    """主解析函数"""
    doc = fitz.open(pdf_path)
    basename = os.path.basename(pdf_path)
    
    # 提取全部文本（去掉页码等干扰）
    full_text = ""
    for i in range(doc.page_count):
        page_text = doc[i].get_text()
        # 去掉页码行
        page_text = re.sub(r'第\s*\d+\s*页\s*\|\s*共\s*\d+\s*页\s*\n?', '', page_text)
        # 去掉页眉
        page_text = re.sub(r'第\s*\d+\s*页\s*\n?', '', page_text)
        full_text += page_text + "\n"
    
    doc.close()
    
    # 检测格式
    fmt = detect_format(full_text)
    
    # 提取试卷名称（第一行）
    first_line = full_text.strip().split('\n')[0] if full_text.strip() else ""
    
    # 分割题目
    if fmt == 'new':
        questions = split_into_questions_new(full_text)
    else:
        questions = split_into_questions_old(full_text)
    
    # 从文件名提取来源信息
    source = extract_source_from_filename(basename)
    
    # 为每道题添加知识点、来源等
    for q in questions:
        q["topicId"] = guess_topic(q["stem"], q["options"])
        q["source"] = source
        q["difficulty"] = "中等"
        # cleanup
        q["stem"] = q["stem"].replace('\n', ' ').strip()
        q["stem"] = re.sub(r'\s+', ' ', q["stem"])
    
    return {
        "source": source,
        "first_line": first_line,
        "format_type": fmt,
        "questions": questions,
    }

def format_question_output(q):
    """格式化输出供预览"""
    lines = []
    lines.append(f"  [{q['number']}] [{q['type']}] {q['stem'][:80]}...")
    if q['options']:
        for opt_line in q['options'].split('\n'):
            lines.append(f"    {opt_line}")
    if q['answer']:
        lines.append(f"    → 答案: {q['answer']}")
    if q['solution'][:100]:
        lines.append(f"    → 解析: {q['solution'][:100]}...")
    lines.append(f"    → 知识点: {q['topicId']} | 来源: {q['source']}")
    return '\n'.join(lines)

def import_to_db(questions, api_key, table="questions"):
    """导入到云端数据库"""
    baas_script = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-cloud-database/scripts/baas.py"
    
    success = 0
    fail = 0
    
    for i, q in enumerate(questions):
        if not q['stem']:
            continue
        payload = {
            "table": table,
            "method": "add",
            "apiKey": api_key,
            "tableData": {
                "topicId": q["topicId"],
                "type": q["type"],
                "difficulty": q["difficulty"] if q.get("difficulty") else "中等",
                "content": q["stem"],
                "options": q["options"],
                "answer": q["answer"],
                "solution": q["solution"],
                "source": q["source"],
                "tags": f"{q['source']}, {q['type']}",
            }
        }
        
        cmd = ["python3", baas_script, "--x-api-type", "tableAddData",
               "--content", json.dumps(payload, ensure_ascii=False)]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if "success" in result.stdout.lower() or '"code":"0"' in result.stdout:
                success += 1
                sys.stdout.write(f"  ✅ {i+1}. {q['source']} 题{q['number']}")
            else:
                fail += 1
                sys.stdout.write(f"  ❌ {i+1}. {q['source']} 题{q['number']}: {result.stdout[:100]}")
        except Exception as e:
            fail += 1
            sys.stdout.write(f"  ❌ {i+1}. {q['source']} 题{q['number']}: {e}")
        sys.stdout.flush()
    
    return success, fail


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='解析高考数学PDF并导入题库')
    parser.add_argument('--pdf', required=True, help='PDF文件路径')
    parser.add_argument('--import-db', action='store_true', help='导入到数据库')
    parser.add_argument('--api-key', default="baas_ZiRfZlhr", help='数据库API Key')
    
    args = parser.parse_args()
    
    print(f"📄 正在解析: {args.pdf}")
    result = parse_pdf(args.pdf)
    
    print(f"\n📋 试卷: {result['source']}")
    print(f"📌 格式: {result['format_type']}")
    print(f"📊 题目数: {len(result['questions'])}")
    
    for q in result['questions']:
        print()
        print(format_question_output(q))
    
    if args.import_db:
        print(f"\n💾 正在导入 {len(result['questions'])} 道题到数据库...")
        s, f = import_to_db(result['questions'], args.api_key)
        print(f"\n✅ 导入完成: 成功 {s}, 失败 {f}")
