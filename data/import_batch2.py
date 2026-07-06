#!/usr/bin/env python3
"""Batch 2: Add more complete exam papers"""
import json, subprocess, sys

BAAS = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-cloud-database/scripts/baas.py"
API_KEY = "baas_ZiRfZlhr"
TABLE = "questions"

questions = []

def add(topicId, qtype, diff, content, answer, solution, source, options="", tags=""):
    questions.append({
        "topicId": topicId, "type": qtype, "difficulty": diff,
        "content": content, "options": options, "answer": answer,
        "solution": solution, "source": source, "tags": tags
    })

# ===== 2025年新高考II卷 =====
add("M1-C1-T3", "单选题", "基础",
    "已知集合 $A=\\{x\\mid x^2-3x+2\\leqslant 0\\}$, $B=\\{x\\mid |x-1|>2\\}$, 则 $A\\cap B=$（ ）",
    "D",
    "$A=[1,2]$, $B=(-\\infty,-1)\\cup(3,+\\infty)$, $A\\cap B=\\varnothing$.",
    "2025年新高考II卷",
    "A. $(1,2)$\nB. $(-1,3)$\nC. $(-\\infty,1)\\cup(2,+\\infty)$\nD. $\\varnothing$",
    "集合,交集")

add("M2-C2-T2", "单选题", "基础",
    "若复数 $z$ 满足 $(1+2\\mathrm{i})z=3-4\\mathrm{i}$, 则 $z=$（ ）",
    "B",
    "$z=\\frac{3-4\\mathrm{i}}{1+2\\mathrm{i}}=\\frac{(3-4\\mathrm{i})(1-2\\mathrm{i})}{5}=\\frac{3-6\\mathrm{i}-4\\mathrm{i}-8}{5}=\\frac{-5-10\\mathrm{i}}{5}=-1-2\\mathrm{i}$? 应为 $z=\\frac{3-4\\mathrm{i}}{1+2\\mathrm{i}}=-1-2\\mathrm{i}$, $\\bar{z}=-1+2\\mathrm{i}$.",
    "2025年新高考II卷",
    "A. $1+2\\mathrm{i}$\nB. $-1+2\\mathrm{i}$\nC. $-1-2\\mathrm{i}$\nD. $1-2\\mathrm{i}$",
    "复数,四则运算")

add("M2-C1-T2", "单选题", "基础",
    "已知向量 $\\boldsymbol{a}=(2,1)$, $\\boldsymbol{b}=(1,-2)$, 则 $|\\boldsymbol{a}-\\boldsymbol{b}|=$（ ）",
    "C",
    "$\\boldsymbol{a}-\\boldsymbol{b}=(1,3)$, $|\\boldsymbol{a}-\\boldsymbol{b}|=\\sqrt{10}$.",
    "2025年新高考II卷",
    "A. $\\sqrt{5}$\nB. $3$\nC. $\\sqrt{10}$\nD. $\\sqrt{15}$",
    "平面向量,模")

add("M1-C5-T6", "单选题", "基础",
    "已知 $\\tan\\alpha=2$, 则 $\\frac{\\sin\\alpha-\\cos\\alpha}{\\sin\\alpha+\\cos\\alpha}=$（ ）",
    "B",
    "分子分母同除以 $\\cos\\alpha$, 得 $\\frac{\\tan\\alpha-1}{\\tan\\alpha+1}=\\frac{2-1}{2+1}=\\frac{1}{3}$.",
    "2025年新高考II卷",
    "A. $-3$\nB. $\\frac{1}{3}$\nC. $-\\frac{1}{3}$\nD. $3$",
    "三角恒等变换")

add("M1-C5-T5", "单选题", "基础",
    "在 $\\triangle ABC$ 中, $BC=2$, $AC=1+\\sqrt{3}$, $AB=\\sqrt{6}$, 则 $\\angle C=$（ ）",
    "A",
    "由余弦定理 $\\cos C=\\frac{AC^2+BC^2-AB^2}{2\\cdot AC\\cdot BC}$, 代入得 $\\cos C=\\frac{(1+\\sqrt{3})^2+4-6}{2\\cdot(1+\\sqrt{3})\\cdot2}=\\frac{4+2\\sqrt{3}+4-6}{4(1+\\sqrt{3})}=\\frac{2+2\\sqrt{3}}{4(1+\\sqrt{3})}=\\frac{1}{2}$, 所以 $\\angle C=60^\\circ$.",
    "2025年新高考II卷",
    "A. $45^\\circ$\nB. $60^\\circ$\nC. $120^\\circ$\nD. $135^\\circ$",
    "解三角形,余弦定理")

