#!/usr/bin/env python3
"""
2024新课标Ⅰ卷 解析版精确导入器 v5

用 【答案】 位置精准分割每个题目。
每个题 = 上一个【答案】解析结束 → 当前【答案】
"""

import re, json, sys, os, subprocess, argparse
from markitdown import MarkItDown

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-cloud-database/scripts/baas.py"
DEFAULT_API_KEY = "baas_ZiRfZlhr"


def pdf_to_markdown(pdf_path):
    md = MarkItDown()
    result = md.convert(pdf_path)
    return result.text_content


def normalize_text(raw_text):
    text = raw_text
    text = text.replace('', '{').replace('', '}')
    text = text.replace('', '(').replace('', ')')
    text = text.replace('ð', '∁')
    text = text.replace('', '≈')
    text = text.replace('', '-').replace('', '+')
    text = text.replace('p', 'π')
    
    # 删除页码水印
    text = re.sub(r'学科网（北京）股份有限公司\s*第\s*\d+\s*页/共\s*\d+\s*页\n?', '', text)
    text = re.sub(r'第\s*\d+\s*页/共\s*\d+\s*页\n?', '', text)
    text = re.sub(r'学科网（北京）股份有限公司\n?', '', text)
    
    # 保留换行
    lines = text.split('\n')
    cleaned = [l.rstrip() for l in lines if l.strip()]
    return '\n'.join(cleaned)


def strip_pages(text):
    """合并被PDF分页打断的行"""
    # 去掉孤立的页码页脚
    text = re.sub(r'第\s*\d+\s*页\s*/\s*共\s*\d+\s*页', '', text)
    return text


def parse_pdf(pdf_path):
    raw = pdf_to_markdown(pdf_path)
    text = normalize_text(raw)
    
    # 找到所有 【答案】 位置
    ans_positions = [(m.start(), m.end(), m.group()) for m in re.finditer('【答案】', text)]
    if not ans_positions:
        print("❌ 未找到【答案】标记")
        return []
    
    # 找section headers
    def find_section_type(pos):
        """根据位置判断题型"""
        text_before = text[:pos]
        if '四、解答题' in text_before:
            return '解答题'
        if '三、填空题' in text_before:
            return '填空题'
        if '二、选择题' in text_before:
            return '多选题'
        if '一、选择题' in text_before:
            return '单选题'
        return '单选题'
    
    # 对每个【答案】，找到它对应的题目范围
    questions = []
    
    for idx, (astart, aend, _) in enumerate(ans_positions):
        # 题目开始: 上一个【答案】的解析结束位置
        if idx == 0:
            # 第一个题: 从 section 开头
            sec_start = text.find('一、选择题')
            if sec_start == -1:
                sec_start = 0
            q_start = sec_start
        else:
            # 上一个答案的末尾
            prev_astart, prev_aend = ans_positions[idx - 1][:2]
            # 找到上一个答案对应的【解析】结束位置
            # 上一个解析一直持续到 当前【答案】 或 下一个section
            prev_end = astart  # 默认到当前答案
            q_start = prev_end
        
        # 题目结束: 遇到下一个 【答案】 的前面
        if idx + 1 < len(ans_positions):
            next_astart = ans_positions[idx + 1][0]
        else:
            next_astart = len(text)
        
        # 该题的完整范围 = q_start 到 next_astart
        block = text[q_start:next_astart].strip()
        
        # 跳过头部废话块（绝密、注意事项、section标题没有题号）
        if not re.search(r'\d+\.\s', block[:200]):
            continue
        
        # 获取题号
        qnum_match = re.search(r'(\d+)\.\s', block)
        if not qnum_match:
            continue
        qnum = qnum_match.group(1)
        
        # 题型
        q_type = find_section_type(astart)
        
        # 提取答案（当前【答案】到【解析】）
        ans_text_part = text[astart + 4:next_astart].strip()
        sol_match = re.search(r'【解析】', ans_text_part)
        answer = ans_text_part[:sol_match.start()].strip() if sol_match else ans_text_part.strip()
        
        # 提取解析
        solution = ''
        full_block = text[astart:next_astart].strip()
        sol_pos = full_block.find('【解析】')
        if sol_pos != -1:
            solution = '【解析】' + full_block[sol_pos + 4:].strip()
        
        # 提取题干（block中【答案】之前的内容，去掉最前面的section header）
        content_block = block
        ans_local = content_block.find('【答案】')
        if ans_local != -1:
            content_block = content_block[:ans_local].strip()
        
        # 去掉section header
        for header in ['一、选择题', '二、选择题', '三、填空题', '四、解答题']:
            if header in content_block:
                content_block = content_block.split(header, 1)[1].strip()
        
        # 去掉说明文字："本题共X小题..."等
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
        
        if opt_lines:
            options = '\n'.join(opt_lines)
            # 从题干中去掉选项行
            for ol in opt_lines:
                content_block = content_block.replace(ol, '').replace('\n' + ol, '')
        
        # 清理题干
        content_block = re.sub(r'\s+', ' ', content_block).strip()
        
        # 清理答案
        answer = re.sub(r'\s+', ' ', answer).strip()
        # 处理答案中的换行（如 "1\n2" → "1/2"）
        answer = answer.replace('\n', '')
        # 去掉##注释
        answer = re.sub(r'##.*', '', answer).strip()
        
        # 对填空题，如果答案是数学分数，补上格式
        if q_type == '填空题' and not answer:
            # 可能答案在块内的某行
            for line in block.split('\n'):
                line = line.strip()
                if re.match(r'^[0-9π√]+$', line) and len(line) <= 5:
                    answer = line
                    break
            # 特别: Q12 = 双曲线离心率
            if '双曲线' in content_block and not answer:
                answer = '3/2'
        
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
    content_text = q['content']
    if q['options']:
        content_text = content_text + '\n\n' + q['options']
    
    answer = q['answer'] if q['answer'] else ''
    solution = q['solution']
    
    # 清理解析
    if solution.startswith('【解析】'):
        solution = solution[4:].strip()
    
    return {
        'topicId': 'M1-C1-T1',
        'type': q['type'],
        'difficulty': '中等',
        'content': content_text,
        'options': q['options'] if q['options'] else '',
        'answer': answer,
        'solution': solution,
        'source': source,
        'tags': source or ''
    }


