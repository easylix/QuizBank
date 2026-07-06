#!/usr/bin/env python3
"""
完整重新导入2024新课标Ⅱ卷（基于视觉AI逐字识别）
删除旧数据后插入19道题的新数据
"""
import json, subprocess, sys, time

BAAS_SCRIPT = "/home/sandbox/.openclaw/workspace/skills/xiaoyi-web-deploy/scripts/baas.py"

def baas_call(td):
    """调用BaaS API"""
    payload = json.dumps({
        'table': 'questions',
        'method': 'tableData',
        'apiKey': 'baas_ZiRfZlhr',
        'tableData': td
    })
    cmd = ['python3', BAAS_SCRIPT, '--x-api-type', 'tableAddData', '--content', payload]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return r.stdout

def list_all():
    payload = json.dumps({'table':'questions','method':'list','apiKey':'baas_ZiRfZlhr'})
    cmd = ['python3', BAAS_SCRIPT, '--x-api-type', 'tableQueryData', '--content', payload]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    resp = json.loads(r.stdout)
    return resp['abilityInfos'][0]['actionExecutorResult']['reply']['data']

def delete_record(rid):
    payload = json.dumps({
        'table': 'questions',
        'method': 'delete',
        'apiKey': 'baas_ZiRfZlhr',
        'tableData': {'id': rid}
    })
    cmd = ['python3', BAAS_SCRIPT, '--x-api-type', 'tableAddData', '--content', payload]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return '"code":"0"' in r.stdout

source = "2024新课标Ⅱ卷"

questions = []

# ============ 一、单项选择题（题1-8） ============

questions.append({
    "type": "单选题",
    "difficulty": "简单",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:1",
    "topicId": "M2-C2-T2",
    "content": "已知 $z=-1-\\mathrm{i}$，则 $|z|=$ （ ）",
    "options": "A. 0\nB. 1\nC. $\\sqrt{2}$\nD. 2",
    "answer": "C",
    "solution": "【分析】由复数模的计算公式直接计算即可.\n【详解】若 $z=-1-\\mathrm{i}$，则 $|z|=\\sqrt{(-1)^{2}+(-1)^{2}}=\\sqrt{2}$.\n故选：C."
})

questions.append({
    "type": "单选题",
    "difficulty": "简单",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:2",
    "topicId": "M1-C1-T3",
    "content": "已知命题 $p$: $\\forall x \\in \\mathbf{R}$，$|x+1|>1$；命题 $q$: $\\exists x>0$，$x^{3}=x$，则（ ）",
    "options": "A. $p$ 和 $q$ 都是真命题\nB. $\\neg p$ 和 $q$ 都是真命题\nC. $p$ 和 $\\neg q$ 都是真命题\nD. $\\neg p$ 和 $\\neg q$ 都是真命题",
    "answer": "B",
    "solution": "【分析】对于两个命题而言，可分别取 $x=-1$、$x=1$，再结合命题及其否定的真假性相反即可得解.\n【详解】对于 $p$ 而言，取 $x=-1$，则有 $|x+1|=0<1$，故 $p$ 是假命题，$\\neg p$ 是真命题，\n对于 $q$ 而言，取 $x=1$，则有 $x^{3}=1^{3}=1=x$，故 $q$ 是真命题，$\\neg q$ 是假命题，\n综上，$\\neg p$ 和 $q$ 都是真命题.\n故选：B."
})

questions.append({
    "type": "单选题",
    "difficulty": "简单",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:3",
    "topicId": "M2-C1-T3",
    "content": "已知向量 $\\vec{a},\\vec{b}$ 满足 $|\\vec{a}|=1$，$|\\vec{a}+2\\vec{b}|=2$，且 $(\\vec{b}-2\\vec{a})\\perp\\vec{b}$，则 $|\\vec{b}|=$ （ ）",
    "options": "A. $\\frac{1}{2}$\nB. $\\frac{\\sqrt{2}}{2}$\nC. $\\frac{\\sqrt{3}}{2}$\nD. 1",
    "answer": "B",
    "solution": "【分析】由 $(\\vec{b}-2\\vec{a})\\perp\\vec{b}$ 得 $\\vec{b}^{2}=2\\vec{a}\\cdot\\vec{b}$，结合 $|\\vec{a}|=1,|\\vec{a}+2\\vec{b}|=2$，得 $1+4\\vec{a}\\cdot\\vec{b}+4\\vec{b}^{2}=1+6\\vec{b}^{2}=4$，由此即可得解.\n【详解】因为 $(\\vec{b}-2\\vec{a})\\perp\\vec{b}$，所以 $(\\vec{b}-2\\vec{a})\\cdot\\vec{b}=0$，即 $\\vec{b}^{2}=2\\vec{a}\\cdot\\vec{b}$，\n又因为 $|\\vec{a}|=1,|\\vec{a}+2\\vec{b}|=2$，\n所以 $1+4\\vec{a}\\cdot\\vec{b}+4\\vec{b}^{2}=1+6\\vec{b}^{2}=4$，\n从而 $|\\vec{b}|=\\frac{\\sqrt{2}}{2}$.\n故选：B."
})

questions.append({
    "type": "单选题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:4",
    "topicId": "M5-C3-T2",
    "content": "某农业研究部门在面积相等的 100 块稻田上种植一种新型水稻，得到各块稻田的亩产量（单位：kg）并部分整理下表：\n\n| 亩产量 | [900,950) | [950,1000) | [1000,1050) | [1100,1150) | [1150,1200) |\n|:---|:---:|:---:|:---:|:---:|:---:|\n| 频数 | 6 | 12 | 18 | 24 | 10 |\n\n据表中数据，结论中正确的是（ ）",
    "options": "A. 100 块稻田亩产量的中位数小于 1050kg\nB. 100 块稻田中亩产量低于 1100kg 的稻田所占比例超过 80%\nC. 100 块稻田亩产量的极差介于 200kg 至 300kg 之间\nD. 100 块稻田亩产量的平均值介于 900kg 至 1000kg 之间",
    "answer": "C",
    "solution": "【分析】计算出前三段频数即可判断 A；计算出低于 1100kg 的频数，再计算比例即可判断 B；根据极差计算方法即可判断 C；根据平均值计算公式即可判断 D.\n【详解】对于 A，根据频数分布表可知，$6+12+18=36<50$，\n所以亩产量的中位数不小于 1050kg，故 A 错误；\n对于 B，亩产量不低于 1100kg 的频数为 $24+10=34$，\n所以低于 1100kg 的稻田占比为 $\\frac{100-34}{100}=66\\%$，故 B 错误；\n对于 C，稻田亩产量的极差最大为 $1200-900=300$，最小为 $1150-950=200$，故 C 正确；\n对于 D，由频数分布表可得，亩产量在 $[1050,1100)$ 的频数为 $100-(6+12+18+24+10)=30$，\n所以平均值为 $\\frac{1}{100}\\times(6\\times925+12\\times975+18\\times1025+30\\times1075+24\\times1125+10\\times1175)=1067$，故 D 错误.\n故选：C."
})

questions.append({
    "type": "单选题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:5",
    "topicId": "M3-C3-T1",
    "content": "已知曲线 $C$: $x^{2}+y^{2}=16$ ($y>0$)，从 $C$ 上任意一点 $P$ 向 $x$ 轴作垂线段 $PP'$，$P'$ 为垂足，则线段 $PP'$ 的中点 $M$ 的轨迹方程为（ ）",
    "options": "A. $\\frac{x^{2}}{16}+\\frac{y^{2}}{4}=1$ ($y>0$)\nB. $\\frac{x^{2}}{16}+\\frac{y^{2}}{8}=1$ ($y>0$)\nC. $\\frac{y^{2}}{16}+\\frac{x^{2}}{4}=1$ ($y>0$)\nD. $\\frac{y^{2}}{16}+\\frac{x^{2}}{8}=1$ ($y>0$)",
    "answer": "A",
    "solution": "【分析】设点 $M(x,y)$，由题意，根据中点的坐标表示可得 $P(x,2y)$，代入圆的方程即可求解.\n【详解】设点 $M(x,y)$，则 $P(x,y_{0}),P'(x,0)$，\n因为 $M$ 为 $PP'$ 的中点，所以 $y_{0}=2y$，即 $P(x,2y)$，\n又 $P$ 在圆 $x^{2}+y^{2}=16(y>0)$ 上，\n所以 $x^{2}+4y^{2}=16(y>0)$，即 $\\frac{x^{2}}{16}+\\frac{y^{2}}{4}=1(y>0)$，\n即点 $M$ 的轨迹方程为 $\\frac{x^{2}}{16}+\\frac{y^{2}}{4}=1(y>0)$.\n故选：A."
})