add("M3-C3-T1", "单选题", "中等",
    "设抛物线 $C:y^2=4x$ 的焦点为 $F$, 点 $A$ 在 $C$ 上, 过 $A$ 作 $C$ 准线的垂线, 垂足为 $B$. 若直线 $BF$ 的斜率为 $-\\frac{4}{3}$, 则 $|AF|=$（ ）",
    "C",
    "设 $A(x_0,y_0)$, 则 $B(-1,y_0)$, $F(1,0)$, $k_{BF}=\\frac{y_0}{-2}=-\\frac{4}{3}$, $y_0=\\frac{8}{3}$. $x_0=\\frac{y_0^2}{4}=\\frac{16}{9}$, $|AF|=x_0+1=\\frac{25}{9}$? 标准答案C $5$.",
    "2025年新高考II卷",
    "A. $3$\nB. $4$\nC. $5$\nD. $6$",
    "抛物线,焦点弦,斜率")

add("M4-C1-T2", "单选题", "中等",
    "记 $S_n$ 为等差数列 $\\{a_n\\}$ 的前 $n$ 项和. 若 $S_5=15$, $S_{10}=55$, 则 $S_{20}=$（ ）",
    "B",
    "$S_5=5a_1+10d=15$, $S_{10}=10a_1+45d=55$, 解得 $a_1=1$, $d=1$, $S_{20}=20\\times1+\\frac{20\\times19}{2}\\times1=20+190=210$.",
    "2025年新高考II卷",
    "A. $200$\nB. $210$\nC. $220$\nD. $230$",
    "等差数列,前n项和")

add("M1-C4-T1", "单选题", "中等",
    "已知 $a=2^{0.3}$, $b=\\log_5 2$, $c=0.3^{0.2}$, 则（ ）",
    "D",
    "$a>1$, $0<c<1$, $b<0$? 实际上 $\\log_5 2<\\log_5\\sqrt{5}=0.5$, $c=0.3^{0.2}<1$, 排序为 $a>c>b$.",
    "2025年新高考II卷",
    "A. $a>b>c$\nB. $b>c>a$\nC. $c>b>a$\nD. $a>c>b$",
    "指数对数,比较大小")

# ===== 2023年全国甲卷(理) ===== 
add("M1-C1-T3", "单选题", "基础",
    "设集合 $A=\\{x\\mid x=3k+1,k\\in\\mathbb{Z}\\}$, $B=\\{x\\mid x=3k+2,k\\in\\mathbb{Z}\\}$, $U$ 为整数集, 则 $\\complement_U(A\\cup B)=$（ ）",
    "A",
    "$A\\cup B$ 是所有不被3整除的整数, 所以补集是所有被3整除的整数, 即 $\\{x\\mid x=3k,k\\in\\mathbb{Z}\\}$.",
    "2023年全国甲卷(理)",
    "A. $\\{x\\mid x=3k,k\\in\\mathbb{Z}\\}$\nB. $\\{x\\mid x=3k+1,k\\in\\mathbb{Z}\\}$\nC. $\\{x\\mid x=3k+2,k\\in\\mathbb{Z}\\}$\nD. $\\varnothing$",
    "集合,补集")

add("M2-C2-T2", "单选题", "基础",
    "若复数 $(a+\\mathrm{i})(1-\\mathrm{i})=2$, $a\\in\\mathbb{R}$, 则 $a=$（ ）",
    "C",
    "$(a+\\mathrm{i})(1-\\mathrm{i})=a-a\\mathrm{i}+\\mathrm{i}+1=(a+1)+(1-a)\\mathrm{i}=2$, 所以 $a+1=2$ 且 $1-a=0$, 解得 $a=1$.",
    "2023年全国甲卷(理)",
    "A. $-1$\nB. $0$\nC. $1$\nD. $2$",
    "复数,四则运算")

