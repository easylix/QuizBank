#!/usr/bin/env python3
"""
高考数学解析卷批量导入器

支持所有卷种格式：
- 新高考Ⅰ/Ⅱ卷：一、选择题 → 二、选择题 → 三、填空题 → 四、解答题
- 全国甲/乙卷：一、选择题 → 二、填空题 → 三、解答题
- 北京/天津/上海卷
"""

import re, json, sys, os, subprocess, argparse
from markitdown import MarkItDown

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-web-deploy/scripts/baas.py"

def pdf_to_markdown(pdf_path):
    md = MarkItDown()
    result = md.convert(pdf_path)
    return result.text_content

def normalize_text(raw_text):
    """修复PDF提取中的Unicode乱码"""
    text = raw_text
    # Unicode符号映射
    fixes = {
        '': '{', '': '}',
        '': '(', '': ')',
        '': '-', '': '+',
        '': '≈',
        '': '≤', '': '≥',
        '': 'α', '': 'β', '': 'γ', '': 'π',
        '': 'θ', '': 'φ', '': 'ω',
        '': '∑', '': '∫', '': '→',
        '': '₁', '': '₂', '': '₃',
        'ð': '∁',
    }
    for k, v in fixes.items():
        text = text.replace(k, v)
    
    # 删除页码水印
    text = re.sub(r'学科网（北京）股份有限公司\s*第\s*\d+\s*页/共\s*\d+\s*页\n?', '', text)
    text = re.sub(r'第\s*\d+\s*页/共\s*\d+\s*页\n?', '', text)
    text = re.sub(r'学科网（北京）股份有限公司\n?', '', text)
    
    # 保留有效换行
    lines = text.split('\n')
    cleaned = [l.rstrip() for l in lines if l.strip()]
    return '\n'.join(cleaned)

def find_section_headers(text):
    """找到所有大题标题及其位置"""
    headers = []
    patterns = [
        r'一[、．]\s*选择题',
        r'二[、．]\s*选择题',
        r'二[、．]\s*填空题',
        r'三[、．]\s*填空题',
        r'三[、．]\s*解答题',
        r'四[、．]\s*解答题',
    ]
    for p in patterns:
        for m in re.finditer(p, text):
            headers.append((m.start(), m.group()))
    
    # 按位置排序
    headers.sort(key=lambda x: x[0])
    return headers

def determine_type(section_name, qnum, text_before):
    """判断题型"""
    if '多选题' in section_name or ('二' in section_name and '选择题' in section_name):
        # 新高考卷：二、选择题 = 多选题
        return '多选题'
    if '选择题' in section_name or '单选题' in section_name:
        return '单选题'
    if '填空题' in section_name:
        return '填空题'
    if '解答题' in section_name:
        return '解答题'
    
    # 根据位置判断
    if '四、' in text_before:
        return '解答题'
    if '三、' in text_before or '二、填空题' in text_before:
        return '填空题'
    if '二、选择题' in text_before:
        return '多选题'
    return '单选题'

def parse_pdf(pdf_path):
    """解析PDF，返回题目列表"""
    raw = pdf_to_markdown(pdf_path)
    text = normalize_text(raw)
    
    # 找到所有【答案】位置
    ans_positions = [(m.start(), m.end()) for m in re.finditer('【答案】', text)]
    if not ans_positions:
        print("❌ 未找到【答案】标记")
        return []
    
    # 找到大题标题
    section_headers = find_section_headers(text)
    
    questions = []
    
    for idx, (astart, aend) in enumerate(ans_positions):
        # 题目开始
        if idx == 0:
            # 第一个题：从第一个大题标题开始
            q_start = section_headers[0][0] if section_headers else 0
        else:
            q_start = ans_positions[idx - 1][1]
        
        # 题目结束：下一个【答案】之前
        if idx + 1 < len(ans_positions):
            next_start = ans_positions[idx + 1][0]
        else:
            next_start = len(text)
        
        block = text[q_start:next_start].strip()
        
        # 跳过头部废话块（绝密、注意事项等没有题号的）
        first_200 = block[:200]
        # 检查是否包含题号
        if not re.search(r'\d+\s*[\.\．、]', first_200):
            continue
        
        # 获取题号
        qnum_match = re.search(r'(\d+)\s*[\.\．、]', block)
        if not qnum_match:
            continue
        qnum = qnum_match.group(1)
        
        # 判断题型
        text_before = text[:astart]
        q_type = determine_type('', int(qnum), text_before)
        
        # 提取答案
        ans_end = astart + 4
        ans_block = text[ans_end:next_start].strip() if idx + 1 < len(ans_positions) else text[ans_end:].strip()
        sol_match = re.search(r'【解析】', ans_block)
        answer = ans_block[:sol_match.start()].strip() if sol_match else ans_block.strip()
        
        # 提取解析
        solution = ''
        full_block = text[astart:next_start].strip() if idx + 1 < len(ans_positions) else text[astart:].strip()
        sol_pos = full_block.find('【解析】')
        if sol_pos != -1:
            solution = full_block[sol_pos + 4:].strip()
        # 也要提取【点睛】
        dj_pos = full_block.find('【点睛】')
        if dj_pos != -1:
            if solution:
                solution += '\n【点睛】' + full_block[dj_pos + 4:].strip()
            else:
                solution = full_block[dj_pos + 4:].strip()
        
        # 提取题干（【答案】之前的内容）
        content_block = block
        ans_local = content_block.find('【答案】')
        if ans_local != -1:
            content_block = content_block[:ans_local].strip()
        
        # 去掉section header
        for h in ['一、选择题', '二、选择题', '二、填空题', '三、填空题', '三、解答题', '四、解答题']:
            if h in content_block:
                content_block = content_block.split(h, 1)[1].strip()
        
        # 去掉说明文字
        content_block = re.sub(r'本题共\s*\d+\s*小题.*', '', content_block)
        content_block = re.sub(r'在每小题给出的四个选项中.*', '', content_block)
        content_block = re.sub(r'在每小题给出的选项中.*', '', content_block)
        content_block = re.sub(r'全部选对得.*', '', content_block)
        
        # 提取选项
        options = ''
        opt_lines = []
        for line in content_block.split('\n'):
            line_s = line.strip()
            if re.match(r'^[A-F]\s*[\.\．、]', line_s):
                opt_lines.append(line_s)
        
        # 处理选项在一行的情况（如 A. xxx B. xxx C. xxx D. xxx）
        if not opt_lines:
            inline_opts = re.findall(r'[A-F]\s*[\.\．、]\s*[^A-F]+?(?=\s*[A-F]\s*[\.\．、]|$)', content_block)
            if inline_opts and len(inline_opts) >= 3:
                opt_lines = [o.strip() for o in inline_opts]
        
        if opt_lines:
            options = '\n'.join(opt_lines)
            # 从题干中去掉选项行
            for ol in opt_lines:
                content_block = content_block.replace(ol, '').replace('\n' + ol, '')
        
        # 清理题干（压缩多余空行，保留单换行）
        content_block = re.sub(r'\s+', ' ', content_block).strip()
        # 去掉题号前缀
        content_block = re.sub(r'^\d+\s*[\.\．、]\s*', '', content_block)
        
        # 清理答案（压缩多余空行）
        answer = re.sub(r'\s+', ' ', answer).strip()
        answer = answer.replace('\n', '')
        
        # 压缩解析中的多余空行（连续2+换行→单个换行）
        solution = re.sub(r'\n{2,}', '\n', solution).strip()
        
        questions.append({
            'qnum': qnum,
            'type': q_type,
            'content': content_block,
            'options': options,
            'answer': answer,
            'solution': solution,
        })
    
    return questions