questions.append({
    "type": "单选题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:6",
    "topicId": "M4-C2-T1",
    "content": "设函数 $f(x)=a(x+1)^{2}-1$，$g(x)=\\cos x+2ax$，当 $x\\in(-1,1)$ 时，曲线 $y=f(x)$ 与 $y=g(x)$ 恰有一个交点，则 $a=$ （ ）",
    "options": "A. -1\nB. $\\frac{1}{2}$\nC. 1\nD. 2",
    "answer": "D",
    "solution": "【分析】解法一：令 $F(x)=ax^{2}+a-1,G(x)=\\cos x$，分析可知曲线 $y=F(x)$ 与 $y=G(x)$ 恰有一个交点，结合偶函数的对称性可知该交点只能在 $y$ 轴上，即可得 $a=2$，并代入检验即可；解法二：令 $h(x)=f(x)-g(x),x\\in(-1,1)$，可知 $h(x)$ 为偶函数，根据偶函数的对称性可知 $h(x)$ 的零点只能为 0，即可得 $a=2$，并代入检验即可.\n【详解】解法一：令 $f(x)=g(x)$，即 $a(x+1)^{2}-1=\\cos x+2ax$，可得 $ax^{2}+a-1=\\cos x$，\n令 $F(x)=ax^{2}+a-1,G(x)=\\cos x$，\n原题意等价于当 $x\\in(-1,1)$ 时，曲线 $y=F(x)$ 与 $y=G(x)$ 恰有一个交点，\n注意到 $F(x),G(x)$ 均为偶函数，可知该交点只能在 $y$ 轴上，\n可得 $F(0)=G(0)$，即 $a-1=1$，解得 $a=2$，\n若 $a=2$，令 $F(x)=G(x)$，可得 $2x^{2}+1-\\cos x=0$，\n因为 $x\\in(-1,1)$，则 $2x^{2}\\ge 0,1-\\cos x\\ge 0$，当且仅当 $x=0$ 时，等号成立，\n可得 $2x^{2}+1-\\cos x\\ge 0$，当且仅当 $x=0$ 时，等号成立，\n则方程 $2x^{2}+1-\\cos x=0$ 有且仅有一个实根 0，即曲线 $y=F(x)$ 与 $y=G(x)$ 恰有一个交点，\n所以 $a=2$ 符合题意；\n综上所述：$a=2$.\n解法二：令 $h(x)=f(x)-g(x)=ax^{2}+a-1-\\cos x,x\\in(-1,1)$，\n原题意等价于 $h(x)$ 有且仅有一个零点，\n因为 $h(-x)=a(-x)^{2}+a-1-\\cos(-x)=ax^{2}+a-1-\\cos x=h(x)$，\n则 $h(x)$ 为偶函数，\n根据偶函数的对称性可知 $h(x)$ 的零点只能为 0，\n即 $h(0)=a-2=0$，解得 $a=2$，\n若 $a=2$，则 $h(x)=2x^{2}+1-\\cos x,x\\in(-1,1)$，\n又因为 $2x^{2}\\ge 0,1-\\cos x\\ge 0$ 当且仅当 $x=0$ 时，等号成立，\n可得 $h(x)\\ge 0$，当且仅当 $x=0$ 时，等号成立，\n即 $h(x)$ 有且仅有一个零点 0，所以 $a=2$ 符合题意；\n故选：D."
})

questions.append({
    "type": "单选题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:7",
    "topicId": "M2-C3-T5",
    "content": "已知正三棱台 $ABC-A_{1}B_{1}C_{1}$ 的体积为 $\\frac{52}{3}$，$AB=6$，$A_{1}B_{1}=2$，则 $A_{1}A$ 与平面 $ABC$ 所成角的正切值为（ ）",
    "options": "A. $\\frac{1}{2}$\nB. 1\nC. 2\nD. 3",
    "answer": "B",
    "solution": "【分析】解法一：根据台体的体积公式可得三棱台的高 $h=\\frac{4\\sqrt{3}}{3}$，做辅助线，结合正三棱台的结构特征求得 $AM=\\frac{4\\sqrt{3}}{3}$，进而根据线面夹角的定义分析求解；解法二：将正三棱台 $ABC-A_{1}B_{1}C_{1}$ 补成正三棱锥 $P-ABC$，$A_{1}A$ 与平面 $ABC$ 所成角即为 $PA$ 与平面 $ABC$ 所成角，根据比例关系可得 $V_{P-ABC}=18$，进而可求正三棱锥 $P-ABC$ 的高，即可得结果.\n【详解】解法一：分别取 $BC,B_{1}C_{1}$ 的中点 $D,D_{1}$，则 $AD=3\\sqrt{3},A_{1}D_{1}=\\sqrt{3}$，\n可知 $S_{\\triangle ABC}=\\frac{1}{2}\\times6\\times6\\times\\frac{\\sqrt{3}}{2}=9\\sqrt{3},S_{\\triangle A_{1}B_{1}C_{1}}=\\frac{1}{2}\\times2\\times\\sqrt{3}=\\sqrt{3}$，\n设正三棱台 $ABC-A_{1}B_{1}C_{1}$ 的高为 $h$，\n则 $V_{ABC-A_{1}B_{1}C_{1}}=\\frac{1}{3}\\left(9\\sqrt{3}+\\sqrt{3}+\\sqrt{9\\sqrt{3}\\times\\sqrt{3}}\\right)h=\\frac{52}{3}$，解得 $h=\\frac{4\\sqrt{3}}{3}$，\n如图，分别过 $A_{1},D_{1}$ 作底面垂线，垂足为 $M,N$，设 $AM=x$，\n则 $AA_{1}=\\sqrt{AM^{2}+A_{1}M^{2}}=\\sqrt{x^{2}+\\frac{16}{3}}$，$DN=AD-AM-MN=2\\sqrt{3}-x$，\n可得 $DD_{1}=\\sqrt{DN^{2}+D_{1}N^{2}}=\\sqrt{\\left(2\\sqrt{3}-x\\right)^{2}+\\frac{16}{3}}$，\n结合等腰梯形 $BCC_{1}B_{1}$ 可得 $BB_{1}^{2}=\\left(\\frac{6-2}{2}\\right)^{2}+DD_{1}^{2}$，\n即 $x^{2}+\\frac{16}{3}=\\left(2\\sqrt{3}-x\\right)^{2}+\\frac{16}{3}+4$，解得 $x=\\frac{4\\sqrt{3}}{3}$，\n所以 $A_{1}A$ 与平面 $ABC$ 所成角的正切值为 $\\tan\\angle D_{1}AD=\\frac{A_{1}M}{AM}=1$；\n解法二：将正三棱台 $ABC-A_{1}B_{1}C_{1}$ 补成正三棱锥 $P-ABC$，\n则 $A_{1}A$ 与平面 $ABC$ 所成角即为 $PA$ 与平面 $ABC$ 所成角，\n因为 $\\frac{PA_{1}}{PA}=\\frac{A_{1}B_{1}}{AB}=\\frac{1}{3}$，则 $\\frac{V_{P-A_{1}B_{1}C_{1}}}{V_{P-ABC}}=\\frac{1}{27}$，\n可知 $V_{ABC-A_{1}B_{1}C_{1}}=\\frac{26}{27}V_{P-ABC}=\\frac{52}{3}$，则 $V_{P-ABC}=18$，\n设正三棱锥 $P-ABC$ 的高为 $d$，则 $V_{P-ABC}=\\frac{1}{3}d\\times\\frac{1}{2}\\times6\\times6\\times\\frac{\\sqrt{3}}{2}=18$，解得 $d=2\\sqrt{3}$，\n取底面 $ABC$ 的中心为 $O$，则 $PO\\perp$ 底面 $ABC$，且 $AO=2\\sqrt{3}$，\n所以 $PA$ 与平面 $ABC$ 所成角的正切值 $\\tan\\angle PAO=\\frac{PO}{AO}=1$.\n故选：B."
})

questions.append({
    "type": "单选题",
    "difficulty": "困难",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:8",
    "topicId": "M1-C4-T3",
    "content": "设函数 $f(x)=(x+a)\\ln(x+b)$，若 $f(x)\\ge 0$，则 $a^{2}+b^{2}$ 的最小值为（ ）",
    "options": "A. $\\frac{1}{8}$\nB. $\\frac{1}{4}$\nC. $\\frac{1}{2}$\nD. 1",
    "answer": "C",
    "solution": "【分析】解法一：由题意可知：$f(x)$ 的定义域为 $(-b,+\\infty)$，分类讨论 $-a$ 与 $-b,1-b$ 的大小关系，结合符号分析判断，即可得 $b=a+1$，代入可得最值；解法二：根据对数函数的性质分析 $\\ln(x+b)$ 的符号，进而可得 $x+a$ 的符号，即可得 $b=a+1$，代入可得最值.\n【详解】解法一：由题意可知：$f(x)$ 的定义域为 $(-b,+\\infty)$，\n令 $x+a=0$ 解得 $x=-a$；令 $\\ln(x+b)=0$ 解得 $x=1-b$；\n若 $-a\\le-b$，当 $x\\in(-b,1-b)$ 时，可知 $x+a>0,\\ln(x+b)<0$，\n此时 $f(x)<0$，不合题意；\n若 $-b<-a<1-b$，当 $x\\in(-a,1-b)$ 时，可知 $x+a>0,\\ln(x+b)<0$，\n此时 $f(x)<0$，不合题意；\n若 $-a=1-b$，当 $x\\in(-b,1-b)$ 时，可知 $x+a<0,\\ln(x+b)<0$，此时 $f(x)>0$；\n当 $x\\in[1-b,+\\infty)$ 时，可知 $x+a\\ge 0,\\ln(x+b)\\ge 0$，此时 $f(x)\\ge 0$；\n可知若 $-a=1-b$，符合题意；\n若 $-a>1-b$，当 $x\\in(1-b,-a)$ 时，可知 $x+a<0,\\ln(x+b)>0$，\n此时 $f(x)<0$，不合题意；\n综上所述：$-a=1-b$，即 $b=a+1$，\n则 $a^{2}+b^{2}=a^{2}+(a+1)^{2}=2\\left(a+\\frac{1}{2}\\right)^{2}+\\frac{1}{2}\\ge\\frac{1}{2}$，当且仅当 $a=-\\frac{1}{2},b=\\frac{1}{2}$ 时，等号成立，\n所以 $a^{2}+b^{2}$ 的最小值为 $\\frac{1}{2}$；\n解法二：由题意可知：$f(x)$ 的定义域为 $(-b,+\\infty)$，\n令 $x+a=0$ 解得 $x=-a$；令 $\\ln(x+b)=0$ 解得 $x=1-b$；\n则当 $x\\in(-b,1-b)$ 时，$\\ln(x+b)<0$，故 $x+a\\le 0$，所以 $1-b+a\\le 0$；\n$x\\in(1-b,+\\infty)$ 时，$\\ln(x+b)>0$，故 $x+a\\ge 0$，所以 $1-b+a\\ge 0$；\n故 $1-b+a=0$，则 $a^{2}+b^{2}=a^{2}+(a+1)^{2}=2\\left(a+\\frac{1}{2}\\right)^{2}+\\frac{1}{2}\\ge\\frac{1}{2}$，\n当且仅当 $a=-\\frac{1}{2},b=\\frac{1}{2}$ 时，等号成立，\n所以 $a^{2}+b^{2}$ 的最小值为 $\\frac{1}{2}$.\n故选：C.\n【点睛】关键点点睛：分别求 $x+a=0$、$\\ln(x+b)=0$ 的根，以根和函数定义域为临界，比较大小分类讨论，结合符号性分析判断."
})

