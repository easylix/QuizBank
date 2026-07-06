#!/usr/bin/env python3
"""
2024全国甲卷（理）视觉AI识别结果 → 数据库导入器
"""

import re, json, sys, os, subprocess

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-web-deploy/scripts/baas.py"

# ============================================================
# 从视觉AI识别结果中提取的题目数据（逐字忠实还原）
# ============================================================

questions_data = [
    {
        "qnum": "1",
        "type": "单选题",
        "content": "设 $z=5+\\mathrm{i}$，则 $\\mathrm{i}\\left(\\bar{z}+z\\right)=$ （ ）",
        "options": "A. $10\\mathrm{i}$\nB. $2\\mathrm{i}$\nC. $10$\nD. $-2$",
        "answer": "A",
        "solution": "【分析】结合共轭复数与复数的基本运算直接求解.\n【详解】由 $z=5+\\mathrm{i} \\Rightarrow \\bar{z}=5-\\mathrm{i}, z+\\bar{z}=10$，则 $\\mathrm{i}\\left(\\bar{z}+z\\right)=10\\mathrm{i}$.\n故选：A"
    },
    {
        "qnum": "2",
        "type": "单选题",
        "content": "集合 $A=\\{1,2,3,4,5,9\\}, B=\\left\\{x \\mid \\sqrt{x} \\in A\\right\\}$，则 $\\complement_{A}(A \\cap B)=$ （ ）",
        "options": "A. $\\{1,4,9\\}$\nB. $\\{3,4,9\\}$\nC. $\\{1,2,3\\}$\nD. $\\{2,3,5\\}$",
        "answer": "D",
        "solution": "【分析】由集合 $B$ 的定义求出 $B$，结合交集与补集运算即可求解.\n【详解】因为 $A=\\{1,2,3,4,5,9\\}, B=\\left\\{x \\mid \\sqrt{x} \\in A\\right\\}$，所以 $B=\\{1,4,9,16,25,81\\}$，\n则 $A \\cap B=\\{1,4,9\\}$，$\\complement_{A}(A \\cap B)=\\{2,3,5\\}$\n故选：D"
    },
    {
        "qnum": "3",
        "type": "单选题",
        "content": "若实数 $x,y$ 满足约束条件 $\\begin{cases} 4x-3y-3 \\ge 0 \\\\ x-2y-2 \\le 0 \\\\ 2x+6y-9 \\le 0 \\end{cases}$，则 $z=x-5y$ 的最小值为（ ）",
        "options": "A. $5$\nB. $\\frac{1}{2}$\nC. $-2$\nD. $-\\frac{7}{2}$",
        "answer": "D",
        "solution": "【分析】画出可行域后，利用 $z$ 的几何意义计算即可得.\n【详解】实数 $x,y$ 满足 $\\begin{cases} 4x-3y-3 \\ge 0 \\\\ x-2y-2 \\le 0 \\\\ 2x+6y-9 \\le 0 \\end{cases}$，作出可行域如图：\n由 $z=x-5y$ 可得 $y=\\frac{1}{5}x-\\frac{1}{5}z$，\n即 $z$ 的几何意义为 $y=\\frac{1}{5}x-\\frac{1}{5}z$ 的截距的 $-\\frac{1}{5}$，\n则该直线截距取最大值时，$z$ 有最小值，\n此时直线 $y=\\frac{1}{5}x-\\frac{1}{5}z$ 过点 A，\n联立 $\\begin{cases} 4x-3y-3=0 \\\\ 2x+6y-9=0 \\end{cases}$，解得 $\\begin{cases} x=\\frac{3}{2} \\\\ y=1 \\end{cases}$，即 $A\\left(\\frac{3}{2}, 1\\right)$，\n则 $z_{\\min}=\\frac{3}{2}-5 \\times 1=-\\frac{7}{2}$.\n故选：D."
    },
    {
        "qnum": "4",
        "type": "单选题",
        "content": "等差数列 $\\{a_n\\}$ 的前 $n$ 项和为 $S_n$，若 $S_5=S_{10}$，$a_5=1$，则 $a_1=$ （ ）",
        "options": "A. $-2$\nB. $\\frac{7}{3}$\nC. $1$\nD. $2$",
        "answer": "B",
        "solution": "【分析】由 $S_5=S_{10}$ 结合等差中项的性质可得 $a_8=0$，即可计算出公差，即可得 $a_1$ 的值.\n【详解】由 $S_{10}-S_5=a_6+a_7+a_8+a_9+a_{10}=5a_8=0$，则 $a_8=0$，\n则等差数列 $\\{a_n\\}$ 的公差 $d=\\frac{a_8-a_5}{3}=-\\frac{1}{3}$，故 $a_1=a_5-4d=1-4 \\times \\left(-\\frac{1}{3}\\right)=\\frac{7}{3}$.\n故选：B."
    },
    {
        "qnum": "5",
        "type": "单选题",
        "content": "已知双曲线 $C: \\frac{y^2}{a^2}-\\frac{x^2}{b^2}=1(a>0,b>0)$ 的上、下焦点分别为 $F_1(0,4), F_2(0,-4)$，点 $P(-6,4)$ 在该双曲线上，则该双曲线的离心率为（ ）",
        "options": "A. $4$\nB. $3$\nC. $2$\nD. $\\sqrt{2}$",
        "answer": "C",
        "solution": "【分析】由焦点坐标可得焦距 $2c$，结合双曲线定义计算可得 $2a$，即可得离心率.\n【详解】由题意，$F_1(0,-4)$、$F_2(0,4)$、$P(-6,4)$，\n则 $|F_1F_2|=2c=8$，$|PF_1|=\\sqrt{6^2+(4+4)^2}=10$，$|PF_2|=\\sqrt{6^2+(4-4)^2}=6$，\n则 $2a=|PF_1|-|PF_2|=10-6=4$，则 $e=\\frac{2c}{2a}=\\frac{8}{4}=2$.\n故选：C."
    },
    {
        "qnum": "6",
        "type": "单选题",
        "content": "设函数 $f(x)=\\frac{\\mathrm{e}^x+2\\sin x}{1+x^2}$，则曲线 $y=f(x)$ 在 $(0,1)$ 处的切线与两坐标轴围成的三角形的面积为（ ）",
        "options": "A. $\\frac{1}{6}$\nB. $\\frac{1}{3}$\nC. $\\frac{1}{2}$\nD. $\\frac{2}{3}$",
        "answer": "A",
        "solution": "【分析】借助导数的几何意义计算可得其在点 $(0,1)$ 处的切线方程，即可得其与坐标轴交点坐标，即可得其面积.\n【详解】$f'(x)=\\frac{\\left(\\mathrm{e}^x+2\\cos x\\right)\\left(1+x^2\\right)-\\left(\\mathrm{e}^x+2\\sin x\\right) \\cdot 2x}{\\left(1+x^2\\right)^2}$，\n则 $f'(0)=\\frac{\\left(\\mathrm{e}^0+2\\cos 0\\right)(1+0)-\\left(\\mathrm{e}^0+2\\sin 0\\right) \\times 0}{(1+0)^2}=3$，\n即该切线方程为 $y-1=3x$，即 $y=3x+1$，\n令 $x=0$，则 $y=1$，令 $y=0$，则 $x=-\\frac{1}{3}$，\n故该切线与两坐标轴所围成的三角形面积 $S=\\frac{1}{2} \\times 1 \\times \\left|-\\frac{1}{3}\\right|=\\frac{1}{6}$.\n故选：A."
    },
    {
        "qnum": "7",
        "type": "单选题",
        "content": "函数 $f(x)=-x^2+\\left(\\mathrm{e}^x-\\mathrm{e}^{-x}\\right)\\sin x$ 在区间 $[-2.8,2.8]$ 的大致图像为（ ）",
        "options": "",
        "answer": "B",
        "solution": "【分析】利用函数的奇偶性可排除 A、C，代入 $x=1$ 可得 $f(1)>0$，可排除 D.\n【详解】$f(-x)=-x^2+\\left(\\mathrm{e}^{-x}-\\mathrm{e}^x\\right)\\sin(-x)=-x^2+\\left(\\mathrm{e}^x-\\mathrm{e}^{-x}\\right)\\sin x=f(x)$，\n又函数定义域为 $[-2.8,2.8]$，故该函数为偶函数，可排除 A、C，\n又 $f(1)=-1+\\left(\\mathrm{e}-\\frac{1}{\\mathrm{e}}\\right)\\sin 1 > -1+\\left(\\mathrm{e}-\\frac{1}{\\mathrm{e}}\\right)\\sin \\frac{\\pi}{6} = \\frac{\\mathrm{e}}{2}-1-\\frac{1}{2\\mathrm{e}} > \\frac{1}{4}-\\frac{1}{2\\mathrm{e}} > 0$，\n故可排除 D.\n故选：B."
    },
    {
        "qnum": "8",
        "type": "单选题",
        "content": "已知 $\\frac{\\cos \\alpha}{\\cos \\alpha-\\sin \\alpha}=\\sqrt{3}$，则 $\\tan \\left(\\alpha+\\frac{\\pi}{4}\\right)=$ （ ）",
        "options": "A. $2\\sqrt{3}+1$\nB. $2\\sqrt{3}-1$\nC. $\\frac{\\sqrt{3}}{2}$\nD. $1-\\sqrt{3}$",
        "answer": "B",
        "solution": "【分析】先将 $\\frac{\\cos \\alpha}{\\cos \\alpha-\\sin \\alpha}$ 弦化切求得 $\\tan \\alpha$，再根据两角和的正切公式即可求解.\n【详解】因为 $\\frac{\\cos \\alpha}{\\cos \\alpha-\\sin \\alpha}=\\sqrt{3}$，\n所以 $\\frac{1}{1-\\tan \\alpha}=\\sqrt{3}$，$\\Rightarrow \\tan \\alpha=1-\\frac{\\sqrt{3}}{3}$，\n所以 $\\tan \\left(\\alpha+\\frac{\\pi}{4}\\right)=\\frac{\\tan \\alpha+1}{1-\\tan \\alpha}=2\\sqrt{3}-1$，\n故选：B."
    },
    {
        "qnum": "9",
        "type": "单选题",
        "content": "已知向量 $\\vec{a}=(x+1, x), \\vec{b}=(x, 2)$，则（ ）",
        "options": "A. \"$x=-3$\" 是 \"$\\vec{a} \\perp \\vec{b}$\" 的必要条件\nB. \"$x=-3$\" 是 \"$\\vec{a} // \\vec{b}$\" 的必要条件\nC. \"$x=0$\" 是 \"$\\vec{a} \\perp \\vec{b}$\" 的充分条件\nD. \"$x=-1+\\sqrt{3}$\" 是 \"$\\vec{a} // \\vec{b}$\" 的充分条件",
        "answer": "C",
        "solution": "【分析】根据向量垂直和平行的坐标表示即可得到方程，解出即可.\n【详解】对 A，当 $\\vec{a} \\perp \\vec{b}$ 时，则 $\\vec{a} \\cdot \\vec{b}=0$，\n所以 $x \\cdot (x+1)+2x=0$，解得 $x=0$ 或 $-3$，即必要性不成立，故 A 错误；\n对 C，当 $x=0$ 时，$\\vec{a}=(1,0), \\vec{b}=(0,2)$，故 $\\vec{a} \\cdot \\vec{b}=0$，\n所以 $\\vec{a} \\perp \\vec{b}$，即充分性成立，故 C 正确；\n对 B，当 $\\vec{a} // \\vec{b}$ 时，则 $2(x+1)=x^2$，解得 $x=1 \\pm \\sqrt{3}$，即必要性不成立，故 B 错误；\n对 D，当 $x=-1+\\sqrt{3}$ 时，不满足 $2(x+1)=x^2$，所以 $\\vec{a} // \\vec{b}$ 不成立，即充分性不立，故 D 错误.\n故选：C."
    },
    {
        "qnum": "10",
        "type": "单选题",
        "content": "设 $\\alpha$、$\\beta$ 是两个平面，$m$、$n$ 是两条直线，且 $\\alpha \\cap \\beta=m$. 下列四个命题：\n①若 $m // n$，则 $n // \\alpha$ 或 $n // \\beta$\n②若 $m \\perp n$，则 $n \\perp \\alpha, n \\perp \\beta$\n③若 $n // \\alpha$，且 $n // \\beta$，则 $m // n$\n④若 $n$ 与 $\\alpha$ 和 $\\beta$ 所成的角相等，则 $m \\perp n$\n其中所有真命题的编号是（ ）",
        "options": "A. ①③\nB. ②④\nC. ①②③\nD. ①③④",
        "answer": "A",
        "solution": "【分析】根据线面平行的判定定理即可判断①；举反例即可判断②④；根据线面平行的性质即可判断③.\n【详解】对①，当 $n \\subset \\alpha$，因为 $m // n$，$m \\subset \\beta$，则 $n // \\beta$，\n当 $n \\subset \\beta$，因为 $m // n$，$m \\subset \\alpha$，则 $n // \\alpha$，\n当 $n$ 既不在 $\\alpha$ 也不在 $\\beta$ 内，因为 $m // n$，$m \\subset \\alpha, m \\subset \\beta$，则 $n // \\alpha$ 且 $n // \\beta$，故①正确；\n对②，若 $m \\perp n$，则 $n$ 与 $\\alpha, \\beta$ 不一定垂直，故②错误；\n对③，过直线 $n$ 分别作两平面与 $\\alpha, \\beta$ 分别相交于直线 $s$ 和直线 $t$，\n因为 $n // \\alpha$，过直线 $n$ 的平面与平面 $\\alpha$ 的交线为直线 $s$，则根据线面平行的性质定理知 $n // s$，\n同理可得 $n // t$，则 $s // t$，因为 $s \\not\\subset$ 平面 $\\beta$，$t \\subset$ 平面 $\\beta$，则 $s //$ 平面 $\\beta$，\n因为 $s \\subset$ 平面 $\\alpha$，$\\alpha \\cap \\beta = m$，则 $s // m$，又因为 $n // s$，则 $m // n$，故③正确；\n（此处有图，略）\n对④，若 $\\alpha \\cap \\beta = m, n$ 与 $\\alpha$ 和 $\\beta$ 所成的角相等，如果 $n // \\alpha, n // \\beta$，则 $m // n$，故④错误；\n综上只有①③正确，\n故选：A."
    },
    {
        "qnum": "11",
        "type": "单选题",
        "content": "在 $\\triangle ABC$ 中内角 $A, B, C$ 所对边分别为 $a, b, c$，若 $B = \\frac{\\pi}{3}$，$b^2 = \\frac{9}{4}ac$，则 $\\sin A + \\sin C =$（ ）",
        "options": "A. $\\frac{3}{2}$\nB. $\\sqrt{2}$\nC. $\\frac{\\sqrt{7}}{2}$\nD. $\\frac{\\sqrt{3}}{2}$",
        "answer": "C",
        "solution": "【分析】利用正弦定理得 $\\sin A \\sin C = \\frac{1}{3}$，再利用余弦定理有 $a^2 + c^2 = \\frac{13}{4}ac$，再利用正弦定理得到 $\\sin^2 A + \\sin^2 C$ 的值，最后代入计算即可.\n【详解】因为 $B = \\frac{\\pi}{3}, b^2 = \\frac{9}{4}ac$，则由正弦定理得 $\\sin A \\sin C = \\frac{4}{9} \\sin^2 B = \\frac{1}{3}$.\n由余弦定理可得：$b^2 = a^2 + c^2 - ac = \\frac{9}{4}ac$，\n即：$a^2 + c^2 = \\frac{13}{4}ac$，根据正弦定理得 $\\sin^2 A + \\sin^2 C = \\frac{13}{4} \\sin A \\sin C = \\frac{13}{12}$，\n所以 $(\\sin A + \\sin C)^2 = \\sin^2 A + \\sin^2 C + 2 \\sin A \\sin C = \\frac{7}{4}$，\n因为 $A, C$ 为三角形内角，则 $\\sin A + \\sin C > 0$，则 $\\sin A + \\sin C = \\frac{\\sqrt{7}}{2}$.\n故选：C."
    },
    {
        "qnum": "12",
        "type": "单选题",
        "content": "已知 $b$ 是 $a, c$ 的等差中项，直线 $ax + by + c = 0$ 与圆 $x^2 + y^2 + 4y - 1 = 0$ 交于 $A, B$ 两点，则 $|AB|$ 的最小值为（ ）",
        "options": "A. 2\nB. 3\nC. 4\nD. $2\\sqrt{5}$",
        "answer": "C",
        "solution": "【分析】结合等差数列性质将 $c$ 代换，求出直线恒过的定点，采用数形结合法即可求解.\n【详解】因为 $a, b, c$ 成等差数列，所以 $2b = a + c$，$c = 2b - a$，代入直线方程 $ax + by + c = 0$ 得 $ax + by + 2b - a = 0$，即 $a(x - 1) + b(y + 2) = 0$，令 $\\begin{cases} x - 1 = 0 \\\\ y + 2 = 0 \\end{cases}$ 得 $\\begin{cases} x = 1 \\\\ y = -2 \\end{cases}$，\n故直线恒过 $(1, -2)$，设 $P(1, -2)$，圆化为标准方程得：$C: x^2 + (y + 2)^2 = 5$，\n设圆心为 $C$，画出直线与圆的图形，由图可知，当 $PC \\perp AB$ 时，$|AB|$ 最小，\n$|PC| = 1, |AC| = |r| = \\sqrt{5}$，此时 $|AB| = 2|AP| = 2\\sqrt{AC^2 - PC^2} = 2\\sqrt{5 - 1} = 4$.\n故选：C"
    },
    {
        "qnum": "13",
        "type": "填空题",
        "content": "$\\left(\\frac{1}{3} + x\\right)^{10}$ 的展开式中，各项系数的最大值是______.",
        "options": "",
        "answer": "5",
        "solution": "【分析】先设展开式中第 $r+1$ 项系数最大，则根据通项公式有 $\\begin{cases} \\mathrm{C}_{10}^r \\left(\\frac{1}{3}\\right)^{10-r} \\ge \\mathrm{C}_{10}^{r+1} \\left(\\frac{1}{3}\\right)^{9-r} \\\\ \\mathrm{C}_{10}^r \\left(\\frac{1}{3}\\right)^{10-r} \\ge \\mathrm{C}_{10}^{r-1} \\left(\\frac{1}{3}\\right)^{11-r} \\end{cases}$，进而求出 $r$ 即可求解.\n【详解】由题展开式通项公式为 $T_{r+1} = \\mathrm{C}_{10}^r \\left(\\frac{1}{3}\\right)^{10-r} x^r$，$0 \\le r \\le 10$ 且 $r \\in \\mathbf{Z}$，\n设展开式中第 $r+1$ 项系数最大，则 $\\begin{cases} \\mathrm{C}_{10}^r \\left(\\frac{1}{3}\\right)^{10-r} \\ge \\mathrm{C}_{10}^{r+1} \\left(\\frac{1}{3}\\right)^{9-r} \\\\ \\mathrm{C}_{10}^r \\left(\\frac{1}{3}\\right)^{10-r} \\ge \\mathrm{C}_{10}^{r-1} \\left(\\frac{1}{3}\\right)^{11-r} \\end{cases}$，\n$\\Rightarrow \\begin{cases} r \\ge \\frac{29}{4} \\\\ r \\le \\frac{33}{4} \\end{cases}$，即 $\\frac{29}{4} \\le r \\le \\frac{33}{4}$，又 $r \\in \\mathbf{Z}$，故 $r = 8$，\n所以展开式中系数最大的项是第 9 项，且该项系数为 $\\mathrm{C}_{10}^8 \\left(\\frac{1}{3}\\right)^2 = 5$.\n故答案为：5."
    },
    {
        "qnum": "14",
        "type": "填空题",
        "content": "已知甲、乙两个圆台上、下底面的半径均为 $r_1$ 和 $r_2$，母线长分别为 $2(r_2 - r_1)$ 和 $3(r_2 - r_1)$，则两个圆台的体积之比 $\\frac{V_{\\text{甲}}}{V_{\\text{乙}}} =$ ______.",
        "options": "",
        "answer": "$\\frac{\\sqrt{6}}{4}$",
        "solution": "【分析】先根据已知条件和圆台结构特征分别求出两圆台的高，再根据圆台的体积公式直接代入计算即可得解.\n【详解】由题可得两个圆台的高分别为 $h_{\\text{甲}} = \\sqrt{\\left[2(r_1 - r_2)\\right]^2 - (r_1 - r_2)^2} = \\sqrt{3}(r_1 - r_2)$，\n$h_{\\text{乙}} = \\sqrt{\\left[3(r_1 - r_2)\\right]^2 - (r_1 - r_2)^2} = 2\\sqrt{2}(r_1 - r_2)$，\n所以 $\\frac{V_{\\text{甲}}}{V_{\\text{乙}}} = \\frac{\\frac{1}{3}(S_2 + S_1 + \\sqrt{S_2 S_1})h_{\\text{甲}}}{\\frac{1}{3}(S_2 + S_1 + \\sqrt{S_2 S_1})h_{\\text{乙}}} = \\frac{h_{\\text{甲}}}{h_{\\text{乙}}} = \\frac{\\sqrt{3}(r_1 - r_2)}{2\\sqrt{2}(r_1 - r_2)} = \\frac{\\sqrt{6}}{4}$.\n故答案为：$\\frac{\\sqrt{6}}{4}$."
    },
    {
        "qnum": "15",
        "type": "填空题",
        "content": "已知 $a > 1$，$\\frac{1}{\\log_8 a} - \\frac{1}{\\log_a 4} = -\\frac{5}{2}$，则 $a =$ ______.",
        "options": "",
        "answer": "64",
        "solution": "【分析】将 $\\log_8 a, \\log_a 4$ 利用换底公式转化成 $\\log_2 a$ 来表示即可求解.\n【详解】由题 $\\frac{1}{\\log_8 a} - \\frac{1}{\\log_a 4} = \\frac{3}{\\log_2 a} - \\frac{1}{2} \\log_2 a = -\\frac{5}{2}$，整理得 $(\\log_2 a)^2 - 5 \\log_2 a - 6 = 0$，\n$\\Rightarrow \\log_2 a = -1$ 或 $\\log_2 a = 6$，又 $a > 1$，\n所以 $\\log_2 a = 6 = \\log_2 2^6$，故 $a = 2^6 = 64$\n故答案为：64."
    },
    {
        "qnum": "16",
        "type": "填空题",
        "content": "有 6 个相同的球，分别标有数字 1、2、3、4、5、6，从中不放回地随机抽取 3 次，每次取 1 个球.记 $m$ 为前两次取出的球上数字的平均值，$n$ 为取出的三个球上数字的平均值，则 $m$ 与 $n$ 差的绝对值不超过 $\\frac{1}{2}$ 的概率是______.",
        "options": "",
        "answer": "$\\frac{7}{15}$",
        "solution": "【分析】根据排列可求基本事件的总数，设前两个球的号码为 $a, b$，第三个球的号码为 $c$，则 $a + b - 3 \\le 2c \\le a + b + 3$，就 $c$ 的不同取值分类讨论后可求随机事件的概率.\n【详解】从 6 个不同的球中不放回地抽取 3 次，共有 $\\mathrm{A}_6^3 = 120$ 种，\n设前两个球的号码为 $a, b$，第三个球的号码为 $c$，则 $\\left| \\frac{a + b + c}{3} - \\frac{a + b}{2} \\right| \\le \\frac{1}{2}$，\n故 $|2c - (a + b)| \\le 3$，故 $-3 \\le 2c - (a + b) \\le 3$，\n故 $a + b - 3 \\le 2c \\le a + b + 3$，\n若 $c = 1$，则 $a + b \\le 5$，则 $(a, b)$ 为：$(2, 3), (3, 2)$，故有 2 种，\n若 $c = 2$，则 $1 \\le a + b \\le 7$，则 $(a, b)$ 为：$(1, 3), (1, 4), (1, 5), (1, 6), (3, 4)$，\n$(3, 1), (4, 1), (5, 1), (6, 1), (4, 3)$，故有 10 种，\n当 $c = 3$，则 $3 \\le a + b \\le 9$，则 $(a, b)$ 为：\n$(1, 2), (1, 4), (1, 5), (1, 6), (2, 4), (2, 5), (2, 6), (4, 5)$，\n$(2, 1), (4, 1), (5, 1), (6, 1), (4, 2), (5, 2), (6, 2), (5, 4)$，\n故有 16 种，\n当 $c = 4$，则 $5 \\le a + b \\le 11$，同理有 16 种，\n当 $c = 5$，则 $7 \\le a + b \\le 13$，同理有 10 种，\n当 $c = 6$，则 $9 \\le a + b \\le 15$，同理有 2 种，\n共 $m$ 与 $n$ 的差的绝对值不超过 $\\frac{1}{2}$ 时不同的抽取方法总数为 $2(2 + 10 + 16) = 56$，\n故所求概率为 $\\frac{56}{120} = \\frac{7}{15}$.\n故答案为：$\\frac{7}{15}$."
    },
    {
        "qnum": "17",
        "type": "解答题",
        "content": "某工厂进行生产线智能化升级改造，升级改造后，从该工厂甲、乙两个车间的产品中随机抽取 150 件进行检验，数据如下：\n\n| | 优级品 | 合格品 | 不合格品 | 总计 |\n| :--- | :---: | :---: | :---: | :---: |\n| 甲车间 | 26 | 24 | 0 | 50 |\n| 乙车间 | 70 | 28 | 2 | 100 |\n| 总计 | 96 | 52 | 2 | 150 |\n\n（1）填写列联表，能否有 $95\\%$ 的把握认为甲、乙两车间产品的优级品率存在差异？能否有 $99\\%$ 的把握认为甲，乙两车间产品的优级品率存在差异？\n\n（2）已知升级改造前该工厂产品的优级品率 $p=0.5$，设 $\\overline{p}$ 为升级改造后抽取的 $n$ 件产品的优级品率.如果 $\\overline{p} > p + 1.65\\sqrt{\\frac{p(1-p)}{n}}$，则认为该工厂产品的优级品率提高了，根据抽取的 150 件产品的数据，能否认为生产线智能化升级改造后，该工厂产品的优级品率提高了？（$\\sqrt{150} \\approx 12.247$）\n\n附：$K^2 = \\frac{n(ad-bc)^2}{(a+b)(c+d)(a+c)(b+d)}$\n\n| $P\\left(K^2 \\ge k\\right)$ | 0.050 | 0.010 | 0.001 |\n| :--- | :--- | :--- | :--- |\n| $k$ | 3.841 | 6.635 | 10.828 |",
        "options": "",
        "answer": "（1）有 $95\\%$ 把握认为存在差异，没有 $99\\%$ 把握认为存在差异\n（2）可以认为优级品率提高了",
        "solution": "【分析】（1）根据题中数据完善列联表，计算 $K^2$，并与临界值对比分析；\n（2）用频率估计概率可得 $\\overline{p}=0.64$，根据题意计算 $p+1.65\\sqrt{\\frac{p(1-p)}{n}}$，结合题意分析判断.\n\n【小问1详解】\n根据题意可得列联表：\n\n| | 优级品 | 非优级品 |\n| :--- | :--- | :--- |\n| 甲车间 | 26 | 24 |\n| 乙车间 | 70 | 30 |\n\n可得 $K^2 = \\frac{150(26 \\times 30 - 24 \\times 70)^2}{50 \\times 100 \\times 96 \\times 54} = \\frac{75}{16} = 4.6875$，\n因为 $3.841 < 4.6875 < 6.635$，\n所以有 $95\\%$ 的把握认为甲、乙两车间产品的优级品率存在差异，没有 $99\\%$ 的把握认为甲，乙两车间产品的优级品率存在差异.\n\n【小问2详解】\n由题意可知：生产线智能化升级改造后，该工厂产品的优级品的频率为 $\\frac{96}{150} = 0.64$，\n用频率估计概率可得 $\\overline{p} = 0.64$，\n又因为升级改造前该工厂产品的优级品率 $p=0.5$，\n则 $p + 1.65\\sqrt{\\frac{p(1-p)}{n}} = 0.5 + 1.65\\sqrt{\\frac{0.5(1-0.5)}{150}} \\approx 0.5 + 1.65 \\times \\frac{0.5}{12.247} \\approx 0.568$，\n可知 $\\overline{p} > p + 1.65\\sqrt{\\frac{p(1-p)}{n}}$，\n所以可以认为生产线智能化升级改造后，该工厂产品的优级品率提高了."
    },
    {
        "qnum": "18",
        "type": "解答题",
        "content": "记 $S_n$ 为数列 $\\{a_n\\}$ 的前 $n$ 项和，且 $4S_n = 3a_n + 4$.\n（1）求 $\\{a_n\\}$ 的通项公式；\n（2）设 $b_n = (-1)^{n-1} n a_n$，求数列 $\\{b_n\\}$ 的前 $n$ 项和为 $T_n$.",
        "options": "",
        "answer": "（1）$a_n = 4 \\cdot (-3)^{n-1}$\n（2）$T_n = (2n-1) \\cdot 3^n + 1$",
        "solution": "【分析】（1）利用退位法可求 $\\{a_n\\}$ 的通项公式.\n（2）利用错位相减法可求 $T_n$.\n\n【小问1详解】\n当 $n=1$ 时，$4S_1 = 4a_1 = 3a_1 + 4$，解得 $a_1 = 4$.\n当 $n \\ge 2$ 时，$4S_{n-1} = 3a_{n-1} + 4$，所以 $4S_n - 4S_{n-1} = 4a_n = 3a_n - 3a_{n-1}$ 即 $a_n = -3a_{n-1}$，\n而 $a_1 = 4 \\ne 0$，故 $a_n \\ne 0$，故 $\\frac{a_n}{a_{n-1}} = -3$，\n$\\therefore$ 数列 $\\{a_n\\}$ 是以 4 为首项，$-3$ 为公比的等比数列，\n所以 $a_n = 4 \\cdot (-3)^{n-1}$.\n\n【小问2详解】\n$b_n = (-1)^{n-1} \\cdot n \\cdot 4 \\cdot (-3)^{n-1} = 4n \\cdot 3^{n-1}$，\n所以 $T_n = b_1 + b_2 + b_3 + \\cdots + b_n = 4 \\cdot 3^0 + 8 \\cdot 3^1 + 12 \\cdot 3^2 + \\cdots + 4n \\cdot 3^{n-1}$\n故 $3T_n = 4 \\cdot 3^1 + 8 \\cdot 3^2 + 12 \\cdot 3^3 + \\cdots + 4n \\cdot 3^n$\n所以 $-2T_n = 4 + 4 \\cdot 3^1 + 4 \\cdot 3^2 + \\cdots + 4 \\cdot 3^{n-1} - 4n \\cdot 3^n$\n$= 4 + 4 \\cdot \\frac{3(1-3^{n-1})}{1-3} - 4n \\cdot 3^n = 4 + 2 \\cdot 3 \\cdot (3^{n-1}-1) - 4n \\cdot 3^n$\n$= (2-4n) \\cdot 3^n - 2$，\n$\\therefore T_n = (2n-1) \\cdot 3^n + 1$."
    },
    {
        "qnum": "19",
        "type": "解答题",
        "content": "如图，在以 $A, B, C, D, E, F$ 为顶点的五面体中，四边形 $ABCD$ 与四边形 $ADEF$ 均为等腰梯形，$BC // AD, EF // AD$，$AD=4, AB=BC=EF=2$，$ED=\\sqrt{10}, FB=2\\sqrt{3}$，$M$ 为 $AD$ 的中点.\n（1）证明：$BM // \\text{平面} CDE$；\n（2）求二面角 $F-BM-E$ 的正弦值.",
        "options": "",
        "answer": "（1）证明见详解\n（2）$\\frac{4\\sqrt{3}}{13}$",
        "solution": "【分析】（1）结合已知易证四边形 $BCDM$ 为平行四边形，可证 $BM // CD$，进而得证；\n（2）作 $BO \\perp AD$ 交 $AD$ 于 $O$，连接 $OF$，易证 $OB, OD, OF$ 三垂直，采用建系法结合二面角夹角余弦公式即可求解.\n\n【小问1详解】\n因为 $BC // AD, EF=2, AD=4, M$ 为 $AD$ 的中点，所以 $BC // MD, BC=MD$，\n四边形 $BCDM$ 为平行四边形，所以 $BM // CD$，又因为 $BM \\not\\subset \\text{平面} CDE$，$CD \\subset \\text{平面} CDE$，所以 $BM // \\text{平面} CDE$；\n\n【小问2详解】\n如图所示，作 $BO \\perp AD$ 交 $AD$ 于 $O$，连接 $OF$，\n因为四边形 $ABCD$ 为等腰梯形，$BC // AD, AD=4, AB=BC=2$，所以 $CD=2$，\n结合（1）$BCDM$ 为平行四边形，可得 $BM=CD=2$，又 $AM=2$，\n所以 $\\triangle ABM$ 为等边三角形，$O$ 为 $AM$ 中点，所以 $OB=\\sqrt{3}$，\n又因为四边形 $ADEF$ 为等腰梯形，$M$ 为 $AD$ 中点，所以 $EF=MD, EF // MD$，\n四边形 $EFMD$ 为平行四边形，$FM=ED=AF$，\n所以 $\\triangle AFM$ 为等腰三角形，$\\triangle ABM$ 与 $\\triangle AFM$ 底边上中点 $O$ 重合，$OF \\perp AM$，\n$OF = \\sqrt{AF^2 - AO^2} = 3$，\n因为 $OB^2 + OF^2 = BF^2$，所以 $OB \\perp OF$，所以 $OB, OD, OF$ 互相垂直，\n以 $OB$ 方向为 $x$ 轴，$OD$ 方向为 $y$ 轴，$OF$ 方向为 $z$ 轴，建立 $O-xyz$ 空间直角坐标系，\n$F(0,0,3)$，$B(\\sqrt{3},0,0), M(0,1,0), E(0,2,3)$，$\\overrightarrow{BM} = (-\\sqrt{3}, 1, 0), \\overrightarrow{BF} = (-\\sqrt{3}, 0, 3)$，\n$\\overrightarrow{BE} = (-\\sqrt{3}, 2, 3)$，设平面 $BFM$ 的法向量为 $\\vec{m} = (x_1, y_1, z_1)$，\n平面 $EMB$ 的法向量为 $\\vec{n} = (x_2, y_2, z_2)$，\n则 $\\begin{cases} \\vec{m} \\cdot \\overrightarrow{BM} = 0 \\\\ \\vec{m} \\cdot \\overrightarrow{BF} = 0 \\end{cases}$，即 $\\begin{cases} -\\sqrt{3}x_1 + y_1 = 0 \\\\ -\\sqrt{3}x_1 + 3z_1 = 0 \\end{cases}$，令 $x_1 = \\sqrt{3}$，得 $y_1 = 3, z_1 = 1$，即 $\\vec{m} = (\\sqrt{3}, 3, 1)$，\n则 $\\begin{cases} \\vec{n} \\cdot \\overrightarrow{BM} = 0 \\\\ \\vec{n} \\cdot \\overrightarrow{BE} = 0 \\end{cases}$，即 $\\begin{cases} -\\sqrt{3}x_2 + y_2 = 0 \\\\ -\\sqrt{3}x_2 + 2y_2 + 3z_2 = 0 \\end{cases}$，令 $x_2 = \\sqrt{3}$，得 $y_2 = 3, z_2 = -1$，\n即 $\\vec{n} = (\\sqrt{3}, 3, -1)$，$\\cos \\langle \\vec{m}, \\vec{n} \\rangle = \\frac{\\vec{m} \\cdot \\vec{n}}{|\\vec{m}| \\cdot |\\vec{n}|} = \\frac{11}{\\sqrt{13} \\cdot \\sqrt{13}} = \\frac{11}{13}$，则 $\\sin \\langle \\vec{m}, \\vec{n} \\rangle = \\frac{4\\sqrt{3}}{13}$，\n故二面角 $F-BM-E$ 的正弦值为 $\\frac{4\\sqrt{3}}{13}$."
    },
    {
        "qnum": "20",
        "type": "解答题",
        "content": "设椭圆 $C: \\frac{x^2}{a^2} + \\frac{y^2}{b^2} = 1 (a > b > 0)$ 的右焦点为 $F$，点 $M\\left(1, \\frac{3}{2}\\right)$ 在 $C$ 上，且 $MF \\perp x$ 轴.\n（1）求 $C$ 的方程；\n（2）过点 $P(4,0)$ 的直线与 $C$ 交于 $A, B$ 两点，$N$ 为线段 $FP$ 的中点，直线 $NB$ 交直线 $MF$ 于点 $Q$，证明：$AQ \\perp y$ 轴.",
        "options": "",
        "answer": "（1）$\\frac{x^2}{4} + \\frac{y^2}{3} = 1$\n（2）证明见解析",
        "solution": "【分析】（1）设 $F(c,0)$，根据 $M$ 的坐标及 $MF \\perp x$ 轴可求基本量，故可求椭圆方程.\n（2）设 $AB: y = k(x-4)$，$A(x_1, y_1)$，$B(x_2, y_2)$，联立直线方程和椭圆方程，用 $A, B$ 的坐标表示 $y_1 - y_Q$，结合韦达定理化简前者可得 $y_1 - y_Q = 0$，故可证 $AQ \\perp y$ 轴.\n\n【小问1详解】\n设 $F(c,0)$，由题设有 $c=1$ 且 $\\frac{b^2}{a} = \\frac{3}{2}$，故 $\\frac{a^2-1}{a} = \\frac{3}{2}$，故 $a=2$，故 $b=\\sqrt{3}$，\n故椭圆方程为 $\\frac{x^2}{4} + \\frac{y^2}{3} = 1$.\n\n【小问2详解】\n直线 $AB$ 的斜率必定存在，设 $AB: y = k(x-4)$，$A(x_1, y_1)$，$B(x_2, y_2)$，\n由 $\\begin{cases} 3x^2+4y^2=12 \\\\ y=k(x-4) \\end{cases}$ 可得 $\\left(3+4k^2\\right)x^2-32k^2x+64k^2-12=0$，\n故 $\\Delta=1024k^4-4\\left(3+4k^2\\right)\\left(64k^2-12\\right)>0$，故 $-\\frac{1}{2}<k<\\frac{1}{2}$，\n又 $x_1+x_2=\\frac{32k^2}{3+4k^2}, x_1x_2=\\frac{64k^2-12}{3+4k^2}$，\n而 $N\\left(\\frac{5}{2}, 0\\right)$，故直线 $BN: y=\\frac{-y_2}{x_2-\\frac{5}{2}}\\left(x-\\frac{5}{2}\\right)$，故 $y_Q=\\frac{-\\frac{3}{2}y_2}{x_2-\\frac{5}{2}}=\\frac{-3y_2}{2x_2-5}$，\n所以 $y_1-y_Q=y_1+\\frac{3y_2}{2x_2-5}=\\frac{y_1\\times\\left(2x_2-5\\right)+3y_2}{2x_2-5}$\n$=\\frac{k\\left(x_1-4\\right)\\times\\left(2x_2-5\\right)+3k\\left(x_2-4\\right)}{2x_2-5}$\n$=k\\frac{2x_1x_2-5\\left(x_1+x_2\\right)+8}{2x_2-5}=k\\frac{2\\times\\frac{64k^2-12}{3+4k^2}-5\\times\\frac{32k^2}{3+4k^2}+8}{2x_2-5}$\n$=k\\frac{\\frac{128k^2-24-160k^2+24+32k^2}{3+4k^2}}{2x_2-5}=0$，\n故 $y_1=y_Q$，即 $AQ \\perp y$ 轴.\n\n【点睛】方法点睛：利用韦达定理法解决直线与圆锥曲线相交问题的基本步骤如下：\n（1）设直线方程，设交点坐标为 $(x_1, y_1), (x_2, y_2)$；\n（2）联立直线与圆锥曲线的方程，得到关于 $x$（或 $y$）的一元二次方程，注意 $\\Delta$ 的判断；\n（3）列出韦达定理；\n（4）将所求问题或题中的关系转化为 $x_1+x_2$、$x_1x_2$（或 $y_1+y_2$、$y_1y_2$）的形式；\n（5）代入韦达定理求解."
    },
    {
        "qnum": "21",
        "type": "解答题",
        "content": "已知函数 $f(x)=(1-ax)\\ln(1+x)-x$.\n（1）当 $a=-2$ 时，求 $f(x)$ 的极值；\n（2）当 $x \\ge 0$ 时，$f(x) \\ge 0$ 恒成立，求 $a$ 的取值范围.",
        "options": "",
        "answer": "（1）极小值为 $0$，无极大值\n（2）$a \\le -\\frac{1}{2}$",
        "solution": "【分析】（1）求出函数的导数，根据导数的单调性和零点可求函数的极值.\n（2）求出函数的二阶导数，就 $a \\le -\\frac{1}{2}$、$-\\frac{1}{2}<a<0$、$a \\ge 0$ 分类讨论后可得参数的取值范围.\n\n【小问1详解】\n当 $a=-2$ 时，$f(x)=(1+2x)\\ln(1+x)-x$，\n故 $f'(x)=2\\ln(1+x)+\\frac{1+2x}{1+x}-1=2\\ln(1+x)-\\frac{1}{1+x}+1$，\n因为 $y=2\\ln(1+x), y=-\\frac{1}{1+x}+1$ 在 $(-1, +\\infty)$ 上为增函数，\n故 $f'(x)$ 在 $(-1, +\\infty)$ 上为增函数，而 $f'(0)=0$，\n故当 $-1<x<0$ 时，$f'(x)<0$，当 $x>0$ 时，$f'(x)>0$，\n故 $f(x)$ 在 $x=0$ 处取极小值且极小值为 $f(0)=0$，无极大值.\n\n【小问2详解】\n$f'(x)=-a\\ln(1+x)+\\frac{1-ax}{1+x}-1=-a\\ln(1+x)-\\frac{(a+1)x}{1+x}, x>0$，\n设 $s(x)=-a\\ln(1+x)-\\frac{(a+1)x}{1+x}, x>0$，\n则 $s'(x)=\\frac{-a}{x+1}-\\frac{(a+1)}{(1+x)^2}=-\\frac{a(x+1)+a+1}{(1+x)^2}=-\\frac{ax+2a+1}{(1+x)^2}$，\n当 $a \\le -\\frac{1}{2}$ 时，$s'(x)>0$，故 $s(x)$ 在 $(0, +\\infty)$ 上为增函数，\n故 $s(x)>s(0)=0$，即 $f'(x)>0$，\n所以 $f(x)$ 在 $[0, +\\infty)$ 上为增函数，故 $f(x) \\ge f(0)=0$.\n当 $-\\frac{1}{2}<a<0$ 时，当 $0<x<-\\frac{2a+1}{a}$ 时，$s'(x)<0$，\n故 $s(x)$ 在 $\\left(0, -\\frac{2a+1}{a}\\right)$ 上为减函数，故在 $\\left(0, -\\frac{2a+1}{a}\\right)$ 上 $s(x)<s(0)$，\n即在 $\\left(0, -\\frac{2a+1}{a}\\right)$ 上 $f'(x)<0$ 即 $f(x)$ 为减函数，\n故在 $\\left(0, -\\frac{2a+1}{a}\\right)$ 上 $f(x)<f(0)=0$，不合题意，舍.\n当 $a \\ge 0$，此时 $s'(x)<0$ 在 $(0, +\\infty)$ 上恒成立，\n同理可得在 $(0, +\\infty)$ 上 $f(x)<f(0)=0$ 恒成立，不合题意，舍；\n综上，$a \\le -\\frac{1}{2}$.\n\n【点睛】思路点睛：导数背景下不等式恒成立问题，往往需要利用导数判断函数单调性，有时还需要对导数进一步利用导数研究其符号特征，处理此类问题时注意利用范围端点的性质来确定如何分类."
    },
    {
        "qnum": "22",
        "type": "解答题",
        "content": "选修4-4：坐标系与参数方程\n在平面直角坐标系 $xOy$ 中，以坐标原点 $O$ 为极点，$x$ 轴的正半轴为极轴建立极坐标系，曲线 $C$ 的极坐标方程为 $\\rho=\\rho\\cos\\theta+1$.\n（1）写出 $C$ 的直角坐标方程；\n（2）设直线 $l$: $\\begin{cases} x=t \\\\ y=t+a \\end{cases}$ ($t$ 为参数)，若 $C$ 与 $l$ 相交于 $A, B$ 两点，若 $|AB|=2$，求 $a$ 的值.",
        "options": "",
        "answer": "（1）$y^2=2x+1$\n（2）$a=\\frac{3}{4}$",
        "solution": "【分析】（1）根据 $\\begin{cases} \\rho=\\sqrt{x^2+y^2} \\\\ \\rho\\cos\\theta=x \\end{cases}$ 可得 $C$ 的直角方程.\n（2）将直线的参数方程代入 $C$ 的直角方程，结合参数 $s$ 的几何意义或弦长公式可求 $a$ 的值.\n\n【小问1详解】\n由 $\\rho=\\rho\\cos\\theta+1$，将 $\\begin{cases} \\rho=\\sqrt{x^2+y^2} \\\\ \\rho\\cos\\theta=x \\end{cases}$ 代入 $\\rho=\\rho\\cos\\theta+1$，\n故可得 $\\sqrt{x^2+y^2}=x+1$，两边平方后可得曲线的直角坐标方程为 $y^2=2x+1$.\n\n【小问2详解】\n对于直线 $l$ 的参数方程消去参数 $t$，得直线的普通方程为 $y=x+a$.\n法1：直线 $l$ 的斜率为 1，故倾斜角为 $\\frac{\\pi}{4}$，\n故直线的参数方程可设为 $\\begin{cases} x=\\frac{\\sqrt{2}}{2}s \\\\ y=a+\\frac{\\sqrt{2}}{2}s \\end{cases}$，$s \\in \\mathbf{R}$.\n将其代入 $y^2=2x+1$ 中得 $s^2+2\\sqrt{2}(a-1)s+2\\left(a^2-1\\right)=0$\n设 $A, B$ 两点对应的参数分别为 $s_1, s_2$，则 $s_1+s_2=-2\\sqrt{2}(a-1), s_1s_2=2\\left(a^2-1\\right)$，\n且 $\\Delta=8(a-1)^2-8\\left(a^2-1\\right)=16-16a>0$，故 $a<1$，\n$\\therefore |AB|=|s_1-s_2|=\\sqrt{\\left(s_1+s_2\\right)^2-4s_1s_2}=\\sqrt{8(a-1)^2-8\\left(a^2-1\\right)}=2$，解得 $a=\\frac{3}{4}$.\n\n法2：联立 $\\begin{cases} y=x+a \\\\ y^2=2x+1 \\end{cases}$，得 $x^2+(2a-2)x+a^2-1=0$，\n$\\Delta=(2a-2)^2-4\\left(a^2-1\\right)=-8a+8>0$，解得 $a<1$，\n设 $A\\left(x_1, y_1\\right), B\\left(x_2, y_2\\right), \\therefore x_1+x_2=2-2a, x_1x_2=a^2-1$，\n则 $|AB|=\\sqrt{1+1^2} \\cdot \\sqrt{\\left(x_1+x_2\\right)^2-4x_1x_2}=\\sqrt{2} \\cdot \\sqrt{(2-2a)^2-4\\left(a^2-1\\right)}=2$，\n解得 $a=\\frac{3}{4}$."
    },
    {
        "qnum": "23",
        "type": "解答题",
        "content": "选修4-5：不等式选讲\n实数 $a, b$ 满足 $a+b \\ge 3$.\n（1）证明：$2a^2+2b^2 > a+b$；\n（2）证明：$\\left|a-2b^2\\right|+\\left|b-2a^2\\right| \\ge 6$.",
        "options": "",
        "answer": "（1）证明见解析\n（2）证明见解析",
        "solution": "【分析】（1）直接利用 $2a^2+2b^2 \\ge (a+b)^2$ 即可证明.\n（2）根据绝对值不等式并结合（1）中结论即可证明.\n\n【小问1详解】\n因为 $2a^2+2b^2-(a+b)^2=a^2-2ab+b^2=(a-b)^2 \\ge 0$，\n当 $a=b$ 时等号成立，则 $2a^2+2b^2 \\ge (a+b)^2$，\n因为 $a+b \\ge 3$，所以 $2a^2+2b^2 \\ge (a+b)^2 > a+b$；\n\n【小问2详解】\n$\\left|a-2b^2\\right|+\\left|b-2a^2\\right| \\ge \\left|a-2b^2+b-2a^2\\right| = \\left|2a^2+2b^2-(a+b)\\right|$\n$= 2a^2+2b^2-(a+b) \\ge (a+b)^2-(a+b) = (a+b)(a+b-1) \\ge 3 \\times 2 = 6$."
    }
]


