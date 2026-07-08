#!/usr/bin/env python3
"""
将 LLM 输出的知识点/难度分类结果合并回 JSON。

用法：
  python3 merge_llm_classification.py <questions.json> <llm_result.txt> <output.json>

LLM 输出格式：
  第 1 题  知识点：M2-C2-T2  难度：中等
  第1题  知识点:M2-C2-T2  难度:中等
"""
import re, json, sys

def parse_llm_result(path: str) -> dict:
    """解析 LLM 输出，返回 {题号: {'topicId': str, 'difficulty': str}}"""
    result = {}
    # 宽松匹配：第(空格)(数字)(题)(空格)知识XX(空格)难度XX
    re_line = re.compile(r'第\s*(\d+)\s*题.*?知识[点]?\s*[：:]\s*([A-Za-z0-9_-]+)\s*.*?难度\s*[：:]\s*(.+)')
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            m = re_line.search(line)
            if m:
                qnum = int(m.group(1))
                topic_id = m.group(2).strip()
                difficulty = m.group(3).strip()
                diff_map = {'简单': '基础', '基础': '基础', '中等': '中等', '困难': '困难', '较难': '困难'}
                difficulty = diff_map.get(difficulty, difficulty)
                result[qnum] = {'topicId': topic_id, 'difficulty': difficulty}
    return result


def merge(questions_path: str, llm_result_path: str, output_path: str):
    print(f"读取题目 JSON: {questions_path}")
    with open(questions_path, 'r', encoding='utf-8') as f:
        questions = json.load(f)

    print(f"读取 LLM 结果: {llm_result_path}")
    meta_map = parse_llm_result(llm_result_path)
    print(f"  解析了 {len(meta_map)} 题标注")

    applied = 0
    for i, q in enumerate(questions):
        qnum = i + 1
        if qnum in meta_map:
            if meta_map[qnum].get('topicId'):
                q['topicId'] = meta_map[qnum]['topicId']
            if meta_map[qnum].get('difficulty'):
                q['difficulty'] = meta_map[qnum]['difficulty']
            applied += 1
        
        # 统一 tags：确保包含 source 前缀和 number:X
        src = q.get('source', '')
        tags = q.get('tags', '') or ''
        qnum_str = f'number:{qnum}'
        new_tags = ''
        if src:
            new_tags = src
        if tags:
            # 从 tags 提取现有的 number:X（如果有）
            m_num = re.search(r'number:\d+', tags)
            if m_num:
                # 保留旧的 number，不替换
                new_tags = src + ',' + tags if src else tags
            else:
                if new_tags:
                    new_tags += ',' + qnum_str
                else:
                    new_tags = qnum_str
        else:
            new_tags = (src + ',' if src else '') + qnum_str
        q['tags'] = new_tags

    print(f"  合并了 {applied} 题")
    if applied < len(questions):
        print(f"  ⚠️ {len(questions) - applied} 题未匹配到标注")

    print(f"保存到: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    print("完成!")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("用法: python3 merge_llm_classification.py <questions.json> <llm_result.txt> <output.json>")
        sys.exit(1)
    merge(sys.argv[1], sys.argv[2], sys.argv[3])