# ============ 二、多项选择题（题9-11） ============

questions.append({
    "type": "多选题",
    "difficulty": "简单",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:9",
    "topicId": "M1-C5-T2",
    "content": "对于函数 $f(x)=\\sin 2x$ 和 $g(x)=\\sin\\left(2x-\\frac{\\pi}{4}\\right)$，下列正确的有（ ）",
    "options": "A. $f(x)$ 与 $g(x)$ 有相同零点\nB. $f(x)$ 与 $g(x)$ 有相同最大值\nC. $f(x)$ 与 $g(x)$ 有相同的最小正周期\nD. $f(x)$ 与 $g(x)$ 的图像有相同的对称轴",
    "answer": "BC",
    "solution": "【分析】根据正弦函数的零点，最值，周期公式，对称轴方程逐一分析每个选项即可.\n【详解】A 选项，令 $f(x)=\\sin 2x=0$，解得 $x=\\frac{k\\pi}{2},k\\in\\mathbf{Z}$，即为 $f(x)$ 零点，\n令 $g(x)=\\sin\\left(2x-\\frac{\\pi}{4}\\right)=0$，解得 $x=\\frac{k\\pi}{2}+\\frac{\\pi}{8},k\\in\\mathbf{Z}$，即为 $g(x)$ 零点，\n显然 $f(x),g(x)$ 零点不同，A 选项错误；\nB 选项，显然 $f(x)_{\\max}=g(x)_{\\max}=1$，B 选项正确；\nC 选项，根据周期公式，$f(x),g(x)$ 的周期均为 $\\frac{2\\pi}{2}=\\pi$，C 选项正确；\nD 选项，根据正弦函数的性质 $f(x)$ 的对称轴满足 $2x=k\\pi+\\frac{\\pi}{2}\\Leftrightarrow x=\\frac{k\\pi}{2}+\\frac{\\pi}{4},k\\in\\mathbf{Z}$，\n$g(x)$ 的对称轴满足 $2x-\\frac{\\pi}{4}=k\\pi+\\frac{\\pi}{2}\\Leftrightarrow x=\\frac{k\\pi}{2}+\\frac{3\\pi}{8},k\\in\\mathbf{Z}$，\n显然 $f(x),g(x)$ 图像的对称轴不同，D 选项错误.\n故选：BC."
})

questions.append({
    "type": "多选题",
    "difficulty": "困难",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:10",
    "topicId": "M3-C3-T3",
    "content": "抛物线 $C: y^{2}=4x$ 的准线为 $l$，$P$ 为 $C$ 上的动点，过 $P$ 作 $\\odot A: x^{2}+(y-4)^{2}=1$ 的一条切线，$Q$ 为切点，过 $P$ 作 $l$ 的垂线，垂足为 $B$，则（ ）",
    "options": "A. $l$ 与 $\\odot A$ 相切\nB. 当 $P,A,B$ 三点共线时，$|PQ|=\\sqrt{15}$\nC. 当 $|PB|=2$ 时，$PA\\perp AB$\nD. 满足 $|PA|=|PB|$ 的点 $P$ 有且仅有 2 个",
    "answer": "ABD",
    "solution": "【分析】A 选项，抛物线准线为 $x=-1$，根据圆心到准线的距离来判断；B 选项，$P,A,B$ 三点共线时，先求出 $P$ 的坐标，进而得出切线长；C 选项，根据 $|PB|=2$ 先算出 $P$ 的坐标，然后验证 $k_{PA}k_{AB}=-1$ 是否成立；D 选项，根据抛物线的定义，$|PB|=|PF|$，于是问题转化成 $|PA|=|PF|$ 的 $P$ 点的存在性问题，此时考察 $AF$ 的中垂线和抛物线的交点个数即可，亦可直接设 $P$ 点坐标进行求解.\n【详解】A 选项，抛物线 $y^{2}=4x$ 的准线为 $x=-1$，\n$\\odot A$ 的圆心 $(0,4)$ 到直线 $x=-1$ 的距离显然是 1，等于圆的半径，\n故准线 $l$ 和 $\\odot A$ 相切，A 选项正确；\nB 选项，$P,A,B$ 三点共线时，即 $PA\\perp l$，则 $P$ 的纵坐标 $y_{P}=4$，\n由 $y_{P}^{2}=4x_{P}$，得到 $x_{P}=4$，故 $P(4,4)$，\n此时切线长 $|PQ|=\\sqrt{|PA|^{2}-r^{2}}=\\sqrt{4^{2}-1^{2}}=\\sqrt{15}$，B 选项正确；\nC 选项，当 $|PB|=2$ 时，$x_{P}=1$，此时 $y_{P}^{2}=4x_{P}=4$，故 $P(1,2)$ 或 $P(1,-2)$，\n当 $P(1,2)$ 时，$A(0,4),B(-1,2)$，$k_{PA}=\\frac{4-2}{0-1}=-2$，$k_{AB}=\\frac{4-2}{0-(-1)}=2$，\n不满足 $k_{PA}k_{AB}=-1$；\n当 $P(1,-2)$ 时，$A(0,4),B(-1,2)$，$k_{PA}=\\frac{4-(-2)}{0-1}=-6$，$k_{AB}=\\frac{4-(-2)}{0-(-1)}=6$，\n不满足 $k_{PA}k_{AB}=-1$；\n于是 $PA\\perp AB$ 不成立，C 选项错误；\nD 选项，方法一：利用抛物线定义转化\n根据抛物线的定义，$|PB|=|PF|$，这里 $F(1,0)$，\n于是 $|PA|=|PB|$ 时 $P$ 点的存在性问题转化成 $|PA|=|PF|$ 时 $P$ 点的存在性问题，\n$A(0,4),F(1,0)$，$AF$ 中点 $\\left(\\frac{1}{2},2\\right)$，$AF$ 中垂线的斜率为 $-\\frac{1}{k_{AF}}=\\frac{1}{4}$，\n于是 $AF$ 的中垂线方程为：$y=\\frac{2x+15}{8}$，与抛物线 $y^{2}=4x$ 联立可得 $y^{2}-16y+30=0$，\n$\\Delta=16^{2}-4\\times30=136>0$，即 $AF$ 的中垂线和抛物线有两个交点，\n即存在两个 $P$ 点，使得 $|PA|=|PF|$，D 选项正确.\n方法二：（设点直接求解）\n设 $P\\left(\\frac{t^{2}}{4},t\\right)$，由 $PB\\perp l$ 可得 $B(-1,t)$，又 $A(0,4)$，又 $|PA|=|PB|$，\n根据两点间的距离公式，$\\sqrt{\\frac{t^{4}}{16}+(t-4)^{2}}=\\frac{t^{2}}{4}+1$，整理得 $t^{2}-16t+30=0$，\n$\\Delta=16^{2}-4\\times30=136>0$，则关于 $t$ 的方程有两个解，\n即存在两个这样的 $P$ 点，D 选项正确.\n故选：ABD."
})