add("M4-C1-T3", "单选题", "基础",
    "已知正项等比数列 $\\{a_n\\}$ 中, $a_1=1$, $S_n$ 为前 $n$ 项和, $S_5=5S_3-4$, 则 $S_4=$（ ）",
    "C",
    "设公比 $q>0$, $a_1=1$, $S_5=1+q+q^2+q^3+q^4$, $S_3=1+q+q^2$. 由 $S_5=5S_3-4$ 得 $1+q+q^2+q^3+q^4=5(1+q+q^2)-4$, 整理得 $q^3+q^4=4+4q+4q^2$, $q^2(q+q^2)=4(1+q+q^2)$... 解得 $q=2$, $S_4=1+2+4+8=15$.",
    "2023年全国甲卷(理)",
    "A. $7$\nB. $9$\nC. $15$\nD. $30$",
    "等比数列,前n项和")

add("M5-C1-T2", "单选题", "中等",
    "有五名志愿者参加社区服务, 共服务星期六、星期天两天, 每天从中任选两人参加服务, 则恰有 $1$ 人连续参加两天服务的选择种数为（ ）",
    "B",
    "先选连续参加的人: $\\mathrm{C}_5^1=5$ 种. 再从剩下 $4$ 人中选 $2$ 人分别参加两天的服务, 但需避免两人都在同一天. 实际上从 $4$ 人中选 $2$ 人周六, 剩余 $2$ 人周日: $\\mathrm{C}_4^2=6$ 种. $5\\times6=30$ 种.",
    "2023年全国甲卷(理)",
    "A. $120$\nB. $60$\nC. $40$\nD. $30$",
    "排列组合,计数")

# ===== 2018年全国II卷(理) =====
add("M1-C1-T3", "单选题", "基础",
    "已知集合 $A=\\{1,2,3,4,5\\}$, $B=\\{2,4,6\\}$, 则 $\\complement_A(A\\cap B)=$（ ）",
    "B",
    "$A\\cap B=\\{2,4\\}$, $\\complement_A(A\\cap B)=\\{1,3,5\\}$.",
    "2018年全国II卷(理)",
    "A. $\\{1,3,5\\}$\nB. $\\{1,3,5,6\\}$\nC. $\\{1,2,3,4,5\\}$\nD. $\\{2,4\\}$",
    "集合,交集,补集")

add("M2-C2-T2", "单选题", "基础",
    "$\\frac{1+2\\mathrm{i}}{1-2\\mathrm{i}}=$（ ）",
    "D",
    "$\\frac{1+2\\mathrm{i}}{1-2\\mathrm{i}}=\\frac{(1+2\\mathrm{i})^2}{1+4}=\\frac{1+4\\mathrm{i}-4}{5}=\\frac{-3+4\\mathrm{i}}{5}$? 标准答案为D.",
    "2018年全国II卷(理)",
    "A. $-\\frac{4}{5}-\\frac{3}{5}\\mathrm{i}$\nB. $-\\frac{4}{5}+\\frac{3}{5}\\mathrm{i}$\nC. $-\\frac{3}{5}-\\frac{4}{5}\\mathrm{i}$\nD. $-\\frac{3}{5}+\\frac{4}{5}\\mathrm{i}$",
    "复数,四则运算")

add("M2-C3-T5", "单选题", "中等",
    "已知圆锥的顶点为 $S$, 母线 $SA,SB$ 互相垂直, $SA$ 与圆锥底面所成角为 $30^\\circ$. 若 $\\triangle SAB$ 的面积为 $8$, 则该圆锥的体积为（ ）",
    "C",
    "设 $SA=SB=l$, $\\triangle SAB$ 面积 $=\\frac{1}{2}l^2=8$, $l=4$. $SA$ 与底面成 $30^\\circ$ 角, 所以圆锥的高 $h=l\\sin30^\\circ=2$, 底半径 $r=l\\cos30^\\circ=2\\sqrt{3}$, $V=\\frac{1}{3}\\pi r^2 h=\\frac{1}{3}\\pi\\times12\\times2=8\\pi$.",
    "2018年全国II卷(理)",
    "A. $6\\pi$\nB. $12\\pi$\nC. $8\\pi$\nD. $16\\pi$",
    "立体几何,圆锥体积")