def format_for_db(q, source):
    """格式化数据为DB记录"""
    content_text = q['content']
    if q['options']:
        content_text = content_text + '\n\n' + q['options']
    
    answer = q['answer'] if q['answer'] else ''
    solution = q['solution']
    
    # 清理解析
    if solution.startswith('【解析】'):
        solution = solution[4:].strip()
    if solution.startswith('】'):
        solution = solution[1:].strip()
    
    return {
        'topicId': 'M1-C1-T1',
        'type': q['type'],
        'difficulty': '中等',
        'content': content_text,
        'options': q['options'] if q['options'] else '',
        'answer': answer,
        'solution': solution,
        'source': source,
        'tags': f'{source},number:{q["qnum"]}'
    }

def import_to_db(records, source):
    """批量导入数据库"""
    success = 0
    fail = 0
    fail_details = []
    
    for i, rec in enumerate(records):
        payload = json.dumps({
            'table': 'questions',
            'method': 'add',
            'apiKey': 'baas_ZiRfZlhr',
            'tableData': rec
        })
        cmd = ['python3', BAAS_SCRIPT, '--x-api-type', 'tableAddData', '--content', payload]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if '"code":"0"' in r.stdout or 'success' in r.stdout.lower():
                success += 1
                print(f'  ✅ 题{rec["tags"].split("number:")[1].split(",")[0] if "number:" in rec["tags"] else i+1}', flush=True)
            else:
                fail += 1
                fail_details.append(f'题{rec["tags"]}: {r.stdout[:200]}')
                print(f'  ❌ 题{rec["tags"]}', flush=True)
        except Exception as e:
            fail += 1
            fail_details.append(str(e))
            print(f'  ❌ 题{rec["tags"]}: {e}', flush=True)
    
    return success, fail, fail_details

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--source', default='', help='试卷来源名称')
    parser.add_argument('--import-db', action='store_true')
    args = parser.parse_args()
    
    print(f'📄 解析: {os.path.basename(args.pdf)}')
    questions = parse_pdf(args.pdf)
    
    source = args.source or os.path.basename(args.pdf).replace('.pdf', '').replace('（解析卷）', '')
    print(f'📋 试卷: {source}')
    print(f'📊 题目数: {len(questions)}')
    
    types = {}
    for q in questions:
        types[q['type']] = types.get(q['type'], 0) + 1
    print(f'   题型分布: {types}')
    
    for q in questions:
        c = q['content'][:65].replace('\n', ' ')
        print(f'\n  [Q{q["qnum"]}] [{q["type"]}] {c}')
        if q['options']:
            for ol in q['options'].split('\n')[:4]:
                print(f'    {ol}')
        print(f'    ✏️ 答案: {q["answer"][:60]}')
        if q['solution']:
            sol_short = q['solution'][:80].replace('\n', ' ')
            print(f'    📝 解析: {sol_short}...')
    
    if args.import_db:
        print(f'\n💾 开始导入 {len(questions)} 道题到数据库...')
        records = [format_for_db(q, source) for q in questions]
        success, fail, details = import_to_db(records, source)
        print(f'\n✅ 导入完成: 成功={success}, 失败={fail}')
        if fail > 0:
            print('失败详情:')
            for d in details[:5]:
                print(f'  • {d}')
    
    return questions

if __name__ == '__main__':
    main()
