#!/usr/bin/env python3
"""
流水线 v2: 正则解析 + 图片标记 + 知识点/难度

流程:
1. 全局 [图] → {IMG_1}, {IMG_2}, ...
2. 正则拆解为单题（保留 {IMG_X} 标记）
3. 从 --- 分隔后的标注段提取【知识点】【难度】
4. 知识点自然语言 → 知识树 ID（模糊匹配 + LLM 回退）
5. 每道题独立重编号 [figN] + 分配图片

用法:
  python3 pipeline_v2.py <ocr_merged.txt> <images_dir> <output.json> <source_name>
"""
import re, json, sys, os, base64

PLACEHOLDER_PREFIX = '{IMG_'

# ========= 步骤A: [图] → {IMG_N} 全局替换 =========
def replace_fig_markers(text: str) -> tuple:
    fig_count = 0
    def repl(m):
        nonlocal fig_count
        fig_count += 1
        return PLACEHOLDER_PREFIX + str(fig_count) + '}'
    result = re.sub(r'\[图\]', repl, text)
    return result, fig_count


# ========= 知识树加载与匹配 =========
def load_knowledge_tree() -> dict:
    tree_path = os.path.join(os.path.dirname(__file__), '..', 'public', 'data', 'knowledge-tree.json')
    if not os.path.exists(tree_path):
        print("  ⚠️ 知识树文件不存在，跳过知识点匹配")
        return {}
    with open(tree_path, 'r', encoding='utf-8') as f:
        tree = json.load(f)
    id_name = {}
    for mod in tree['modules']:
        for ch in mod['chapters']:
            for t in ch['topics']:
                id_name[t['id']] = t['name']
            id_name[ch['id'] + '-OTHER'] = ch['name'] + '其他'
    return id_name


def fuzzy_match_knowledge(text: str, id_name_map: dict) -> str:
    """自然语言知识点描述 → 知识树ID（字符级模糊匹配）"""
    if not text or not id_name_map:
        return ''
    text_clean = re.sub(r'[、，,。.、\s]', '', text)
    best_id = None
    best_score = 0
    for tid, tname in id_name_map.items():
        tname_clean = re.sub(r'[、，,。.、\s]', '', tname)
        if not tname_clean:
            continue
        m = len(tname_clean)
        n = len(text_clean)
        max_common = 0
        for start in range(n):
            k = 0
            while start + k < n and k < m and text_clean[start + k] == tname_clean[k]:
                k += 1
            if k > max_common:
                max_common = k
        score = max_common / max(m, 1)
        if score > best_score:
            best_score = score
            best_id = tid
    return best_id if best_score >= 0.6 else ''


def llm_match_knowledge(text: str, id_name_map: dict) -> str:
    """LLM 回退映射"""
    kt_list = '\n'.join(f'{tid} {tname}' for tid, tname in id_name_map.items())
    prompt = f"""你是一个高中数学知识点分类专家。请将以下知识点描述映射到最精确的知识点ID。

可用知识点ID映射：
{kt_list}

用户描述：{text}

请只输出一个知识点ID，不要任何解释。如果不太确定，选择最接近的。"""

    volc_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    volc_key = "a99be5e8-4c9b-4c08-96d1-1e2ec5bccacf"
    volc_model = "doubao-1.5-lite-32k-250115"

    payload = {
        "model": volc_model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 64,
        "temperature": 0.1
    }

    try:
        import urllib.request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(volc_url, data=data,
            headers={"Authorization": f"Bearer {volc_key}", "Content-Type": "application/json"},
            method='POST')
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        llm_text = result["choices"][0]["message"]["content"].strip()
        m = re.search(r'(M\d+-C\d+-[A-Z]+\d+(?:-\d+)?)', llm_text)
        if m and m.group(1) in id_name_map:
            return m.group(1)
        return ''
    except Exception as e:
        print(f"    ⚠️ LLM匹配失败: {e}")
        return ''