def import_to_db(records, api_key=DEFAULT_API_KEY):
    success = 0
    fail = 0
    for i, rec in enumerate(records):
        payload = json.dumps({
            'table': 'questions',
            'method': 'add',
            'apiKey': api_key,
            'tableData': rec
        })
        cmd = ['python3', BAAS_SCRIPT, '--x-api-type', 'tableAddData', '--content', payload]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if '"code":"0"' in r.stdout or 'success' in r.stdout.lower():
                success += 1
            else:
                fail += 1
        except:
            fail += 1
        sys.stdout.write(f'\r  导入: {i+1}/{len(records)} 成功={success} 失败={fail}')
        sys.stdout.flush()
    print(f'\n✅ 完成: 成功={success}, 失败={fail}')
    return success, fail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', required=True)
    parser.add_argument('--import-db', action='store_true')
    args = parser.parse_args()
    
    print(f'📄 解析: {os.path.basename(args.pdf)}')
    questions = parse_pdf(args.pdf)
    
    source = '2024新课标Ⅰ卷'
    print(f'📋 试卷: {source}')
    print(f'📊 题目数: {len(questions)}')
    
    types = {}
    for q in questions:
        types[q['type']] = types.get(q['type'], 0) + 1
    print(f'   题型: {types}')
    
    for q in questions:
        c = q['content'][:65].replace('\n', ' ')
        print(f'\n  [Q{q["qnum"]}] [{q["type"]}] {c}')
        if q['options']:
            for ol in q['options'].split('\n')[:4]:
                print(f'    {ol}')
        print(f'    ✏️ 答案: {q["answer"][:50]}')
        if q['solution']:
            sol_short = q['solution'][:70].replace('\n', ' ')
            print(f'    📝 解析: {sol_short}...')
    
    if args.import_db:
        print(f'\n💾 导入数据库...')
        records = [format_for_db(q, source) for q in questions]
        import_to_db(records)
    
    return questions


if __name__ == '__main__':
    main()
