#!/usr/bin/env python3
"""
更新2024全国甲卷（理）的知识点归类
"""

import json, subprocess, sys

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-web-deploy/scripts/baas.py"

# id → 正确 topicId 映射
# 知识点规则：
# 题不精确匹配任何子知识点 → 只归入该章的"其他"子项（用 {chapter}-OTHER）
# 但知识点树中没有 OTHER 项，所以用子知识点中最匹配的

topic_fix = {
    # 选择题
    3455: 'M2-C2-T2',   # 题1 复数 z=5+i → 复数的四则运算
    3456: 'M1-C1-T3',   # 题2 集合 → 集合的基本运算
    3457: 'M1-C2-T3',   # 题3 线性规划 → 二次函数与一元二次方程、不等式
    3458: 'M4-C1-T2',   # 题4 等差数列 → 等差数列
    3459: 'M3-C3-T2',   # 题5 双曲线 → 双曲线
    3460: 'M4-C2-T1',   # 题6 导数几何意义(切线) → 导数的概念与几何意义
    3461: 'M1-C3-T3',   # 题7 函数图像(奇偶性) → 函数的奇偶性
    3462: 'M1-C5-T6',   # 题8 三角恒等 → 三角恒等变换
    3463: 'M2-C1-T3',   # 题9 向量 → 平面向量基本定理与坐标表示
    3464: 'M2-C3-T3',   # 题10 立体几何(线面平行) → 直线、平面的平行判定与性质
    3465: 'M1-C5-T6',   # 题11 解三角形(正弦余弦定理) → 三角恒等变换
    3466: 'M3-C2-T4',   # 题12 直线与圆 → 直线与圆、圆与圆的位置关系
    # 填空题
    3467: 'M5-C1-T3',   # 题13 二项式定理 → 二项式定理
    3468: 'M2-C3-T5',   # 题14 圆台体积 → 简单几何体的表面积与体积
    3469: 'M1-C4-T2',   # 题15 对数运算 → 对数运算与对数函数
    3470: 'M2-C5-T1',   # 题16 概率 → 随机事件与概率
    # 解答题
    3471: 'M5-C3-T2',   # 题17 独立性检验 → 列联表与独立性检验
    3472: 'M4-C1-T3',   # 题18 等比数列 → 等比数列
    3473: 'M3-C1-T5',   # 题19 立体几何二面角 → 用空间向量研究距离与夹角
    3474: 'M3-C3-T1',   # 题20 椭圆 → 椭圆
    3475: 'M4-C2-T4',   # 题21 导数极值恒成立 → 导数与函数的极值、最值
    3476: 'M3-C2-T3',   # 题22 极坐标(抛物线+直线) → 圆的方程 (其实是抛物线但放在解析几何)
    3477: 'M1-C2-T1',   # 题23 不等式证明 → 不等式的性质
}

# Check topic IDs exist
valid_topics = {
    'M1-C1-T1','M1-C1-T2','M1-C1-T3','M1-C1-T4','M1-C1-T5',
    'M1-C2-T1','M1-C2-T2','M1-C2-T3',
    'M1-C3-T1','M1-C3-T2','M1-C3-T3','M1-C3-T4','M1-C3-T5',
    'M1-C4-T1','M1-C4-T2','M1-C4-T3','M1-C4-T4',
    'M1-C5-T1','M1-C5-T2','M1-C5-T3','M1-C5-T4','M1-C5-T5','M1-C5-T6',
    'M2-C1-T1','M2-C1-T2','M2-C1-T3','M2-C1-T4',
    'M2-C2-T1','M2-C2-T2',
    'M2-C3-T1','M2-C3-T2','M2-C3-T3','M2-C3-T4','M2-C3-T5',
    'M2-C4-T1','M2-C4-T2',
    'M2-C5-T1','M2-C5-T2','M2-C5-T3',
    'M3-C1-T1','M3-C1-T2','M3-C1-T3','M3-C1-T4','M3-C1-T5',
    'M3-C2-T1','M3-C2-T2','M3-C2-T3','M3-C2-T4',
    'M3-C3-T1','M3-C3-T2','M3-C3-T3',
    'M4-C1-T1','M4-C1-T2','M4-C1-T3','M4-C1-T4',
    'M4-C2-T1','M4-C2-T2','M4-C2-T3','M4-C2-T4','M4-C2-T5',
    'M5-C1-T1','M5-C1-T2','M5-C1-T3',
    'M5-C2-T1','M5-C2-T2','M5-C2-T3','M5-C2-T4',
    'M5-C3-T1','M5-C3-T2',
}

for rid, tid in topic_fix.items():
    if tid not in valid_topics:
        print(f'⚠️  {rid} → {tid} 不在知识点树中!')
        sys.exit(1)

print('✅ 所有 topicId 校验通过')

success = 0
fail = 0

for rid, new_topic in topic_fix.items():
    payload = json.dumps({
        'table': 'questions',
        'method': 'update',
        'apiKey': 'baas_ZiRfZlhr',
        'tableData': {
            'id': rid,
            'topicId': new_topic
        }
    })
    
    cmd = ['python3', BAAS_SCRIPT, '--x-api-type', 'tableAddData', '--content', payload]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if '"code":"0"' in r.stdout or 'success' in r.stdout.lower():
            success += 1
            print(f'  ✅ id={rid} → {new_topic}', flush=True)
        else:
            fail += 1
            print(f'  ❌ id={rid}: {r.stdout[:150]}', flush=True)
    except Exception as e:
        fail += 1
        print(f'  ❌ id={rid}: {e}', flush=True)

print(f'\n✅ 更新完成: 成功={success}, 失败={fail}')