def match_knowledge(text: str, id_name_map: dict) -> str:
    if not text or not id_name_map:
        return ''
    tid = fuzzy_match_knowledge(text, id_name_map)
    if tid:
        return tid
    print(f"    🔄 模糊匹配失败，调LLM映射: {text}")
    return llm_match_knowledge(text, id_name_map)


# ========= 步骤B: 解析标注段 =========
def _parse_meta_section(meta_text: str) -> dict:
    """解析 --- 后的知识点/难度标注段
    格式: 1. 知识：集合的基本运算 难度：基础
    返回 {题号: {'knowledge': str, 'difficulty': str}}
    """
    result = {}
    # 匹配 "1. 知识：xxx 难度：xxx" 或 "1. 知识:xxx 难度:xxx"
    re_meta = re.compile(r'^(\d+)[.．]\s*知识[：:](.+?)难度[：:](.+)$')
    for line in meta_text.strip().split('\n'):
        m = re_meta.search(line)
        if m:
            qnum = int(m.group(1))
            knowledge = m.group(2).strip()
            difficulty = m.group(3).strip()
            result[qnum] = {'knowledge': knowledge, 'difficulty': difficulty}
    return result


# ========= 步骤C: 正则拆解题目 =========
def parse_questions(text: str, source: str, id_name_map: dict) -> list:
    """正则拆解为题列表，从 --- 后提取知识点/难度"""
    # 切分: --- 前是题目，--- 后是知识点/难度标注
    parts = text.split('\n---\n')
    question_text = parts[0]
    meta_text = parts[1] if len(parts) > 1 else ''
    meta_map = _parse_meta_section(meta_text)
    if meta_map:
        print(f"      解析了 {len(meta_map)} 题的知识点/难度标注")

    lines = question_text.split('\n')

    re_section = re.compile(r'^[一二三][、.．]\s*(选|填|解)')
    re_qnum = re.compile(r'^(\d+)[.．]\s*')
    re_option = re.compile(r'^[A-Da-d]\s*[.．、]\s')
    re_answer = re.compile(r'^【答案】')
    re_analysis = re.compile(r'^【分析】')
    re_detail = re.compile(r'^【详解】')
    re_highlight = re.compile(r'^【点睛】')

    questions = []
    cur = None
    section_name = ""
    state = "idle"

    def pop_question():
        nonlocal cur
        if cur is None:
            return

        content = cur.get('_content', '').strip()
        # 去除内容中的所有空行
        content = '\n'.join(l for l in content.split('\n') if l.strip())
        options = cur.get('_options', '').strip()
        answer = (cur.get('_answer', '') or '').strip()
        qnum = cur.get('_qnum', 0)

        # 组装解析
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
        # 去除解析中的所有空行
        solution = '\n'.join(l for l in solution.split('\n') if l.strip())

        # 题型
        if '选择' in section_name:
            qtype = '单选题'
        elif '填空' in section_name:
            qtype = '填空题'
        else:
            qtype = '解答题'

        # 选择题答案转字母
        if qtype in ('单选题', '多选题') and options:
            opt_lines = [l for l in options.split('\n') if l.strip()]
            if not re.match(r'^[A-Da-d]+$', answer):
                ans_clean = re.sub(r'[\s\$\{\}\\\^]', '', answer)
                for o in opt_lines:
                    letter = o[0].upper()
                    oc = re.sub(r'^[A-Da-d][.．、]\s*', '', o)
                    oc_clean = re.sub(r'[\s\$\{\}\\\^]', '', oc)
                    if ans_clean == oc_clean:
                        answer = letter
                        break

        # 难度：标注段 → 关键词 → 硬编码
        if qnum in meta_map and meta_map[qnum].get('difficulty'):
            dt = meta_map[qnum]['difficulty']
            dk = {'基础': '基础', '简单': '基础', '中等': '中等', '困难': '困难', '较难': '困难'}
            for kw, val in dk.items():
                if kw in dt:
                    difficulty = val
                    break
            else:
                difficulty = '中等'
        else:
            total_sel = sum(1 for q in questions if q['type'] == '单选题')
            if qtype == '单选题':
                idx = total_sel + 1
                difficulty = '基础' if idx <= 4 else ('中等' if idx <= 8 else '困难')
            else:
                difficulty = '中等'

        # 知识点：标注段 → 模糊匹配 → LLM 回退
        topic_id = ''
        if qnum in meta_map and meta_map[qnum].get('knowledge'):
            kt = meta_map[qnum]['knowledge']
            topic_id = match_knowledge(kt, id_name_map)
            if topic_id:
                print(f"    ✅ 知识点匹配: {kt} → {topic_id}")
            else:
                print(f"    ⚠️ 知识点未匹配: {kt}")

        record = {
            'type': qtype,
            'difficulty': difficulty,
            'content': content,
            'options': options,
            'answer': answer,
            'solution': solution,
            'source': source,
            'topicId': topic_id,
        }
        questions.append(record)
        cur = None

    # 主解析循环
    for line in lines:
        s = line.rstrip()
        if not s:
            if cur:
                if state == 'content':
                    cur['_content'] = (cur.get('_content','') or '') + '\n'
                elif state == 'options':
                    cur['_options'] = (cur.get('_options','') or '') + '\n'
                elif state == 'answer':
                    cur['_answer'] = (cur.get('_answer','') or '') + ' '
            continue

        if re_section.match(s):
            pop_question()
            section_name = s
            continue

        m_q = re_qnum.match(s)
        if m_q:
            pop_question()
            cur = {
                '_qnum': int(m_q.group(1)),
                '_content': s[m_q.end():],
                '_options': '',
                '_answer': '',
                '_analysis': '',
                '_detail': '',
                '_highlight': '',
            }
            state = 'content'
            continue

        if cur is None:
            continue

        if state in ('content', 'options'):
            # 检测是否包含选项标记
            opt_match = re_option.search(s)
            if opt_match:
                # 拆开同一行内多个选项（如 A. 1 B. 2 C. 3 D. 4）
                parts = re.split(r'(?=[A-Da-d]\s*[.、，]\s)', s)
                for part in parts:
                    part = part.strip()
                    if part and re_option.match(part):
                        cur['_options'] = (cur['_options'] + '\n' + part).strip()
                state = 'options'
                continue

        if re_answer.match(s):
            cur['_answer'] = s[4:].strip()
            state = 'answer'
            continue

        if s == '【解析】':
            state = 'sol_other'
            continue
        if s.startswith('【解析】'):
            cur['_analysis'] = s[4:].strip()
            state = 'sol_analysis'
            continue

        if re_analysis.match(s):
            cur['_analysis'] = s[4:].strip()
            state = 'sol_analysis'
            continue

        if re_detail.match(s):
            cur['_detail'] = s[4:].strip()
            state = 'sol_detail'
            continue

        if re_highlight.match(s):
            cur['_highlight'] = s[5:].strip()
            state = 'sol_highlight'
            continue

        if state == 'content':
            cur['_content'] = (cur['_content'] + '\n' + s).strip()
        elif state == 'options':
            cur['_options'] = (cur['_options'] + '\n' + s).strip()
        elif state == 'answer':
            cur['_answer'] = (cur['_answer'] + ' ' + s).strip()
        elif state in ('sol_analysis', 'sol_other'):
            cur['_analysis'] = (cur['_analysis'] + '\n' + s).strip()
            state = 'sol_analysis'
        elif state == 'sol_detail':
            cur['_detail'] = (cur['_detail'] + '\n' + s).strip()
        elif state == 'sol_highlight':
            cur['_highlight'] = (cur['_highlight'] + '\n' + s).strip()

    pop_question()
    return questions