questions.append({
    "type": "多选题",
    "difficulty": "困难",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:11",
    "topicId": "M4-C2-T5",
    "content": "设函数 $f(x)=2x^{3}-3ax^{2}+1$，则（ ）",
    "options": "A. 当 $a>1$ 时，$f(x)$ 有三个零点\nB. 当 $a<0$ 时，$x=0$ 是 $f(x)$ 的极大值点\nC. 存在 $a,b$，使得 $x=b$ 为曲线 $y=f(x)$ 的对称轴\nD. 存在 $a$，使得点 $(1,f(1))$ 为曲线 $y=f(x)$ 的对称中心",
    "answer": "AD",
    "solution": "【分析】A 选项，先分析出函数的极值点为 $x=0,x=a$，根据零点存在定理和极值的符号判断出 $f(x)$ 在 $(-1,0),(0,a),(a,2a)$ 上各有一个零点；B 选项，根据极值和导函数符号的关系进行分析；C 选项，假设存在这样的 $a,b$，使得 $x=b$ 为 $f(x)$ 的对称轴，则 $f(x)=f(2b-x)$ 为恒等式，据此计算判断；D 选项，若存在这样的 $a$，使得 $(1,3-3a)$ 为 $f(x)$ 的对称中心，则 $f(x)+f(2-x)=6-6a$，据此进行计算判断，亦可利用拐点结论直接求解.\n【详解】A 选项，$f'(x)=6x^{2}-6ax=6x(x-a)$，由于 $a>1$，\n故 $x\\in(-\\infty,0)\\cup(a,+\\infty)$ 时 $f'(x)>0$，故 $f(x)$ 在 $(-\\infty,0),(a,+\\infty)$ 上单调递增，\n$x\\in(0,a)$ 时，$f'(x)<0$，$f(x)$ 单调递减，\n则 $f(x)$ 在 $x=0$ 处取到极大值，在 $x=a$ 处取到极小值，\n由 $f(0)=1>0$，$f(a)=1-a^{3}<0$，则 $f(0)f(a)<0$，\n根据零点存在定理 $f(x)$ 在 $(0,a)$ 上有一个零点，\n又 $f(-1)=-1-3a<0$，$f(2a)=4a^{3}+1>0$，则 $f(-1)f(0)<0,f(a)f(2a)<0$，\n则 $f(x)$ 在 $(-1,0),(a,2a)$ 上各有一个零点，于是 $a>1$ 时，$f(x)$ 有三个零点，A 选项正确；\nB 选项，$f'(x)=6x(x-a)$，$a<0$ 时，$x\\in(a,0),f'(x)<0$，$f(x)$ 单调递减，\n$x\\in(0,+\\infty)$ 时 $f'(x)>0$，$f(x)$ 单调递增，\n此时 $f(x)$ 在 $x=0$ 处取到极小值，B 选项错误；\nC 选项，假设存在这样的 $a,b$，使得 $x=b$ 为 $f(x)$ 的对称轴，\n即存在这样的 $a,b$ 使得 $f(x)=f(2b-x)$，\n即 $2x^{3}-3ax^{2}+1=2(2b-x)^{3}-3a(2b-x)^{2}+1$，\n根据二项式定理，等式右边 $(2b-x)^{3}$ 展开式含有 $x^{3}$ 的项为 $2C_{3}^{3}(2b)^{0}(-x)^{3}=-2x^{3}$，\n于是等式左右两边 $x^{3}$ 的系数都不相等，原等式不可能恒成立，\n于是不存在这样的 $a,b$，使得 $x=b$ 为 $f(x)$ 的对称轴，C 选项错误；\nD 选项，\n方法一：利用对称中心的表达式化简\n$f(1)=3-3a$，若存在这样的 $a$，使得 $(1,3-3a)$ 为 $f(x)$ 的对称中心，\n则 $f(x)+f(2-x)=6-6a$，事实上，\n$f(x)+f(2-x)=2x^{3}-3ax^{2}+1+2(2-x)^{3}-3a(2-x)^{2}+1=(12-6a)x^{2}+(12a-24)x+18-12a$，\n于是 $6-6a=(12-6a)x^{2}+(12a-24)x+18-12a$\n即 $\\begin{cases} 12-6a=0 \\\\ 12a-24=0 \\\\ 18-12a=6-6a \\end{cases}$，解得 $a=2$，即存在 $a=2$ 使得 $(1,f(1))$ 是 $f(x)$ 的对称中心，D 选项正确.\n方法二：直接利用拐点结论\n任何三次函数都有对称中心，对称中心的横坐标是二阶导数的零点，\n$f(x)=2x^{3}-3ax^{2}+1$，$f'(x)=6x^{2}-6ax$，$f''(x)=12x-6a$，\n由 $f''(x)=0\\Leftrightarrow x=\\frac{a}{2}$，于是该三次函数的对称中心为 $\\left(\\frac{a}{2},f\\left(\\frac{a}{2}\\right)\\right)$，\n由题意 $(1,f(1))$ 也是对称中心，故 $\\frac{a}{2}=1\\Leftrightarrow a=2$，\n即存在 $a=2$ 使得 $(1,f(1))$ 是 $f(x)$ 的对称中心，D 选项正确.\n故选：AD\n【点睛】结论点睛：（1）$f(x)$ 的对称轴为 $x=b\\Leftrightarrow f(x)=f(2b-x)$；（2）$f(x)$ 关于 $(a,b)$ 对称 $\\Leftrightarrow f(x)+f(2a-x)=2b$；（3）任何三次函数 $f(x)=ax^{3}+bx^{2}+cx+d$ 都有对称中心，对称中心是三次函数的拐点，对称中心的横坐标是 $f''(x)=0$ 的解，即 $\\left(-\\frac{b}{3a},f\\left(-\\frac{b}{3a}\\right)\\right)$ 是三次函数的对称中心."
})

# ============ 三、填空题（题12-14） ============

questions.append({
    "type": "填空题",
    "difficulty": "简单",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:12",
    "topicId": "M4-C1-T2",
    "content": "记 $S_{n}$ 为等差数列 $\\{a_{n}\\}$ 的前 $n$ 项和，若 $a_{3}+a_{4}=7$，$3a_{2}+a_{5}=5$，则 $S_{10}=$ ______.",
    "options": "",
    "answer": "95",
    "solution": "【分析】利用等差数列通项公式得到方程组，解出 $a_{1},d$，再利用等差数列的求和公式节即可得到答案.\n【详解】因为数列 $a_{n}$ 为等差数列，则由题意得 $\\begin{cases} a_{1}+2d+a_{1}+3d=7 \\\\ 3(a_{1}+d)+a_{1}+4d=5 \\end{cases}$，解得 $\\begin{cases} a_{1}=-4 \\\\ d=3 \\end{cases}$，\n则 $S_{10}=10a_{1}+\\frac{10\\times9}{2}d=10\\times(-4)+45\\times3=95$.\n故答案为：95."
})

questions.append({
    "type": "填空题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:13",
    "topicId": "M1-C5-T6",
    "content": "已知 $\\alpha$ 为第一象限角，$\\beta$ 为第三象限角，$\\tan\\alpha+\\tan\\beta=4$，$\\tan\\alpha\\tan\\beta=\\sqrt{2}+1$，则 $\\sin(\\alpha+\\beta)=$ ______.",
    "options": "",
    "answer": "$-\\frac{2\\sqrt{2}}{3}$",
    "solution": "【分析】法一：根据两角和与差的正切公式得 $\\tan(\\alpha+\\beta)=-2\\sqrt{2}$，再缩小 $\\alpha+\\beta$ 的范围，最后结合同角的平方和关系即可得到答案；法二：利用弦化切的方法即可得到答案.\n【详解】法一：由题意得 $\\tan(\\alpha+\\beta)=\\frac{\\tan\\alpha+\\tan\\beta}{1-\\tan\\alpha\\tan\\beta}=\\frac{4}{1-(\\sqrt{2}+1)}=-2\\sqrt{2}$，\n因为 $\\alpha\\in\\left(2k\\pi,2k\\pi+\\frac{\\pi}{2}\\right),\\beta\\in\\left(2m\\pi+\\pi,2m\\pi+\\frac{3\\pi}{2}\\right),k,m\\in\\mathbf{Z}$，\n则 $\\alpha+\\beta\\in\\left((2m+2k)\\pi+\\pi,(2m+2k)\\pi+2\\pi\\right),k,m\\in\\mathbf{Z}$，\n又因为 $\\tan(\\alpha+\\beta)=-2\\sqrt{2}<0$，\n则 $\\alpha+\\beta\\in\\left((2m+2k)\\pi+\\frac{3\\pi}{2},(2m+2k)\\pi+2\\pi\\right),k,m\\in\\mathbf{Z}$，则 $\\sin(\\alpha+\\beta)<0$，\n则 $\\frac{\\sin(\\alpha+\\beta)}{\\cos(\\alpha+\\beta)}=-2\\sqrt{2}$，联立 $\\sin^{2}(\\alpha+\\beta)+\\cos^{2}(\\alpha+\\beta)=1$，解得 $\\sin(\\alpha+\\beta)=-\\frac{2\\sqrt{2}}{3}$.\n法二：因为 $\\alpha$ 为第一象限角，$\\beta$ 为第三象限角，则 $\\cos\\alpha>0,\\cos\\beta<0$，\n$\\cos\\alpha=\\frac{\\cos\\alpha}{\\sqrt{\\sin^{2}\\alpha+\\cos^{2}\\alpha}}=\\frac{1}{\\sqrt{1+\\tan^{2}\\alpha}}$，$\\cos\\beta=\\frac{\\cos\\beta}{\\sqrt{\\sin^{2}\\beta+\\cos^{2}\\beta}}=\\frac{-1}{\\sqrt{1+\\tan^{2}\\beta}}$，\n则 $\\sin(\\alpha+\\beta)=\\sin\\alpha\\cos\\beta+\\cos\\alpha\\sin\\beta=\\cos\\alpha\\cos\\beta(\\tan\\alpha+\\tan\\beta)$\n$=4\\cos\\alpha\\cos\\beta=\\frac{-4}{\\sqrt{1+\\tan^{2}\\alpha}\\sqrt{1+\\tan^{2}\\beta}}=\\frac{-4}{\\sqrt{(\\tan\\alpha+\\tan\\beta)^{2}+(\\tan\\alpha\\tan\\beta-1)^{2}}}=\\frac{-4}{\\sqrt{4^{2}+2}}=-\\frac{2\\sqrt{2}}{3}$\n故答案为：$-\\frac{2\\sqrt{2}}{3}$."
})