# ============================================================
# 导入函数
# ============================================================

def import_to_db(questions, source):
    success = 0
    fail = 0
    fail_details = []
    
    for i, q in enumerate(questions):
        # Content = 题干
        content_text = q['content']
        
        # Options单独存储
        options_text = q.get('options', '')
        
        rec = {
            'topicId': 'M1-C1-T1',
            'type': q['type'],
            'difficulty': '中等',
            'content': content_text,
            'options': options_text,
            'answer': q.get('answer', ''),
            'solution': q.get('solution', ''),
            'source': source,
            'tags': f'{source},number:{q["qnum"]}'
        }
        
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
                print(f'  ✅ 题{q["qnum"]} [{q["type"]}]', flush=True)
            else:
                fail += 1
                fail_details.append(f'题{q["qnum"]}: {r.stdout[:150]}')
                print(f'  ❌ 题{q["qnum"]}: {r.stdout[:100]}', flush=True)
        except Exception as e:
            fail += 1
            fail_details.append(f'题{q["qnum"]}: {e}')
            print(f'  ❌ 题{q["qnum"]}: {e}', flush=True)
    
    return success, fail, fail_details


if __name__ == '__main__':
    source = '2024全国甲卷（理）'
    print(f'📋 试卷: {source}')
    print(f'📊 题目数: {len(questions_data)}')
    
    # 统计题型
    types = {}
    for q in questions_data:
        types[q['type']] = types.get(q['type'], 0) + 1
    print(f'   题型分布: {types}')
    
    print(f'\n💾 开始导入 {len(questions_data)} 道题到数据库...')
    success, fail, details = import_to_db(questions_data, source)
    print(f'\n✅ 导入完成: 成功={success}, 失败={fail}')
    if fail > 0:
        print('失败详情:')
        for d in details[:5]:
            print(f'  • {d}')
