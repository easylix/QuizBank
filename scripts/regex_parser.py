#!/usr/bin/env python3
"""
正则解析器: 将带[figN]标记的OCR文本按标准格式拆分为结构化题

格式假设:
  一、选择题／二、填空题／三、解答题
  1. 题干文字（可跨行）
  A. 选项x  B. 选项y ... (选择题)
  【答案】xxx
  【解析】(可省略)
  【分析】xxx (可省略)
  【详解】xxx (可省略)
  【点睛】xxx (可省略)
"""
import re, sys, json

def parse_to_questions(text: str, source: str) -> list:
    lines = text.split('\n')
    
    # 正则
    re_section = re.compile(r'^[一二三][、.．]\s*(选|填|解)')  # 一、选择题
    re_qnum = re.compile(r'^(\d+)[.．]\s')                    # 1. 
    re_option = re.compile(r'^[A-Da-d]\s*[.．、]\s')          # A.  B)  A、 
    re_answer = re.compile(r'^【答案】')                      # 【答案】xxx 
    re_analysis = re.compile(r'^【分析】')                    # 【分析】xxx
    re_detail = re.compile(r'^【详解】')                      # 【详解】xxx
    re_highlight = re.compile(r'^【点睛】')                   # 【点睛】xxx
    re_ending = re.compile(r'^(?:故选|故答案为|所以答案)')    # 故选：xxx
    
    questions = []
    cur = None  # current question buffer
    section_name = ""
    state = "idle"  # idle | content | options | sol_analysis | sol_detail | sol_highlight | sol_other
    qnum = 0
    
    def pop_question(to_next_qnum=None):
        nonlocal cur, qnum
        if cur is None:
            return
        
        # Build answer
        answer = (cur.get('_answer', '') or '').strip()
        
        # Build solution from all sol_* lines
        sol_parts = []
        analysis = cur.get('_analysis', '').strip()
        detail = cur.get('_detail', '').strip()
        highlight = cur.get('_highlight', '').strip()
        if analysis:
            sol_parts.append('【分析】' + analysis)
        if detail:
            sol_parts.append('【详解】' + detail)
        if highlight:
            sol_parts.append('【点睛】' + highlight)
        solution = '\n\n'.join(sol_parts)
        
        # Content & options
        content = cur.get('_content', '').strip()
        options = cur.get('_options', '').strip()
        
        # Type
        if '选择' in section_name:
            qtype = '单选题'
        elif '填空' in section_name:
            qtype = '填空题'
        else:
            qtype = '解答题'
        
        # 选择题答案转字母
        if qtype in ('单选题', '多选题') and options:
            ans_clean = re.sub(r'[\s\$]', '', answer)
            opt_lines = [l for l in options.split('\n') if l.strip()]
            matched_letter = None
            for o in opt_lines:
                letter = o[0].upper()
                oc = re.sub(r'^[A-Da-d][.．、]\s*', '', o)
                oc_clean = re.sub(r'[\s\$]', '', oc)
                if ans_clean == oc_clean:
                    matched_letter = letter
                    break
                # Also try direct letter match
                if answer.upper() == letter:
                    matched_letter = letter
                    break
            if matched_letter:
                answer = matched_letter
        
        # Difficulty
        total_sel = sum(1 for q in questions if q['type'] == '单选题')
        if qtype == '单选题':
            idx = total_sel + 1
            if idx <= 4:
                difficulty = '基础'
            elif idx <= 8:
                difficulty = '中等'
            else:
                difficulty = '困难'
        elif qtype == '填空题':
            difficulty = '中等'
        else:
            difficulty = '中等'
        
        record = {
            'type': qtype,
            'difficulty': difficulty,
            'content': content,
            'options': options,
            'answer': answer,
            'solution': solution,
            'source': source,
        }
        questions.append(record)
        
        # 如果指定了新题号，更新qnum
        if to_next_qnum:
            qnum = to_next_qnum
    
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            # 空行: 根据不同状态处理
            # content或options保留空行，solution不保留
            if cur and state == 'content':
                cur['_content'] = (cur.get('_content', '') or '') + '\n'
            elif cur and state == 'options':
                cur['_options'] = (cur.get('_options', '') or '') + '\n'
            continue
        
        # 1. 大题标题
        m_sec = re_section.match(stripped)
        if m_sec:
            # 弹出上一题
            if cur:
                pop_question()
            section_name = stripped
            cur = None
            state = 'idle'
            continue
        
        # 2. 题号
        m_q = re_qnum.match(stripped)
        if m_q:
            new_qnum = int(m_q.group(1))
            # 如果有当前题，弹出
            if cur is not None:
                pop_question(to_next_qnum=new_qnum)
            
            cur = {
                '_content': stripped[m_q.end():],  # 题号后的文本
                '_options': '',
                '_answer': '',
                '_analysis': '',
                '_detail': '',
                '_highlight': '',
            }
            qnum = new_qnum
            state = 'content'
            continue
        
        # 如果还没有cur（在"一、选择题"之后、第1题之前的内容），跳过
        if cur is None:
            continue
        
        # 3. 选项 (仅在content/options状态下)
        m_o = re_option.match(stripped)
        if m_o and state in ('content', 'options'):
            if cur['_options']:
                cur['_options'] += '\n' + stripped
            else:
                cur['_options'] = stripped
            state = 'options'
            continue
        
        # 4. 【答案】
        if re_answer.match(stripped):
            cur['_answer'] = stripped[4:].strip()
            state = 'answer'
            continue
        
        # 5. 【解析】(只是分隔标记，不包含内容)
        if stripped == '【解析】' or stripped.startswith('【解析】'):
            state = 'sol_other'
            continue
        
        # 6. 【分析】
        if re_analysis.match(stripped):
            cur['_analysis'] = stripped[4:].strip()
            state = 'sol_analysis'
            continue
        
        # 7. 【详解】
        if re_detail.match(stripped):
            cur['_detail'] = stripped[4:].strip()
            state = 'sol_detail'
            continue
        
        # 8. 【点睛】
        if re_highlight.match(stripped):
            cur['_highlight'] = stripped[5:].strip()
            state = 'sol_highlight'
            continue
        
        # 9. 其他文本，按当前状态分配
        if state == 'content':
            # 可能题干跨多行
            if cur['_content']:
                cur['_content'] += '\n' + stripped
            else:
                cur['_content'] = stripped
        elif state == 'options':
            # 选项可能跨行（MathType公式分行）
            if cur['_options']:
                cur['_options'] += '\n' + stripped
            else:
                cur['_options'] = stripped
        elif state == 'answer':
            # 答案可能跨行
            if cur['_answer']:
                cur['_answer'] += ' ' + stripped
            else:
                cur['_answer'] = stripped
        elif state in ('sol_analysis', 'sol_other'):
            if cur['_analysis']:
                cur['_analysis'] += '\n' + stripped
            else:
                cur['_analysis'] = stripped
            state = 'sol_analysis'
        elif state == 'sol_detail':
            if cur['_detail']:
                cur['_detail'] += '\n' + stripped
            else:
                cur['_detail'] = stripped
        elif state == 'sol_highlight':
            if cur['_highlight']:
                cur['_highlight'] += '\n' + stripped
            else:
                cur['_highlight'] = stripped
        else:
            # 兜底
            pass
    
    # 最后一题
    if cur is not None:
        pop_question()
    
    return questions