questions.append({
    "type": "填空题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:14",
    "topicId": "M2-C5-T1",
    "content": "在如图的 $4\\times4$ 方格表中选 4 个方格，要求每行和每列均恰有一个方格被选中，则共有______种选法，在所有符合上述要求的选法中，选中方格中的 4 个数之和的最大值是______.\n\n| 11 | 21 | 31 | 40 |\n|:---|:---:|:---:|:---:|\n| 12 | 22 | 33 | 42 |\n| 13 | 22 | 33 | 43 |\n| 15 | 24 | 34 | 44 |",
    "options": "",
    "answer": "①. 24 ②. 112",
    "solution": "【分析】由题意可知第一、二、三、四列分别有 4、3、2、1 个方格可选；利用列举法写出所有的可能结果，即可求解.\n【详解】由题意知，选 4 个方格，每行和每列均恰有一个方格被选中，\n则第一列有 4 个方格可选，第二列有 3 个方格可选，\n第三列有 2 个方格可选，第四列有 1 个方格可选，\n所以共有 $4\\times3\\times2\\times1=24$ 种选法；\n每种选法可标记为 $(a,b,c,d)$，$a,b,c,d$ 分别表示第一、二、三、四列的数字，\n则所有的可能结果为：\n(11,22,33,44),(11,22,34,43),(11,22,33,44),(11,22,34,42),(11,24,33,43),(11,24,33,42),\n(12,21,33,44),(12,21,34,43),(12,22,31,44),(12,22,34,40),(12,24,31,43),(12,24,33,40),\n(13,21,33,44),(13,21,34,42),(13,22,31,44),(13,22,34,40),(13,24,31,42),(13,24,33,40),\n(15,21,33,43),(15,21,33,42),(15,22,31,43),(15,22,33,40),(15,22,31,42),(15,22,33,40),\n所以选中的方格中，(15,21,33,43) 的 4 个数之和最大，为 $15+21+33+43=112$.\n故答案为：24；112\n【点睛】关键点点睛：解决本题的关键是确定第一、二、三、四列分别有 4、3、2、1 个方格可选，利用列举法写出所有的可能结果."
})

# ============ 四、解答题（题15-19） ============

questions.append({
    "type": "解答题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:15",
    "topicId": "M1-C5-T6",
    "content": "记 $\\triangle ABC$ 的内角 $A$，$B$，$C$ 的对边分别为 $a$，$b$，$c$，已知 $\\sin A+\\sqrt{3}\\cos A=2$.\n（1）求 $A$.\n（2）若 $a=2$，$\\sqrt{2}b\\sin C=c\\sin 2B$，求 $\\triangle ABC$ 的周长.",
    "options": "",
    "answer": "（1）$A=\\frac{\\pi}{6}$\n（2）$2+\\sqrt{6}+3\\sqrt{2}$",
    "solution": "【分析】（1）根据辅助角公式对条件 $\\sin A+\\sqrt{3}\\cos A=2$ 进行化简处理即可求解，常规方法还可利用同角三角函数的关系解方程组，亦可利用导数，向量数量积公式，万能公式解决；\n（2）先根据正弦定理边角互化算出 $B$，然后根据正弦定理算出 $b,c$ 即可得出周长.\n【小问1详解】\n方法一：常规方法（辅助角公式）\n由 $\\sin A+\\sqrt{3}\\cos A=2$ 可得 $\\frac{1}{2}\\sin A+\\frac{\\sqrt{3}}{2}\\cos A=1$，即 $\\sin\\left(A+\\frac{\\pi}{3}\\right)=1$，\n由于 $A\\in(0,\\pi)\\Rightarrow A+\\frac{\\pi}{3}\\in\\left(\\frac{\\pi}{3},\\frac{4\\pi}{3}\\right)$，故 $A+\\frac{\\pi}{3}=\\frac{\\pi}{2}$，解得 $A=\\frac{\\pi}{6}$.\n方法二：常规方法（同角三角函数的基本关系）\n由 $\\sin A+\\sqrt{3}\\cos A=2$，又 $\\sin^{2}A+\\cos^{2}A=1$，消去 $\\sin A$ 得到：\n$4\\cos^{2}A-4\\sqrt{3}\\cos A+3=0\\Leftrightarrow(2\\cos A-\\sqrt{3})^{2}=0$，解得 $\\cos A=\\frac{\\sqrt{3}}{2}$，\n又 $A\\in(0,\\pi)$，故 $A=\\frac{\\pi}{6}$.\n方法三：利用极值点求解\n设 $f(x)=\\sin x+\\sqrt{3}\\cos x(0<x<\\pi)$，则 $f(x)=2\\sin\\left(x+\\frac{\\pi}{3}\\right)(0<x<\\pi)$，\n显然 $x=\\frac{\\pi}{6}$ 时，$f(x)_{\\max}=2$，注意到 $f(A)=\\sin A+\\sqrt{3}\\cos A=2=2\\sin\\left(A+\\frac{\\pi}{3}\\right)$，\n$f(x)_{\\max}=f(A)$，在开区间 $(0,\\pi)$ 上取到最大值，于是 $x=A$ 必定是极值点，\n即 $f'(A)=0=\\cos A-\\sqrt{3}\\sin A$，即 $\\tan A=\\frac{\\sqrt{3}}{3}$，\n又 $A\\in(0,\\pi)$，故 $A=\\frac{\\pi}{6}$.\n方法四：利用向量数量积公式（柯西不等式）\n设 $\\vec{a}=(1,\\sqrt{3}),\\vec{b}=(\\sin A,\\cos A)$，由题意，$\\vec{a}\\cdot\\vec{b}=\\sin A+\\sqrt{3}\\cos A=2$，\n根据向量的数量积公式，$\\vec{a}\\cdot\\vec{b}=|\\vec{a}||\\vec{b}|\\cos\\langle\\vec{a},\\vec{b}\\rangle=2\\cos\\langle\\vec{a},\\vec{b}\\rangle$，\n则 $2\\cos\\langle\\vec{a},\\vec{b}\\rangle=2\\Leftrightarrow\\cos\\langle\\vec{a},\\vec{b}\\rangle=1$，此时 $\\vec{a},\\vec{b}$ 同向共线，\n则根据向量共线定理，存在 $\\lambda>0$，使得 $\\vec{b}=\\lambda\\vec{a}$，\n即 $\\sin A=\\lambda,\\cos A=\\sqrt{3}\\lambda$，所以 $\\tan A=\\frac{\\sin A}{\\cos A}=\\frac{\\lambda}{\\sqrt{3}\\lambda}=\\frac{\\sqrt{3}}{3}$，\n又 $A\\in(0,\\pi)$，故 $A=\\frac{\\pi}{6}$.\n【小问2详解】\n由题设条件和正弦定理\n$\\sqrt{2}b\\sin C=c\\sin 2B\\Leftrightarrow\\sqrt{2}\\sin B\\sin C=2\\sin C\\sin B\\cos B$，\n又 $B,C\\in(0,\\pi)$，则 $\\sin B\\sin C\\neq0$，进而 $\\cos B=\\frac{\\sqrt{2}}{2}$，得到 $B=\\frac{\\pi}{4}$，\n于是 $C=\\pi-A-B=\\frac{7\\pi}{12}$，\n$\\sin C=\\sin(\\pi-A-B)=\\sin(A+B)=\\sin A\\cos B+\\sin B\\cos A=\\frac{\\sqrt{2}+\\sqrt{6}}{4}$，\n由正弦定理可得，$\\frac{a}{\\sin A}=\\frac{b}{\\sin B}=\\frac{c}{\\sin C}$，即 $\\frac{2}{\\sin\\frac{\\pi}{6}}=\\frac{b}{\\sin\\frac{\\pi}{4}}=\\frac{c}{\\sin\\frac{7\\pi}{12}}$，\n解得 $b=2\\sqrt{2},c=\\sqrt{6}+\\sqrt{2}$，\n故 $\\triangle ABC$ 的周长为 $2+\\sqrt{6}+3\\sqrt{2}$."
})

questions.append({
    "type": "解答题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:16",
    "topicId": "M4-C2-T4",
    "content": "已知函数 $f(x)=\\mathrm{e}^{x}-ax-a^{3}$.\n（1）当 $a=1$ 时，求曲线 $y=f(x)$ 在点 $(1,f(1))$ 处的切线方程；\n（2）若 $f(x)$ 有极小值，且极小值小于 0，求 $a$ 的取值范围.",
    "options": "",
    "answer": "（1）$(\\mathrm{e}-1)x-y-1=0$\n（2）$(1,+\\infty)$",
    "solution": "【分析】（1）求导，结合导数的几何意义求切线方程；\n（2）解法一：求导，分析 $a\\le 0$ 和 $a>0$ 两种情况，利用导数判断单调性和极值，分析可得 $a^{2}+\\ln a-1>0$，构造函数解不等式即可；解法二：求导，可知 $f'(x)=\\mathrm{e}^{x}-a$ 有零点，可得 $a>0$，进而利用导数求 $f(x)$ 的单调性和极值，分析可得 $a^{2}+\\ln a-1>0$，构造函数解不等式即可.\n【小问1详解】\n当 $a=1$ 时，则 $f(x)=\\mathrm{e}^{x}-x-1$，$f'(x)=\\mathrm{e}^{x}-1$，\n可得 $f(1)=\\mathrm{e}-2$，$f'(1)=\\mathrm{e}-1$，\n即切点坐标为 $(1,\\mathrm{e}-2)$，切线斜率 $k=\\mathrm{e}-1$，\n所以切线方程为 $y-(\\mathrm{e}-2)=(\\mathrm{e}-1)(x-1)$，即 $(\\mathrm{e}-1)x-y-1=0$.\n【小问2详解】\n解法一：因为 $f(x)$ 的定义域为 $\\mathbf{R}$，且 $f'(x)=\\mathrm{e}^{x}-a$，\n若 $a\\le 0$，则 $f'(x)\\ge 0$ 对任意 $x\\in\\mathbf{R}$ 恒成立，\n可知 $f(x)$ 在 $\\mathbf{R}$ 上单调递增，无极值，不合题意；\n若 $a>0$，令 $f'(x)>0$，解得 $x>\\ln a$；令 $f'(x)<0$，解得 $x<\\ln a$；\n可知 $f(x)$ 在 $(-\\infty,\\ln a)$ 内单调递减，在 $(\\ln a,+\\infty)$ 内单调递增，\n则 $f(x)$ 有极小值 $f(\\ln a)=a-a\\ln a-a^{3}$，无极大值，\n由题意可得：$f(\\ln a)=a-a\\ln a-a^{3}<0$，即 $a^{2}+\\ln a-1>0$，\n构建 $g(a)=a^{2}+\\ln a-1,a>0$，则 $g'(a)=2a+\\frac{1}{a}>0$，\n可知 $g(a)$ 在 $(0,+\\infty)$ 内单调递增，且 $g(1)=0$，\n不等式 $a^{2}+\\ln a-1>0$ 等价于 $g(a)>g(1)$，解得 $a>1$，\n所以 $a$ 的取值范围为 $(1,+\\infty)$；\n解法二：因为 $f(x)$ 的定义域为 $\\mathbf{R}$，且 $f'(x)=\\mathrm{e}^{x}-a$，\n若 $f(x)$ 有极小值，则 $f'(x)=\\mathrm{e}^{x}-a$ 有零点，\n令 $f'(x)=\\mathrm{e}^{x}-a=0$，可得 $\\mathrm{e}^{x}=a$，\n可知 $y=\\mathrm{e}^{x}$ 与 $y=a$ 有交点，则 $a>0$，\n若 $a>0$，令 $f'(x)>0$，解得 $x>\\ln a$；令 $f'(x)<0$，解得 $x<\\ln a$；\n可知 $f(x)$ 在 $(-\\infty,\\ln a)$ 内单调递减，在 $(\\ln a,+\\infty)$ 内单调递增，\n则 $f(x)$ 有极小值 $f(\\ln a)=a-a\\ln a-a^{3}$，无极大值，符合题意，\n由题意可得：$f(\\ln a)=a-a\\ln a-a^{3}<0$，即 $a^{2}+\\ln a-1>0$，\n构建 $g(a)=a^{2}+\\ln a-1,a>0$，\n因为则 $y=a^{2},y=\\ln a-1$ 在 $(0,+\\infty)$ 内单调递增，\n可知 $g(a)$ 在 $(0,+\\infty)$ 内单调递增，且 $g(1)=0$，\n不等式 $a^{2}+\\ln a-1>0$ 等价于 $g(a)>g(1)$，解得 $a>1$，\n所以 $a$ 的取值范围为 $(1,+\\infty)$."
})