# ========= 步骤D: 重编号 [figN] + 分配图片 =========
def assign_and_renumber(questions: list, images_dir: str, total_imgs: int) -> list:
    img_bytes = []
    if os.path.isdir(images_dir):
        files = sorted(f for f in os.listdir(images_dir) if f.endswith('.png') and f != 'image_manifest.json')
        for fname in files:
            with open(os.path.join(images_dir, fname), 'rb') as fh:
                img_bytes.append(fh.read())

    print(f"      读取了 {len(img_bytes)} 张提取的图片")

    img_map = {i+1: base64.b64encode(data).decode('ascii') for i, data in enumerate(img_bytes)}
    re_plh = re.compile(r'\{IMG_(\d+)\}')

    for q in questions:
        content = q['content']
        solution = q['solution']

        # content 中的图 → q.image (逗号拼接)
        content_imgs = list(dict.fromkeys(int(x) for x in re_plh.findall(content)))
        content_images = [img_map[ig] for ig in content_imgs if ig in img_map]
        for i, ig in enumerate(content_imgs):
            tag = '[fig1]' if i == 0 else f'[fig1_{i+1}]'
            content = content.replace(PLACEHOLDER_PREFIX + str(ig) + '}', tag, 1)
        q_image = ','.join(content_images) if content_images else ''

        # solution 中的图 → q.answerImage (逗号拼接)
        solution_imgs = list(dict.fromkeys(int(x) for x in re_plh.findall(solution)))
        solution_images = [img_map[ig] for ig in solution_imgs if ig in img_map]
        for i, ig in enumerate(solution_imgs):
            tag = '[fig2]' if i == 0 else f'[fig2_{i+1}]'
            solution = solution.replace(PLACEHOLDER_PREFIX + str(ig) + '}', tag, 1)
        q_answer_image = ','.join(solution_images) if solution_images else ''

        q['content'] = content
        q['solution'] = solution
        q['image'] = q_image
        q['answerImage'] = q_answer_image

    return questions