# 测试
if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/import_pipeline_v3/ocr/ocr_marked.txt'
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    questions = parse_to_questions(text, '2023全国乙卷理')
    print(f"共解析出 {len(questions)} 道题")
    
    figs_content = 0
    figs_solution = 0
    empty_image = 0
    empty_answer_image = 0
    
    for i, q in enumerate(questions):
        c_figs = re.findall(r'\[fig\d+\]', q['content'])
        s_figs = re.findall(r'\[fig\d+\]', q['solution'])
        if c_figs:
            figs_content += len(c_figs)
        if s_figs:
            figs_solution += len(s_figs)
        
        print(f"\n--- 题#{i+1} ({q['type']}) ---")
        print(f"  答案: {repr(q['answer'])}")
        print(f"  题干[fig]: {c_figs}")
        print(f"  解析[fig]: {s_figs}")
        print(f"  题干前80: {repr(q['content'][:80])}")
        if q['options']:
            opts_short = q['options'][:80]
            print(f"  选项: {repr(opts_short)}")
        if q['solution']:
            sol_short = q['solution'][:100].replace('\n', '\\n')
            print(f"  解析: {sol_short}")
    
    print(f"\n统计: {len(questions)}题, content中[fig]={figs_content}, solution中[fig]={figs_solution}")