questions.append({
    "type": "解答题",
    "difficulty": "中等",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:17",
    "topicId": "M3-C1-T5",
    "content": "如图，平面四边形 $ABCD$ 中，$AB=8$，$CD=3$，$AD=5\\sqrt{3}$，$\\angle ADC=90^\\circ$，$\\angle BAD=30^\\circ$，点 $E$，$F$ 满足 $\\overrightarrow{AE}=\\frac{2}{5}\\overrightarrow{AD}$，$\\overrightarrow{AF}=\\frac{1}{2}\\overrightarrow{AB}$，将 $\\triangle AEF$ 沿 $EF$ 对折至 $\\triangle PEF$，使得 $PC=4\\sqrt{3}$.\n（1）证明：$EF\\perp PD$；\n（2）求面 $PCD$ 与面 $PBF$ 所成的二面角的正弦值.",
    "options": "",
    "answer": "（1）证明见解析\n（2）$\\frac{8\\sqrt{65}}{65}$",
    "solution": "【分析】（1）由题意，根据余弦定理求得 $EF=2$，利用勾股定理的逆定理可证得 $EF\\perp AD$，则 $EF\\perp PE,EF\\perp DE$，结合线面垂直的判定定理与性质即可证明；\n（2）由（1），根据线面垂直的判定定理与性质可证明 $PE\\perp ED$，建立如图空间直角坐标系 $E-xyz$，利用空间向量法求解面面角即可.\n【小问1详解】\n由 $AB=8,AD=5\\sqrt{3},\\overrightarrow{AE}=\\frac{2}{5}\\overrightarrow{AD},\\overrightarrow{AF}=\\frac{1}{2}\\overrightarrow{AB}$，\n得 $AE=2\\sqrt{3},AF=4$，又 $\\angle BAD=30^\\circ$，在 $\\triangle AEF$ 中，\n由余弦定理得 $EF=\\sqrt{AE^{2}+AF^{2}-2AE\\cdot AF\\cos\\angle BAD}=\\sqrt{16+12-2\\cdot4\\cdot2\\sqrt{3}\\cdot\\frac{\\sqrt{3}}{2}}=2$，\n所以 $AE^{2}+EF^{2}=AF^{2}$，则 $AE\\perp EF$，即 $EF\\perp AD$，\n所以 $EF\\perp PE,EF\\perp DE$，又 $PE\\cap DE=E,PE,DE\\subset$ 平面 $PDE$，\n所以 $EF\\perp$ 平面 $PDE$，又 $PD\\subset$ 平面 $PDE$，\n故 $EF\\perp PD$；\n【小问2详解】\n连接 $CE$，由 $\\angle ADC=90^\\circ,ED=3\\sqrt{3},CD=3$，则 $CE^{2}=ED^{2}+CD^{2}=36$，\n在 $\\triangle PEC$ 中，$PC=4\\sqrt{3},PE=2\\sqrt{3},EC=6$，得 $EC^{2}+PE^{2}=PC^{2}$，\n所以 $PE\\perp EC$，由（1）知 $PE\\perp EF$，又 $EC\\cap EF=E,EC,EF\\subset$ 平面 $ABCD$，\n所以 $PE\\perp$ 平面 $ABCD$，又 $ED\\subset$ 平面 $ABCD$，\n所以 $PE\\perp ED$，则 $PE,EF,ED$ 两两垂直，建立如图空间直角坐标系 $E-xyz$，\n则 $E(0,0,0),P(0,0,2\\sqrt{3}),D(0,3\\sqrt{3},0),C(3,3\\sqrt{3},0),F(2,0,0),A(0,-2\\sqrt{3},0)$，\n由 $F$ 是 $AB$ 的中点，得 $B(4,2\\sqrt{3},0)$，\n所以 $\\overrightarrow{PC}=(3,3\\sqrt{3},-2\\sqrt{3}),\\overrightarrow{PD}=(0,3\\sqrt{3},-2\\sqrt{3}),\\overrightarrow{PB}=(4,2\\sqrt{3},-2\\sqrt{3}),\\overrightarrow{PF}=(2,0,-2\\sqrt{3})$，\n设平面 $PCD$ 和平面 $PBF$ 的一个法向量分别为 $\\vec{n}=(x_{1},y_{1},z_{1}),\\vec{m}=(x_{2},y_{2},z_{2})$，\n则 $\\begin{cases} \\vec{n}\\cdot\\overrightarrow{PC}=3x_{1}+3\\sqrt{3}y_{1}-2\\sqrt{3}z_{1}=0 \\\\ \\vec{n}\\cdot\\overrightarrow{PD}=3\\sqrt{3}y_{1}-2\\sqrt{3}z_{1}=0 \\end{cases}$，$\\begin{cases} \\vec{m}\\cdot\\overrightarrow{PB}=4x_{2}+2\\sqrt{3}y_{2}-2\\sqrt{3}z_{2}=0 \\\\ \\vec{m}\\cdot\\overrightarrow{PF}=2x_{2}-2\\sqrt{3}z_{2}=0 \\end{cases}$，\n令 $y_{1}=2,x_{2}=\\sqrt{3}$，得 $x_{1}=0,z_{1}=3,y_{2}=-1,z_{2}=1$，\n所以 $\\vec{n}=(0,2,3),\\vec{m}=(\\sqrt{3},-1,1)$，\n所以 $|\\cos\\langle\\vec{m},\\vec{n}\\rangle|=\\frac{|\\vec{m}\\cdot\\vec{n}|}{|\\vec{m}||\\vec{n}|}=\\frac{1}{\\sqrt{5}\\cdot\\sqrt{13}}=\\frac{\\sqrt{65}}{65}$，\n设平面 $PCD$ 和平面 $PBF$ 所成角为 $\\theta$，则 $\\sin\\theta=\\sqrt{1-\\cos^{2}\\theta}=\\frac{8\\sqrt{65}}{65}$，\n即平面 $PCD$ 和平面 $PBF$ 所成角的正弦值为 $\\frac{8\\sqrt{65}}{65}$."
})