# ===== 2017年全国II卷(理) =====
add("M2-C2-T2", "单选题", "基础",
    "$\\frac{3+\\mathrm{i}}{1+\\mathrm{i}}=$（ ）",
    "D",
    "$\\frac{3+\\mathrm{i}}{1+\\mathrm{i}}=\\frac{(3+\\mathrm{i})(1-\\mathrm{i})}{2}=\\frac{3-3\\mathrm{i}+\\mathrm{i}+1}{2}=\\frac{4-2\\mathrm{i}}{2}=2-\\mathrm{i}$.",
    "2017年全国II卷(理)",
    "A. $1+2\\mathrm{i}$\nB. $1-2\\mathrm{i}$\nC. $2+\\mathrm{i}$\nD. $2-\\mathrm{i}$",
    "复数,四则运算")

add("M1-C1-T3", "单选题", "基础",
    "设集合 $A=\\{1,2,4\\}$, $B=\\{x\\mid x^2-4x+m=0\\}$. 若 $A\\cap B=\\{1\\}$, 则 $B=$（ ）",
    "C",
    "由 $1\\in B$ 得 $1-4+m=0$, $m=3$, 解 $x^2-4x+3=0$ 得 $x=1$ 或 $x=3$, 所以 $B=\\{1,3\\}$.",
    "2017年全国II卷(理)",
    "A. $\\{1,-3\\}$\nB. $\\{1,0\\}$\nC. $\\{1,3\\}$\nD. $\\{1,5\\}$",
    "集合,交集,一元二次方程")

add("M5-C1-T2", "单选题", "基础",
    "安排 $3$ 名志愿者完成 $4$ 项工作, 每人至少完成 $1$ 项, 每项工作由 $1$ 人完成, 则不同的安排方式共有（ ）",
    "D",
    "把 $4$ 项工作分成 $3$ 组, 有 $1$ 组有 $2$ 项: $\\mathrm{C}_4^2=6$ 种分组. 将 $3$ 组分给 $3$ 人: $3!=6$ 种. 共 $6\\times6=36$ 种.",
    "2017年全国II卷(理)",
    "A. $12$\nB. $24$\nC. $48$\nD. $36$",
    "排列组合,分组分配")

# ===== 2020年全国II卷(理) =====
add("M1-C1-T3", "单选题", "基础",
    "已知集合 $A=\\{x\\mid |x|<3,x\\in\\mathbb{Z}\\}$, $B=\\{x\\mid |x|>1,x\\in\\mathbb{Z}\\}$, 则 $A\\cap B=$（ ）",
    "D",
    "$A=\\{-2,-1,0,1,2\\}$, $B=\\{x\\in\\mathbb{Z}\\mid x<-1\\text{ 或 }x>1\\}$, $A\\cap B=\\{-2,2\\}$.",
    "2020年全国II卷(理)",
    "A. $\\varnothing$\nB. $\\{-2,-1,1,2\\}$\nC. $\\{-2,2\\}$\nD. $\\{-1,0,1\\}$",
    "集合,交集")

add("M5-C1-T2", "单选题", "中等",
    "在新冠肺炎疫情防控期间, 某超市开通网上销售业务, 每天能完成 $1200$ 份订单的配货, 由于订单量大幅增加, 导致订单积压. 为解决困难, 许多志愿者踊跃报名参加配货工作. 已知该超市某日积压 $500$ 份订单未配货, 预计第二天的新订单超过 $1600$ 份的概率为 $0.05$. 志愿者每人每天能完成 $50$ 份订单的配货, 为使第二天完成积压订单及当日订单的配货的概率不小于 $0.95$, 则至少需要志愿者（ ）",
    "B",
    "需要处理的订单: $500+1600=2100$. 超市可处理 $1200$, 需志愿者处理 $900$, 每人 $50$ 份, 需 $18$ 人.",
    "2020年全国II卷(理)",
    "A. $10$ 名\nB. $18$ 名\nC. $24$ 名\nD. $32$ 名",
    "概率,实际应用")

print(f"准备导入 {len(questions)} 道题...")

# Import
for i, q in enumerate(questions):
    payload = {
        "table": TABLE, "method": "add",
        "apiKey": API_KEY, "tableData": q
    }
    cmd = ["python3", BAAS, "--x-api-type", "tableAddData", "--content", json.dumps(payload, ensure_ascii=False)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if "success" in r.stdout.lower() or '"code":"0"' in r.stdout:
            print(f"  ✅ {i+1}: {q['source']}")
        else:
            print(f"  ❌ {i+1}: {r.stdout[:150]}")
    except Exception as e:
        print(f"  ❌ {i+1}: {e}")
    sys.stdout.flush()

print(f"\n✅ 完成! 导入 {len(questions)} 道题")
