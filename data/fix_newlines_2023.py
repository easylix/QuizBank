#!/usr/bin/env python3
"""
修复2023全国乙卷理题目中的多余空行
从数据库取出已有数据 → 压缩换行 → 更新回数据库
"""
import re, sys, json
import urllib.request

API_BASE = "http://127.0.0.1:5000"

def api_post(path, data):
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

# 1. 查所有题目
res = api_post("/api/query", {"method": "list", "limit": 1000})

if not res.get("success"):
    print(f"❌ 查询失败: {res}")
    sys.exit(1)

all_qs = res.get("data", [])
target = [q for q in all_qs if "2023全国乙卷理" in (q.get("source") or "")]

print(f"找到 {len(target)} 道2023全国乙卷理的题目")

updated = 0
for q in target:
    qid = q["id"]
    changes = {}
    
    # 压缩content
    old_content = q.get("content", "") or ""
    new_content = re.sub(r'\n{2,}', '\n', old_content).strip()
    if new_content != old_content:
        changes["content"] = new_content
    
    # 压缩solution
    old_sol = q.get("solution", "") or ""
    # 注意：保留【分析】\n【详解】之间的单换行，只压缩连续2+换行
    new_sol = re.sub(r'\n{2,}', '\n', old_sol).strip()
    if new_sol != old_sol:
        changes["solution"] = new_sol
    
    # 压缩answer（一般没有换行，但保底）
    old_ans = q.get("answer", "") or ""
    new_ans = re.sub(r'\n{2,}', '\n', old_ans).strip()
    if new_ans != old_ans:
        changes["answer"] = new_ans
    
    # 修复选项：ABCD选项如果在同一行，拆分为每行一个选项
    old_opts = q.get("options", "") or ""
    if old_opts:
        # 如果选项行数太少（<3行），说明可能是单行拼接
        lines = old_opts.split('\n')
        if len(lines) <= 2:
            new_opts = re.sub(r'(?<=[.．、])\s+(?=[A-F]\s*[.．、])', '\n', old_opts).strip()
            new_opts = re.sub(r'\n{2,}', '\n', new_opts).strip()
            if new_opts != old_opts and len(new_opts.split('\n')) >= 3:
                changes["options"] = new_opts
    
    if not changes:
        num_tag = ''
        if 'number:' in (q.get("tags") or ""):
            num_tag = q["tags"].split("number:")[1].split(",")[0]
        print(f"  ID {qid} 题{num_tag}：无变化")
        continue
    
    # 更新
    update_data = {"id": qid, **changes}
    r = api_post("/api/query", {"method": "update", "tableData": update_data})
    if r.get("success"):
        updated += 1
        num = ""
        if "number:" in (q.get("tags") or ""):
            num = q["tags"].split("number:")[1].split(",")[0]
        print(f"  ✅ ID {qid} 题{num}：{' '.join(changes.keys())} 已更新")
    else:
        num = ""
        if "number:" in (q.get("tags") or ""):
            num = q["tags"].split("number:")[1].split(",")[0]
        print(f"  ❌ ID {qid} 题{num}：更新失败 {r}")

print(f"\n总计：{len(target)} 题，更新 {updated} 题")