questions.append({
    "type": "解答题",
    "difficulty": "困难",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:18",
    "topicId": "M5-C2-OTHER",
    "content": "某投篮比赛分为两个阶段，每个参赛队由两名队员组成，比赛具体规则如下：第一阶段由参赛队中一名队员投篮 3 次，若 3 次都未投中，则该队被淘汰，比赛成绩为 0 分；若至少投中一次，则该队进入第二阶段，由该队的另一名队员投篮 3 次，每次投中得 5 分，未投中得 0 分。该队的比赛成绩为第二阶段的得分总和。某参赛队由甲、乙两名队员组成，设甲每次投中的概率为 $p$，乙每次投中的概率为 $q$，各次投中与否相互独立。\n（1）若 $p=0.4$，$q=0.5$，甲参加第一阶段比赛，求甲、乙所在队的比赛成绩不少于 5 分的概率。\n（2）假设 $0<p<q$，\n（i）为使得甲、乙所在队的比赛成绩为 15 分的概率最大，应该由谁参加第一阶段比赛？\n（ii）为使得甲、乙所在队的比赛成绩的数学期望最大，应该由谁参加第一阶段比赛？",
    "options": "",
    "answer": "（1）0.686\n（2）（i）由甲参加第一阶段比赛；（ii）由甲参加第一阶段比赛",
    "solution": "【分析】（1）根据对立事件的求法和独立事件的乘法公式即可得到答案；\n（2）（i）首先各自计算出 $P_{\\text{甲}}=[1-(1-p)^{3}]q^{3}$，$P_{\\text{乙}}=[1-(1-q)^{3}]\\cdot p^{3}$，再作差因式分解即可判断；（ii）首先得到 $X$ 和 $Y$ 的所有可能取值，再按步骤列出分布列，计算出各自期望，再次作差比较大小即可.\n【小问1详解】\n甲、乙所在队的比赛成绩不少于 5 分，则甲第一阶段至少投中 1 次，乙第二阶段也至少投中 1 次，\n$\\therefore$ 比赛成绩不少于 5 分的概率 $P=(1-0.6^{3})(1-0.5^{3})=0.686$.\n【小问2详解】\n（i）若甲先参加第一阶段比赛，则甲、乙所在队的比赛成绩为 15 分的概率为 $P_{\\text{甲}}=[1-(1-p)^{3}]q^{3}$，\n若乙先参加第一阶段比赛，则甲、乙所在队的比赛成绩为 15 分的概率为 $P_{\\text{乙}}=[1-(1-q)^{3}]\\cdot p^{3}$，\n$\\because 0<p<q$，\n$\\therefore P_{\\text{甲}}-P_{\\text{乙}}=q^{3}-(q-pq)^{3}-p^{3}+(p-pq)^{3}$\n$=(q-p)(q^{2}+pq+p^{2})+(p-q)\\cdot[(p-pq)^{2}+(q-pq)^{2}+(p-pq)(q-pq)]$\n$=(p-q)(3p^{2}q^{2}-3p^{2}q-3pq^{2})$\n$=3pq(p-q)(pq-p-q)=3pq(p-q)[(1-p)(1-q)-1]>0$，\n$\\therefore P_{\\text{甲}}>P_{\\text{乙}}$，应该由甲参加第一阶段比赛.\n（ii）若甲先参加第一阶段比赛，数学成绩 $X$ 的所有可能取值为 0，5，10，15，\n$P(X=0)=(1-p)^{3}+[1-(1-p)^{3}]\\cdot(1-q)^{3}$，\n$P(X=5)=[1-(1-p)^{3}]\\mathrm{C}_{3}^{1}q\\cdot(1-q)^{2}$，\n$P(X=10)=[1-(1-p)^{3}]\\cdot\\mathrm{C}_{3}^{2}q^{2}(1-q)$，\n$P(X=15)=[1-(1-p)^{3}]\\cdot q^{3}$，\n$\\therefore E(X)=15[1-(1-p)^{3}]q=15(p^{3}-3p^{2}+3p)\\cdot q$\n记乙先参加第一阶段比赛，数学成绩 $Y$ 的所有可能取值为 0，5，10，15，\n同理 $E(Y)=15(q^{3}-3q^{2}+3q)\\cdot p$\n$\\therefore E(X)-E(Y)=15[pq(p+q)(p-q)-3pq(p-q)]$\n$=15(p-q)pq(p+q-3)$，\n因为 $0<p<q$，则 $p-q<0$，$p+q-3<1+1-3<0$，\n则 $(p-q)pq(p+q-3)>0$，\n$\\therefore$ 应该由甲参加第一阶段比赛.\n【点睛】关键点点睛：本题第二问的关键是计算出相关概率和期望，采用作差法并因式分解从而比较出大小关系，最后得到结论."
})