def run(ocr_path: str, images_dir: str, output_path: str, source: str):
    print(f"[1/4] 读取OCR + 加载知识树")
    with open(ocr_path, 'r', encoding='utf-8') as f:
        text = f.read()
    id_name_map = load_knowledge_tree()
    print(f"      知识树: {len(id_name_map)} 个知识点")

    print(f"[2/4] [图] → {{IMG_N}} 替换")
    marked_text, total_imgs = replace_fig_markers(text)
    print(f"      替换了 {total_imgs} 个 [图] 标记")

    print(f"[3/4] 正则解析 + 知识点匹配")
    questions = parse_questions(marked_text, source, id_name_map)
    print(f"      解析出 {len(questions)} 道题")
    matched = sum(1 for q in questions if q.get('topicId'))
    print(f"      知识点匹配: {matched}/{len(questions)}")

    print(f"[4/4] 重编号 [figN] + 分配图片")
    questions = assign_and_renumber(questions, images_dir, total_imgs)

    # 统计
    figs_content = sum(len(re.findall(r'\[fig\d+\]', q['content'])) for q in questions)
    figs_solution = sum(len(re.findall(r'\[fig\d+\]', q['solution'])) for q in questions)
    has_image = sum(1 for q in questions if q['image'])
    has_a_image = sum(1 for q in questions if q.get('answerImage',''))

    print(f"\n统计:")
    print(f"  题目总数: {len(questions)}")
    print(f"  content中[fig]: {figs_content}")
    print(f"  solution中[fig]: {figs_solution}")
    print(f"  有题干附图: {has_image}")
    print(f"  有答案附图: {has_a_image}")

    # 验证格式
    issues = []
    for i, q in enumerate(questions):
        img = q.get('image','')
        aimg = q.get('answerImage','')
        if img and img.startswith('data:'):
            issues.append(f"  题#{i+1}: image 含 data: 前缀")
        if aimg and aimg.startswith('data:'):
            issues.append(f"  题#{i+1}: answerImage 含 data: 前缀")
        if '{IMG_' in q.get('content','') or '{IMG_' in q.get('solution',''):
            issues.append(f"  题#{i+1}: 还有未替换的 {{IMG_X}} 标记")
    if issues:
        print(f"\n⚠️ 格式问题:")
        for issue in issues:
            print(issue)
    else:
        print(f"\n✅ 格式验证通过")

    print(f"\n保存到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print("完成!")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    ocr_path = sys.argv[1]
    images_dir = sys.argv[2]
    output_path = sys.argv[3]
    source = sys.argv[4] if len(sys.argv) > 4 else '未命名试卷'

    run(ocr_path, images_dir, output_path, source)