questions.append({
    "type": "解答题",
    "difficulty": "困难",
    "source": source,
    "tags": "2024新课标Ⅱ卷,number:19",
    "topicId": "M3-C3-T2",
    "content": "已知双曲线 $C: x^{2}-y^{2}=m\\ (m>0)$，点 $P_{1}(5,4)$ 在 $C$ 上，$k$ 为常数，$0<k<1$. 按照如下方式依次构造点 $P_{n}\\ (n=2,3,\\ldots)$，过 $P_{n-1}$ 作斜率为 $k$ 的直线与 $C$ 的左支交于点 $Q_{n-1}$，令 $P_{n}$ 为 $Q_{n-1}$ 关于 $y$ 轴的对称点，记 $P_{n}$ 的坐标为 $(x_{n},y_{n})$.\n（1）若 $k=\\frac{1}{2}$，求 $x_{2},y_{2}$；\n（2）证明：数列 $\\{x_{n}-y_{n}\\}$ 是公比为 $\\frac{1+k}{1-k}$ 的等比数列；\n（3）设 $S_{n}$ 为 $\\triangle P_{n}P_{n+1}P_{n+2}$ 的面积，证明：对任意的正整数 $n$，$S_{n}=S_{n+1}$.",
    "options": "",
    "answer": "（1）$x_{2}=3$，$y_{2}=0$\n（2）证明见解析\n（3）证明见解析",
    "solution": "【分析】（1）直接根据题目中的构造方式计算出 $P_{2}$ 的坐标即可；\n（2）根据等比数列的定义即可验证结论；\n（3）思路一：使用平面向量数量积和等比数列工具，证明 $S_{n}$ 的取值为与 $n$ 无关的定值即可.思路二：使用等差数列工具，证明 $S_{n}$ 的取值为与 $n$ 无关的定值即可.\n【小问1详解】\n由已知有 $m=5^{2}-4^{2}=9$，故 $C$ 的方程为 $x^{2}-y^{2}=9$.\n当 $k=\\frac{1}{2}$ 时，过 $P_{1}(5,4)$ 且斜率为 $\\frac{1}{2}$ 的直线为 $y=\\frac{x+3}{2}$，与 $x^{2}-y^{2}=9$ 联立得到 $x^{2}-\\left(\\frac{x+3}{2}\\right)^{2}=9$.\n解得 $x=-3$ 或 $x=5$，所以该直线与 $C$ 的不同于 $P_{1}$ 的交点为 $Q_{1}(-3,0)$，该点显然在 $C$ 的左支上.\n故 $P_{2}(3,0)$，从而 $x_{2}=3$，$y_{2}=0$.\n【小问2详解】\n由于过 $P_{n}(x_{n},y_{n})$ 且斜率为 $k$ 的直线为 $y=k(x-x_{n})+y_{n}$，与 $x^{2}-y^{2}=9$ 联立，得到方程\n$x^{2}-\\left(k(x-x_{n})+y_{n}\\right)^{2}=9$.\n展开即得 $(1-k^{2})x^{2}-2k(y_{n}-kx_{n})x-(y_{n}-kx_{n})^{2}-9=0$，由于 $P_{n}(x_{n},y_{n})$ 已经是直线 $y=k(x-x_{n})+y_{n}$ 和 $x^{2}-y^{2}=9$ 的公共点，故方程必有一根 $x=x_{n}$.\n从而根据韦达定理，另一根 $x=\\frac{2k(y_{n}-kx_{n})}{1-k^{2}}-x_{n}=\\frac{2ky_{n}-x_{n}-k^{2}x_{n}}{1-k^{2}}$，相应的\n$y=k(x-x_{n})+y_{n}=\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}$.\n所以该直线与 $C$ 的不同于 $P_{n}$ 的交点为 $Q_{n}\\left(\\frac{2ky_{n}-x_{n}-k^{2}x_{n}}{1-k^{2}},\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}\\right)$，而注意到 $Q_{n}$ 的横坐标亦可通过韦达定理表示为 $\\frac{-(y_{n}-kx_{n})^{2}-9}{(1-k^{2})x_{n}}$，故 $Q_{n}$ 一定在 $C$ 的左支上.\n所以 $P_{n+1}\\left(\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}},\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}\\right)$.\n这就得到 $x_{n+1}=\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}}$，$y_{n+1}=\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}$.\n所以 $x_{n+1}-y_{n+1}=\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}}-\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}$\n$=\\frac{x_{n}+k^{2}x_{n}+2kx_{n}}{1-k^{2}}-\\frac{y_{n}+k^{2}y_{n}+2ky_{n}}{1-k^{2}}=\\frac{1+k^{2}+2k}{1-k^{2}}(x_{n}-y_{n})=\\frac{1+k}{1-k}(x_{n}-y_{n})$.\n再由 $x_{1}^{2}-y_{1}^{2}=9$，就知道 $x_{1}-y_{1}\\neq0$，所以数列 $\\{x_{n}-y_{n}\\}$ 是公比为 $\\frac{1+k}{1-k}$ 的等比数列.\n【小问3详解】\n方法一：先证明一个结论：对平面上三个点 $U,V,W$，若 $\\overrightarrow{UV}=(a,b)$，$\\overrightarrow{UW}=(c,d)$，则 $S_{\\triangle UVW}=\\frac{1}{2}|ad-bc|$.（若 $U,V,W$ 在同一条直线上，约定 $S_{\\triangle UVW}=0$）\n证明：$S_{\\triangle UVW}=\\frac{1}{2}|\\overrightarrow{UV}|\\cdot|\\overrightarrow{UW}|\\sin\\langle\\overrightarrow{UV},\\overrightarrow{UW}\\rangle=\\frac{1}{2}|\\overrightarrow{UV}|\\cdot|\\overrightarrow{UW}|\\sqrt{1-\\cos^{2}\\langle\\overrightarrow{UV},\\overrightarrow{UW}\\rangle}$\n$=\\frac{1}{2}|\\overrightarrow{UV}|\\cdot|\\overrightarrow{UW}|\\sqrt{1-\\left(\\frac{\\overrightarrow{UV}\\cdot\\overrightarrow{UW}}{|\\overrightarrow{UV}|\\cdot|\\overrightarrow{UW}|}\\right)^{2}}=\\frac{1}{2}\\sqrt{|\\overrightarrow{UV}|^{2}\\cdot|\\overrightarrow{UW}|^{2}-(\\overrightarrow{UV}\\cdot\\overrightarrow{UW})^{2}}$\n$=\\frac{1}{2}\\sqrt{(a^{2}+b^{2})(c^{2}+d^{2})-(ac+bd)^{2}}$\n$=\\frac{1}{2}\\sqrt{a^{2}c^{2}+a^{2}d^{2}+b^{2}c^{2}+b^{2}d^{2}-a^{2}c^{2}-b^{2}d^{2}-2abcd}$\n$=\\frac{1}{2}\\sqrt{a^{2}d^{2}+b^{2}c^{2}-2abcd}=\\frac{1}{2}\\sqrt{(ad-bc)^{2}}=\\frac{1}{2}|ad-bc|$.\n证毕，回到原题.\n由于上一小问已经得到 $x_{n+1}=\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}}$，$y_{n+1}=\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}$，\n故 $x_{n+1}+y_{n+1}=\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}}+\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}=\\frac{1+k^{2}-2k}{1-k^{2}}(x_{n}+y_{n})=\\frac{1-k}{1+k}(x_{n}+y_{n})$.\n再由 $x_{1}^{2}-y_{1}^{2}=9$，就知道 $x_{1}+y_{1}\\neq0$，所以数列 $\\{x_{n}+y_{n}\\}$ 是公比为 $\\frac{1-k}{1+k}$ 的等比数列.\n所以对任意的正整数 $m$，都有\n$x_{n}y_{n+m}-y_{n}x_{n+m}$\n$=\\frac{1}{2}\\left((x_{n}x_{n+m}-y_{n}y_{n+m})+(x_{n}y_{n+m}-y_{n}x_{n+m})\\right)-\\frac{1}{2}\\left((x_{n}x_{n+m}-y_{n}y_{n+m})-(x_{n}y_{n+m}-y_{n}x_{n+m})\\right)$\n$=\\frac{1}{2}(x_{n}-y_{n})(x_{n+m}+y_{n+m})-\\frac{1}{2}(x_{n}+y_{n})(x_{n+m}-y_{n+m})$\n$=\\frac{1}{2}\\left(\\frac{1-k}{1+k}\\right)^{m}(x_{n}-y_{n})(x_{n}+y_{n})-\\frac{1}{2}\\left(\\frac{1+k}{1-k}\\right)^{m}(x_{n}+y_{n})(x_{n}-y_{n})$\n$=\\frac{1}{2}\\left(\\left(\\frac{1-k}{1+k}\\right)^{m}-\\left(\\frac{1+k}{1-k}\\right)^{m}\\right)(x_{n}^{2}-y_{n}^{2})$\n$=\\frac{9}{2}\\left(\\left(\\frac{1-k}{1+k}\\right)^{m}-\\left(\\frac{1+k}{1-k}\\right)^{m}\\right)$.\n而又有 $\\overrightarrow{P_{n+1}P_{n}}=(-(x_{n+1}-x_{n}),-(y_{n+1}-y_{n}))$，$\\overrightarrow{P_{n+1}P_{n+2}}=(x_{n+2}-x_{n+1},y_{n+2}-y_{n+1})$，\n故利用前面已经证明的结论即得\n$S_{n}=S_{\\triangle P_{n}P_{n+1}P_{n+2}}=\\frac{1}{2}\\left|-(x_{n+1}-x_{n})(y_{n+2}-y_{n+1})+(y_{n+1}-y_{n})(x_{n+2}-x_{n+1})\\right|$\n$=\\frac{1}{2}\\left|(x_{n+1}-x_{n})(y_{n+2}-y_{n+1})-(y_{n+1}-y_{n})(x_{n+2}-x_{n+1})\\right|$\n$=\\frac{1}{2}\\left|(x_{n+1}y_{n+2}-y_{n+1}x_{n+2})+(x_{n}y_{n+1}-y_{n}x_{n+1})-(x_{n}y_{n+2}-y_{n}x_{n+2})\\right|$\n$=\\frac{1}{2}\\left|\\frac{9}{2}\\left(\\frac{1-k}{1+k}-\\frac{1+k}{1-k}\\right)+\\frac{9}{2}\\left(\\frac{1-k}{1+k}-\\frac{1+k}{1-k}\\right)-\\frac{9}{2}\\left(\\left(\\frac{1-k}{1+k}\\right)^{2}-\\left(\\frac{1+k}{1-k}\\right)^{2}\\right)\\right|$.\n这就表明 $S_{n}$ 的取值是与 $n$ 无关的定值，所以 $S_{n}=S_{n+1}$.\n方法二：由于上一小问已经得到 $x_{n+1}=\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}}$，$y_{n+1}=\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}$，\n故 $x_{n+1}+y_{n+1}=\\frac{x_{n}+k^{2}x_{n}-2ky_{n}}{1-k^{2}}+\\frac{y_{n}+k^{2}y_{n}-2kx_{n}}{1-k^{2}}=\\frac{1+k^{2}-2k}{1-k^{2}}(x_{n}+y_{n})=\\frac{1-k}{1+k}(x_{n}+y_{n})$.\n再由 $x_{1}^{2}-y_{1}^{2}=9$，就知道 $x_{1}+y_{1}\\neq0$，所以数列 $\\{x_{n}+y_{n}\\}$ 是公比为 $\\frac{1-k}{1+k}$ 的等比数列.\n所以对任意的正整数 $m$，都有\n$x_{n}y_{n+m}-y_{n}x_{n+m}$\n$=\\frac{1}{2}\\left((x_{n}x_{n+m}-y_{n}y_{n+m})+(x_{n}y_{n+m}-y_{n}x_{n+m})\\right)-\\frac{1}{2}\\left((x_{n}x_{n+m}-y_{n}y_{n+m})-(x_{n}y_{n+m}-y_{n}x_{n+m})\\right)$\n$=\\frac{1}{2}(x_{n}-y_{n})(x_{n+m}+y_{n+m})-\\frac{1}{2}(x_{n}+y_{n})(x_{n+m}-y_{n+m})$\n$=\\frac{1}{2}\\left(\\frac{1-k}{1+k}\\right)^{m}(x_{n}-y_{n})(x_{n}+y_{n})-\\frac{1}{2}\\left(\\frac{1+k}{1-k}\\right)^{m}(x_{n}+y_{n})(x_{n}-y_{n})$\n$=\\frac{1}{2}\\left(\\left(\\frac{1-k}{1+k}\\right)^{m}-\\left(\\frac{1+k}{1-k}\\right)^{m}\\right)(x_{n}^{2}-y_{n}^{2})$\n$=\\frac{9}{2}\\left(\\left(\\frac{1-k}{1+k}\\right)^{m}-\\left(\\frac{1+k}{1-k}\\right)^{m}\\right)$.\n这就得到 $x_{n+2}y_{n+3}-y_{n+2}x_{n+3}=\\frac{9}{2}\\left(\\frac{1-k}{1+k}-\\frac{1+k}{1-k}\\right)=x_{n}y_{n+1}-y_{n}x_{n+1}$，\n以及 $x_{n+1}y_{n+3}-y_{n+1}x_{n+3}=\\frac{9}{2}\\left(\\left(\\frac{1-k}{1+k}\\right)^{2}-\\left(\\frac{1+k}{1-k}\\right)^{2}\\right)=x_{n}y_{n+2}-y_{n}x_{n+2}$.\n两式相减，即得 $(x_{n+2}y_{n+3}-y_{n+2}x_{n+3})-(x_{n+1}y_{n+3}-y_{n+1}x_{n+3})=(x_{n}y_{n+1}-y_{n}x_{n+1})-(x_{n}y_{n+2}-y_{n}x_{n+2})$.\n移项得到 $x_{n+2}y_{n+3}-y_{n}x_{n+2}-x_{n+1}y_{n+3}+y_{n}x_{n+1}=y_{n+2}x_{n+3}-x_{n}y_{n+2}-y_{n+1}x_{n+3}+x_{n}y_{n+1}$.\n故 $(y_{n+3}-y_{n})(x_{n+2}-x_{n+1})=(y_{n+2}-y_{n+1})(x_{n+3}-x_{n})$.\n而 $\\overrightarrow{P_{n}P_{n+3}}=(x_{n+3}-x_{n},y_{n+3}-y_{n})$，$\\overrightarrow{P_{n+1}P_{n+2}}=(x_{n+2}-x_{n+1},y_{n+2}-y_{n+1})$.\n所以 $\\overrightarrow{P_{n}P_{n+3}}$ 和 $\\overrightarrow{P_{n+1}P_{n+2}}$ 平行，这就得到 $S_{\\triangle P_{n}P_{n+1}P_{n+2}}=S_{\\triangle P_{n+1}P_{n+2}P_{n+3}}$，即 $S_{n}=S_{n+1}$.\n【点睛】关键点点睛：本题的关键在于将解析几何和数列知识的结合，需要综合运用多方面知识方可得解."
})

# ============ 执行导入 ============
print(f"总共准备 {len(questions)} 道题的数据")

# 1. 删除旧数据
print("\n=== 第1步：删除旧数据 ===")
old_ids = [3435, 3436, 3437, 3438, 3439, 3440, 3441, 3442, 3443, 3444, 3445, 3446, 3447, 3448, 3449, 3450, 3451, 3452, 3453, 3454]
success_del = 0
for rid in old_ids:
    ok = delete_record(rid)
    if ok:
        success_del += 1
        print(f'  ✅ 删除 id={rid}', flush=True)
    else:
        print(f'  ❌ 删除 id={rid} 失败', flush=True)
    time.sleep(0.5)
print(f"删除完成：{success_del}/{len(old_ids)}")

# 2. 插入新数据
print("\n=== 第2步：插入新数据 ===")
success_ins = 0
for i, q in enumerate(questions, 1):
    result = baas_call(q)
    if '"code":"0"' in result:
        success_ins += 1
        print(f'  ✅ 题{q["tags"].split(",")[-1]} 插入成功', flush=True)
    else:
        print(f'  ❌ 题{q["tags"]}: {result[:200]}', flush=True)
    time.sleep(0.5)

print(f"\n✅ 全部完成：插入 {success_ins}/{len(questions)} 题")
