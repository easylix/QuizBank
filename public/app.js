/* ===== 高中数学题库 - 应用逻辑 (云端版) ===== */

// ---- 云端数据库配置 ----
const BAAS_CONFIG = {
  baseUrl: 'https://baas.kuafuai.net/baas-api',
  apiKey: 'baas_ZiRfZlhr'
};

const APP_VERSION = 'v23b';

let client = null;
let questions = [];
let currentTopicId = null;
let showAnswerCache = {};
let currentPage = 1;
let pageSize = 30;
let showAllAnswers = false;

// ---- 初始化 ----
(async function init() {
  // 1. 初始化云端数据库客户端
  client = aipexbase.createClient({
    baseUrl: BAAS_CONFIG.baseUrl,
    apiKey: BAAS_CONFIG.apiKey
  });

  // 2. 加载知识点树
  const res = await fetch('data/knowledge-tree.json');
  window.KNOWLEDGE_TREE = await res.json();
  renderTree();

  // 3. 从云端加载题目
  // 显示版本号
  const verEl = document.querySelector('.ver-badge');
  if (verEl) verEl.textContent = APP_VERSION;

  await loadQuestionsFromCloud();
  renderList();

  // 4. 绑定事件
  bindUI();
})();

// ---- 云端数据操作 ----

function fixLatexUnderscore(str) {
  // 将 \_\_\_... 替换为 $\\underline{\\hspace{...}}$，让renderMath识别并交给KaTeX渲染
  if (!str) return '';
  return str
    .replace(/\\_(\\_)+/g, '$\\underline{\\hspace{8em}}$')
    .replace(/\\_/g, '$\\underline{\\hspace{2em}}$');
}

async function loadQuestionsFromCloud() {
  try {
    const res = await client.db.from('questions_v2').list().order('createdAt', 'desc');
    if (res.success && res.data) {
      const seen = new Set();
      questions = (res.data || []).filter(q => {
        const key = (q.content || '').replace(/\s+/g, '');
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
      }).map(q => {
        // 从 tags 字段解析题号 (number:XX) 和图片 (image:path)
        let num = '';
        let img = '';
        if (q.tags) {
          const nm = q.tags.match(/number:(\d+)/);
          if (nm) num = nm[1];
          const im = q.tags.match(/image:([^,]+)/);
          if (im) img = im[1];
        }
        return {
          id: q.id,
          topicId: q.topicId || '',
          type: q.type || '单选题',
          difficulty: q.difficulty || '中等',
          content: fixLatexUnderscore(q.content || ''),
          options: q.options || '',
          answer: q.answer || '',
          solution: fixLatexUnderscore(q.solution || ''),
          source: q.source || '',
          tags: q.tags || '',
          // 优先使用数据库中的 image/answerImage 字段，回退到 tags 中的旧引用
          image: q.image || img,
          answerImage: q.answerImage || '',
          number: num,
          createdAt: q.createdAt ? new Date(q.createdAt).getTime() : Date.now()
        };
      });
    } else {
      questions = [];
    }
  } catch (e) {
    console.error('加载云端数据失败:', e);
    questions = [];
    showToast('加载题库失败，请刷新重试', 'error');
  }
  updateStats();
  renderTree();
}

async function saveNumberToTag(id, number) {
  try {
    const listRes = await client.db.from('questions_v2').list().eq('id', id);
    if (!listRes.success || !listRes.data || listRes.data.length === 0) return;
    const q = listRes.data[0];
    let newTags = (q.tags || '').replace(/,?number:\d+/g, '');
    if (number) {
      newTags = newTags ? newTags + ',number:' + number : 'number:' + number;
    }
    await client.db.from('questions_v2').update().set({tags: newTags}).eq('id', id);
  } catch(e) {
    console.error('题号保存失败:', e);
  }
}

async function removeNumberFromTag(id) {
  await saveNumberToTag(id, '');
}

async function saveAddQuestion(data) {
  try {
    const now = new Date().toISOString().slice(0, 19).replace('T', ' ');
    const res = await client.db.from('questions_v2').insert().values({
      topicId: data.topicId,
      type: data.type,
      difficulty: data.difficulty,
      content: data.content,
      options: data.options || '',
      answer: data.answer,
      solution: data.solution || '',
      source: data.source || '',
      tags: data.tags || '',
      createdAt: now
    });
    if (res.success) {
      await loadQuestionsFromCloud();
      if (data.number && res.data && res.data.id) {
        await saveNumberToTag(res.data.id, data.number);
      }
      renderList();
      renderTree();
      return true;
    } else {
      alert('保存失败：' + (res.message || '未知错误'));
      return false;
    }
  } catch (e) {
    alert('保存失败：' + e.message);
    return false;
  }
}

async function saveUpdateQuestion(id, data) {
  try {
    const res = await client.db.from('questions_v2').update().set({
      topicId: data.topicId,
      type: data.type,
      difficulty: data.difficulty,
      content: data.content,
      options: data.options || '',
      answer: data.answer,
      solution: data.solution || '',
      source: data.source || '',
      tags: data.tags || '',
    }).eq('id', id);
    if (res.success) {
      await saveNumberToTag(id, data.number || '');
      await loadQuestionsFromCloud();
      renderList();
      renderTree();
      return true;
    } else {
      alert('更新失败：' + (res.message || '未知错误'));
      return false;
    }
  } catch (e) {
    alert('更新失败：' + e.message);
    return false;
  }
}

async function saveDeleteQuestion(id) {
  try {
    const res = await client.db.from('questions_v2').delete().eq('id', id);
    if (res.success) {
      await removeNumberFromTag(id);
      await loadQuestionsFromCloud();
      renderList();
      renderTree();
      return true;
    } else {
      alert('删除失败：' + (res.message || '未知错误'));
      return false;
    }
  } catch (e) {
    alert('删除失败：' + e.message);
    return false;
  }
}

function updateStats() {
  document.getElementById('totalStats').textContent = `${questions.length} 题`;
}

// ---- 知识点树渲染（与原来一致）----
function renderTree() {
  const container = document.getElementById('treeContainer');
  const tree = KNOWLEDGE_TREE;
  let html = '';
  tree.modules.forEach(mod => {
    var modSelected = currentTopicId === mod.id || mod.chapters.some(function(ch) { return ch.id === currentTopicId || ch.topics.some(function(t) { return t.id === currentTopicId; }); });
    html += '<div class="tree-module open" data-id="' + mod.id + '">';
    html += '  <div class="tree-module-header' + (modSelected ? ' selected' : '') + '">';
    html += '    <span class="arrow open" onclick="event.stopPropagation();toggleModule(\'' + mod.id + '\')">▶</span>';
    html += '    <span class="tree-label" onclick="selectModule(\'' + mod.id + '\')">' + mod.name + '</span>';
    html += '    <span class="count">(' + qCount(mod.id) + ')</span>';
    html += '  </div>';
    html += '  <div class="tree-chapter">';
    mod.chapters.forEach(function(ch) {
      var chSelected = currentTopicId === ch.id || ch.topics.some(function(t) { return t.id === currentTopicId; });
      html += '  <div class="tree-chapter open" data-id="' + ch.id + '">';
      html += '    <div class="tree-chapter-header' + (chSelected ? ' selected' : '') + '">';
      html += '      <span class="arrow open" onclick="event.stopPropagation();toggleChapter(\'' + ch.id + '\')">▶</span>';
      html += '      <span class="tree-label" onclick="selectChapter(\'' + ch.id + '\')">' + ch.name + '</span>';
      html += '      <span class="count">(' + qCount(ch.id) + ')</span>';
      html += '    </div>';
      html += '    <div class="tree-topics">';
      ch.topics.forEach(function(t) {
        html += '      <div class="tree-topic' + (currentTopicId === t.id ? ' active' : '') + '" data-id="' + t.id + '" onclick="selectTopic(\'' + t.id + '\')">' + t.name + '<span class="count">' + qCount(t.id) + '</span></div>';
      });
      html += '    </div>';
      html += '  </div>';
    });
    html += '</div></div>';
  });
  container.innerHTML = html;
}

function toggleModule(id) {
  const el = document.querySelector(`.tree-module[data-id="${id}"]`);
  el.classList.toggle('open');
  el.querySelector('.tree-module-header .arrow')?.classList.toggle('open');
}

function toggleChapter(id) {
  const el = document.querySelector(`.tree-chapter[data-id="${id}"]`);
  el.classList.toggle('open');
  el.querySelector('.tree-chapter-header .arrow')?.classList.toggle('open');
}

function selectModule(id) {
  if (currentTopicId === id) { currentTopicId = null; renderTree(); renderList(); return; }
  currentTopicId = id;
  renderTree();
  renderList();
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }
}

function selectChapter(id) {
  if (currentTopicId === id) { currentTopicId = null; renderTree(); renderList(); return; }
  currentTopicId = id;
  renderTree();
  renderList();
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }
}

function selectTopic(id) {
  if (currentTopicId === id) { currentTopicId = null; renderTree(); renderList(); return; }
  currentTopicId = id;
  document.querySelectorAll('.tree-topic').forEach(el => el.classList.remove('active'));
  const el = document.querySelector(`.tree-topic[data-id="${id}"]`);
  if (el) {
    el.classList.add('active');
    el.closest('.tree-chapter')?.classList.add('open');
    el.closest('.tree-module')?.classList.add('open');
  }
  renderTree();
  renderList();
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }
}

function qCount(nodeId) {
  return questions.filter(q => {
    const ids = (q.topicId || '').split(',').filter(Boolean);
    if (ids.includes(nodeId)) return true;
    for (const mod of KNOWLEDGE_TREE.modules) {
      for (const ch of mod.chapters) {
        if (ch.id === nodeId) {
          if (ch.topics.some(t => ids.includes(t.id))) return true;
        }
      }
      if (mod.id === nodeId) {
        for (const ch of mod.chapters) {
          if (ch.topics.some(t => ids.includes(t.id))) return true;
        }
      }
    }
    return false;
  }).length;
}

function getChapterNames(id) {
  const ids = (id || '').split(',').filter(Boolean);
  const chapters = [];
  const topics = [];
  for (const mod of KNOWLEDGE_TREE.modules) {
    for (const ch of mod.chapters) {
      if (ids.includes(ch.id)) {
        chapters.push(ch.name);
      }
      for (const t of ch.topics) {
        if (ids.includes(t.id)) {
          topics.push(t.name);
          if (!chapters.includes(ch.name)) chapters.push(ch.name);
        }
      }
    }
  }
  return { module: '', chapter: chapters.join('、') || '', topic: topics.join('、') };
}

// ---- 渲染题目列表 ----
function renderList() {
  const list = document.getElementById('questionList');
  const resultCount = document.getElementById('resultCount');

  let filtered = [...questions];

  if (currentTopicId) {
    filtered = filtered.filter(q => {
      const ids = (q.topicId || '').split(',').filter(Boolean);
      if (ids.includes(currentTopicId)) return true;
      for (const mod of KNOWLEDGE_TREE.modules) {
        for (const ch of mod.chapters) {
          if (ch.id === currentTopicId) {
            return ids.some(id => ch.topics.some(t => t.id === id));
          }
          if (mod.id === currentTopicId) {
            // 模块级：检查该模块所有章节的所有知识点
            if (ids.some(id => ch.topics.some(t => t.id === id))) {
              return true;
            }
          }
        }
        // 模块级：所有章节检查完无一匹配
        if (mod.id === currentTopicId) {
          return false;
        }
      }
      return false;
    });
  }

  const diffVal = document.getElementById('filterDifficulty').value;
  if (diffVal) filtered = filtered.filter(q => q.difficulty === diffVal);

  const typeVal = document.getElementById('filterType').value;
  if (typeVal) filtered = filtered.filter(q => q.type === typeVal);

  const sourceVal = document.getElementById('filterSource').value;
  if (sourceVal) {
    filtered = filtered.filter(q => q.source && q.source.split(',').map(s => s.trim()).includes(sourceVal));
  }

  const searchVal = document.getElementById('searchInput').value.trim().toLowerCase();
  if (searchVal) {
    filtered = filtered.filter(q =>
      q.content.toLowerCase().includes(searchVal) ||
      (q.tags && q.tags.toLowerCase().includes(searchVal)) ||
      (q.solution && q.solution.toLowerCase().includes(searchVal))
    );
  }

  resultCount.textContent = `共 ${filtered.length} 题`;

  if (filtered.length === 0) {
    list.innerHTML = `<div class="empty-state">
      <div class="empty-icon">🔍</div>
      <h3>没有找到题目</h3>
      <p>试试其他筛选条件，或者点击右上角「加题」添加新题目</p>
    </div>`;
    return;
  }

  // 按题号排序（保持真题原卷顺序）
  filtered.sort((a, b) => (parseInt(a.number) || 999) - (parseInt(b.number) || 999));

  // 分页
  const totalPages = Math.ceil(filtered.length / pageSize) || 1;
  if (currentPage > totalPages) currentPage = totalPages;
  const start = (currentPage - 1) * pageSize;
  const pageItems = filtered.slice(start, start + pageSize);

  let html = '';
  pageItems.forEach(q => {
    const info = getChapterNames(q.topicId);
    const diffClass = q.difficulty === '基础' ? 'q-badge-difficulty-easy' : q.difficulty === '中等' ? 'q-badge-difficulty-mid' : 'q-badge-difficulty-hard';

    // 选择题/多选题：生成选项HTML（在卡片中显示，LaTeX公式用renderMath渲染）
    let optionsHtml = '';
    if (q.options && !q.type.includes('填空') && !q.type.includes('解答')) {
      const opts = q.options.split('\n').filter(Boolean);
      optionsHtml = '<div class="q-card-options">';
      opts.forEach(o => {
        optionsHtml += `<div class="q-card-option">${replaceFigMarkers(renderMath(o), q)}</div>`;
      });
      optionsHtml += '</div>';
    }

    // 答案区域（默认隐藏，点击显示答案+解析）
    const showAnswer = showAnswerCache[q.id] === undefined ? showAllAnswers : showAnswerCache[q.id];
    const answerSection = showAnswer
      ? `<div class="q-card-answer-show">
          <div class="q-answer-line"><span class="q-label">✅ 答案：</span>${replaceFigMarkers(renderMath(q.answer), q)}</div>
          ${q.solution ? `<div class="q-solution-line"><span class="q-label">📖 解析：</span>${replaceFigMarkers(renderMath(q.solution), q)}</div>` : ''}
          <div class="answer-toggle-btm" onclick="event.stopPropagation();toggleAnswer('${q.id}')">🙈 隐藏答案</div>
         </div>`
      : `<span class="hidden-answer" onclick="event.stopPropagation();toggleAnswer('${q.id}')">👁 显示答案</span>`;

    html += `<div class="q-card" onclick="showDetail('${q.id}')">
      <div class="q-card-header">
        <span class="q-badge q-badge-topic">${info.chapter}</span>
        <span class="q-badge q-badge-type">${q.type}</span>
        <span class="q-badge ${diffClass}">${q.difficulty}</span>
        ${q.source ? `<span class="q-badge q-badge-source">📖 ${q.source}</span>` : ''}
        ${q.number ? `<span class="q-badge q-badge-number">#${q.number}</span>` : ''}
      </div>
      <div class="q-card-content">${q.number ? `<span class="qn">${q.number}.</span> ` : ''}${replaceFigMarkers(renderMath(q.content), q)}</div>
      ${optionsHtml}
      <div class="q-card-answer" onclick="event.stopPropagation()">${answerSection}</div>
    </div>`;
  });
  // 分页控件
  html += `<div class="pagination">
    <div class="page-size-select">
      <label>每页</label>
      <select onchange="changePageSize(this.value)">
        <option value="10"${pageSize===10?' selected':''}>10</option>
        <option value="20"${pageSize===20?' selected':''}>20</option>
        <option value="30"${pageSize===30?' selected':''}>30</option>
        <option value="50"${pageSize===50?' selected':''}>50</option>
      </select>
      <label>题</label>
    </div>
    <div class="page-nav">
      <button class="btn btn-xs" onclick="goPage(${currentPage - 1})"${currentPage <= 1 ? ' disabled' : ''}>←</button>
      <span class="page-info">第 ${currentPage} / ${totalPages} 页</span>
      <button class="btn btn-xs" onclick="goPage(${currentPage + 1})"${currentPage >= totalPages ? ' disabled' : ''}>→</button>
    </div>
  </div>`;

  list.innerHTML = html;
  renderMathInElement(list);
}

function resetFilter() {
  currentTopicId = null;
  currentPage = 1;
  renderTree();
  renderList();
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('open');
  }
}

function toggleAnswer(id) {
  const current = showAnswerCache[id] === undefined ? showAllAnswers : showAnswerCache[id];
  if (current) {
    // 当前显 → 隐
    showAnswerCache[id] = false;
  } else {
    // 当前隐 → 显
    if (showAllAnswers) {
      // 全局已显示，删除缓存恢复跟随全局
      delete showAnswerCache[id];
    } else {
      showAnswerCache[id] = true;
    }
  }
  renderList();
}

function changePageSize(size) {
  pageSize = parseInt(size);
  currentPage = 1;
  renderList();
}

function goPage(page) {
  if (page < 1) return;
  const totalPages = Math.ceil(getFilteredQuestions().length / pageSize) || 1;
  if (page > totalPages) return;
  currentPage = page;
  renderList();
}

function getFilteredQuestions() {
  let filtered = [...questions];
  if (currentTopicId) {
    filtered = filtered.filter(q => {
      const ids = (q.topicId || '').split(',').filter(Boolean);
      if (ids.includes(currentTopicId)) return true;
      for (const mod of KNOWLEDGE_TREE.modules) {
        for (const ch of mod.chapters) {
          if (ch.id === currentTopicId) return ids.some(id => ch.topics.some(t => t.id === id));
          if (mod.id === currentTopicId) {
            if (ids.some(id => ch.topics.some(t => t.id === id))) return true;
          }
        }
        if (mod.id === currentTopicId) return false;
      }
      return false;
    });
  }
  const diffVal = document.getElementById('filterDifficulty').value;
  if (diffVal) filtered = filtered.filter(q => q.difficulty === diffVal);
  const typeVal = document.getElementById('filterType').value;
  if (typeVal) filtered = filtered.filter(q => q.type === typeVal);
  const sourceVal = document.getElementById('filterSource').value;
  if (sourceVal) {
    filtered = filtered.filter(q => q.source && q.source.split(',').map(s => s.trim()).includes(sourceVal));
  }
  const searchVal = document.getElementById('searchInput').value.trim().toLowerCase();
  if (searchVal) {
    filtered = filtered.filter(q =>
      q.content.toLowerCase().includes(searchVal) ||
      (q.tags && q.tags.toLowerCase().includes(searchVal)) ||
      (q.solution && q.solution.toLowerCase().includes(searchVal))
    );
  }
  filtered.sort((a, b) => (parseInt(a.number) || 999) - (parseInt(b.number) || 999));
  return filtered;
}



// ---- 详情弹窗 ----
function showDetail(id) {
  const q = questions.find(x => x.id == id);
  if (!q) return;
  const info = getChapterNames(q.topicId);
  const diffClass = q.difficulty === '基础' ? 'q-badge-difficulty-easy' : q.difficulty === '中等' ? 'q-badge-difficulty-mid' : 'q-badge-difficulty-hard';
  let optionsHtml = '';
  if (q.options && !q.type.includes('填空')) {
    const opts = q.options.split('\n').filter(Boolean);
    const correct = q.answer.trim().toUpperCase().split(',').map(x => x.trim());
    optionsHtml = '<ul class="detail-options">';
    opts.forEach(o => {
      const letter = o.charAt(0).toUpperCase();
      const isCorrect = correct.includes(letter);
      optionsHtml += `<li class="${isCorrect ? 'correct' : ''}">${isCorrect ? '✅ ' : ''}${replaceFigMarkers(renderMath(o), q)}</li>`;
    });
    optionsHtml += '</ul>';
  }

  document.getElementById('detailContent').innerHTML = `
    <div class="detail-section">
      <h4>题目信息</h4>
      <div class="detail-body">
        <span class="q-badge q-badge-topic">${info.module} / ${info.chapter}</span>
        <span class="q-badge q-badge-type">${q.type}</span>
        <span class="q-badge ${diffClass}">${q.difficulty}</span>
        ${q.source ? `<span class="q-badge q-badge-topic" style="background:#fef3c7;color:#b45309;">📖 ${q.source}</span>` : ''}
        ${q.number ? `<span class="q-badge q-badge-number">#${q.number}</span>` : ''}
      </div>
    </div>
    <div class="detail-section">
      <h4>题目</h4>
      <div class="detail-body">${q.number ? `<span class="qn">${q.number}.</span> ` : ''}${replaceFigMarkers(renderMath(q.content), q)}</div>
    </div>
    ${optionsHtml ? `<div class="detail-section"><h4>选项</h4><div class="detail-body">${optionsHtml}</div></div>` : ''}
    <div class="detail-section">
      <h4>答案</h4>
      <div class="detail-body" style="color:var(--success);font-weight:500;">${replaceFigMarkers(renderMath(q.answer), q)}</div>
    </div>
    ${q.solution ? `<div class="detail-section">
      <h4>解析</h4>
      <div class="detail-body">${replaceFigMarkers(renderMath(q.solution), q)}</div>
    </div>` : ''}
    ${q.tags ? `<div class="detail-section"><h4>标签</h4><div class="detail-tags">${q.tags.split(',').filter(function(t){return !t.match(/^(image|answerImage):/)}).map(function(t){return '<span class="tag">'+t.trim()+'</span>';}).join('')}</div></div>` : ''}
    <div class="detail-section" style="margin-top:4px;">
      <div class="detail-body" style="font-size:.78rem;color:var(--text-muted);">${q.source ? '来源：' + q.source + ' · ' : ''}创建时间：${new Date(q.createdAt).toLocaleString()}</div>
    </div>`;
  renderMathInElement(document.getElementById('detailContent'));
  document.getElementById('detailModal').classList.add('open');
}

// ---- 添加/编辑题目 ----
function populateFormTopics(selectedId) {
  const sel = document.getElementById('formTopic');
  sel.innerHTML = '<option value="">— 选择知识点 —</option>';
  KNOWLEDGE_TREE.modules.forEach(mod => {
    const optgroup = document.createElement('optgroup');
    optgroup.label = mod.name;
    mod.chapters.forEach(ch => {
      ch.topics.forEach(t => {
        const opt = document.createElement('option');
        opt.value = t.id;
        opt.textContent = `${ch.name} / ${t.name}`;
        if (t.id === selectedId) opt.selected = true;
        optgroup.appendChild(opt);
      });
    });
    sel.appendChild(optgroup);
  });
}

function openAddModal() {
  document.getElementById('modalTitle').textContent = '添加题目';
  document.getElementById('editId').value = '';
  document.getElementById('questionForm').reset();
  populateFormTopics('');
  document.getElementById('optionsGroup').style.display = 'block';
  document.getElementById('questionModal').classList.add('open');
}

function editQuestion(id) {
  const q = questions.find(x => x.id == id);
  if (!q) return;
  document.getElementById('modalTitle').textContent = '编辑题目';
  document.getElementById('editId').value = id;
  populateFormTopics(q.topicId);
  document.getElementById('formType').value = q.type || '单选题';
  document.getElementById('formDifficulty').value = q.difficulty || '中等';
  document.getElementById('formContent').value = q.content;
  document.getElementById('formOptions').value = q.options || '';
  document.getElementById('formAnswer').value = q.answer;
  document.getElementById('formSolution').value = q.solution || '';
  document.getElementById('formNumber').value = q.number || '';
  document.getElementById('formSource').value = q.source || '';
  document.getElementById('formTags').value = q.tags || '';
  document.getElementById('optionsGroup').style.display = (q.type && (q.type.includes('单选') || q.type.includes('多选'))) ? 'block' : 'none';
  document.getElementById('questionModal').classList.add('open');
}

document.addEventListener('change', function(e) {
  if (e.target.id === 'formType') {
    document.getElementById('optionsGroup').style.display =
      (e.target.value.includes('单选') || e.target.value.includes('多选')) ? 'block' : 'none';
  }
});

document.getElementById('questionForm').addEventListener('submit', async function(e) {
  e.preventDefault();
  const editId = document.getElementById('editId').value;
  const topicId = document.getElementById('formTopic').value;
  if (!topicId) { alert('请选择知识点'); return; }

  const data = {
    topicId,
    type: document.getElementById('formType').value,
    difficulty: document.getElementById('formDifficulty').value,
    content: document.getElementById('formContent').value.trim(),
    options: document.getElementById('formOptions').value.trim() || '',
    answer: document.getElementById('formAnswer').value.trim(),
    solution: document.getElementById('formSolution').value.trim() || '',
    source: document.getElementById('formSource').value.trim() || '',
    number: document.getElementById('formNumber').value.trim() || '',
    tags: document.getElementById('formTags').value.trim() || ''
  };

  if (!data.content || !data.answer) { alert('题目内容和答案不能为空'); return; }

  document.getElementById('questionModal').classList.remove('open');

  if (editId) {
    await saveUpdateQuestion(editId, data);
  } else {
    await saveAddQuestion(data);
  }
});

async function deleteQuestion(id) {
  if (!confirm('确认删除这道题吗？')) return;
  await saveDeleteQuestion(id);
}

// ---- PUA字符清理 (PDF提取乱码) ----
function cleanPuaChars(str) {
  if (!str) return '';
  const map = {
    '\uf02d': '-',   // Adobe CID 减号
    '\uf03d': '=',   // 等号
    '\uf02b': '+',   // 加号
    '\uf07b': '{',   // 左大括号
    '\uf07d': '}',   // 右大括号
    '\uf0a0': ' ',   // 空格
    '\uf0b3': '≥',   // 大于等于
    '\uf0b2': '≤',   // 小于等于
    '\uf0a3': '×',   // 乘号
    '\uf0b0': '°',   // 度
    '\uf0a5': '$',   // 货币符号 -> $
    '\uf0e7': 'c'    // ç -> c
  };
  return str.replace(/[\uf02d\uf03d\uf02b\uf07b\uf07d\uf0a0\uf0b3\uf0b2\uf0a3\uf0b0\uf0a5\uf0e7]/g, ch => map[ch] || ch);
}

// ---- LaTeX 渲染 ----
function renderMath(text) {
  if (!text) return '';
  text = cleanPuaChars(text);
  // 安全保护：如果KaTeX尚未加载，直接返回textToHtml（纯文本+换行+表格）
  if (typeof window.katex === 'undefined' || typeof window.katex.renderToString !== 'function') {
    return textToHtml(text);
  }

  let result = '';
  let lastEnd = 0;

  // 同时匹配块级公式 $$...$$ 和行内公式 $...$
  const combined = /(\$\$(.+?)\$\$)|\$(.+?)\$/gs;
  let m;

  while ((m = combined.exec(text)) !== null) {
    // 公式前面的纯文本，做HTML转义+换行+表格转换
    result += textToHtml(text.slice(lastEnd, m.index));

    if (m[1]) {
      // 块级公式 $$...$$
      try {
        result += window.katex.renderToString(m[2].trim(), { displayMode: true, throwOnError: false });
      } catch(e) {
        result += m[1];
      }
    } else {
      // 行内公式 $...$
      try {
        result += window.katex.renderToString(m[3].trim(), { displayMode: false, throwOnError: false });
      } catch(e) {
        result += m[0];
      }
    }
    lastEnd = m.index + m[0].length;
  }

  // 剩余的纯文本，做HTML转义+换行+表格转换
  result += textToHtml(text.slice(lastEnd));

  // 最后，将KaTeX渲染后的HTML中的Markdown表格转换为HTML表格
  // （解决表格行内含有$公式$的情况）
  result = postProcessTables(result);

  return result;
}

/** 将纯文本转换为HTML（转义 + 换行 + 空格保留） */
function textToHtml(str) {
  return escapeHtml(str)
    .replace(/\n/g, '<br>')
    .replace(/  /g, '&nbsp;&nbsp;');
}

/**
 * 在KaTeX渲染完成后，将剩余的Markdown表格（| 分隔）转换为HTML <table>
 * 注意：此时的文本中$...$已经被KaTeX渲染完了，剩下的|...|可以安全转换
 */
/** 分割Markdown表格行，保留空单元格，去除首尾的空单元格（来自首尾 |） */
function splitMdRow(row) {
  // 先处理：KaTeX渲染后可能会有HTML标签，用占位符保留
  var cells = row.split('|');
  // cells[0] 是第一个|之前的内容（空字符串），cells[last] 是最后一个|之后的内容（空字符串）
  // 我们取 cells[1..last-1] 并trim每个
  var result = [];
  for (var i = 1; i < cells.length - 1; i++) {
    result.push(cells[i].trim());
  }
  return result;
}

function postProcessTables(html) {
  // 查找没有被KaTeX渲染器包裹的Markdown表格行
  // 匹配一个完整表格块：连续多行以 | 开头和结尾的行
  var result = [];
  var lines = html.split('<br>');
  var i = 0;
  var tableRows = [];
  
  function isTableRow(line) {
    var stripped = line.replace(/<[^>]+>/g, '').trim();
    return stripped.startsWith('|') && stripped.includes('|', 1) && stripped.endsWith('|');
  }
  
  function isSeparatorRow(line) {
    var stripped = line.replace(/<[^>]+>/g, '').trim();
    return /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?$/.test(stripped);
  }
  
  function flushTable() {
    if (tableRows.length < 2) {
      result = result.concat(tableRows);
      tableRows = [];
      return;
    }
    
    // Parse align from separator row (strip HTML tags since separator has only :---)
    var sepLine = tableRows[1].replace(/<[^>]+>/g, '');
    var alignCells = splitMdRow(sepLine);
    var aligns = alignCells.map(function(c) {
      if (c.startsWith(':') && c.endsWith(':')) return 'center';
      if (c.endsWith(':')) return 'right';
      return 'left';
    });
    
    var tbl = '<table class="md-table"><thead><tr>';
    // 直接使用原始行（含KaTeX渲染后的HTML），不剥离HTML标签
    var hCells = splitMdRow(tableRows[0]);
    hCells.forEach(function(c, idx) {
      var a = aligns[idx] || 'left';
      tbl += '<th style="text-align:' + a + ';padding:6px 10px;">' + c + '</th>';
    });
    tbl += '</tr></thead><tbody>';
    
    for (var ri = 2; ri < tableRows.length; ri++) {
      // 直接使用原始行，保留KaTeX渲染后的HTML标签
      var cells = splitMdRow(tableRows[ri]);
      if (cells.length === 0) continue;
      tbl += '<tr>';
      cells.forEach(function(c, idx) {
        var a = aligns[idx] || 'left';
        tbl += '<td style="text-align:' + a + ';padding:6px 10px;">' + c + '</td>';
      });
      tbl += '</tr>';
    }
    
    tbl += '</tbody></table>';
    result.push(tbl);
    tableRows = [];
  }
  
  while (i < lines.length) {
    var line = lines[i];
    if (isTableRow(line)) {
      tableRows.push(line);
    } else {
      if (tableRows.length > 0) flushTable();
      result.push(line);
    }
    i++;
  }
  if (tableRows.length > 0) flushTable();
  
  return result.join('<br>');
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function renderMathInElement(el) {
  if (window.renderMathInElement) {
    try {
      window.renderMathInElement(el, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false}
        ]
      });
    } catch(e) {}
  }
}

// ---- 简单提示 ----

function replaceFigMarkers(text, q) {
  if (!text) return text;
  function resolveSrc(figData) {
    if (!figData || !figData.trim()) return null;
    var v = figData.trim();
    if (v.startsWith('data:') || v.startsWith('http')) return v;
    if (/^[a-zA-Z0-9+/=]+$/.test(v) && v.length > 50) return 'data:image/png;base64,' + v;
    return '/' + v;
  }
  function getFigSrc(kind, index) {
    var fieldVal = q[kind];
    if (fieldVal && fieldVal.trim()) {
      var parts = fieldVal.split(',');
      // index 0 = first, index 1 = second, etc.
      var startIdx = index || 0;
      if (startIdx < parts.length) {
        var src = resolveSrc(parts[startIdx].trim());
        if (src) return src;
      }
      // fallback: iterate all
      for (var i = 0; i < parts.length; i++) {
        var src = resolveSrc(parts[i].trim());
        if (src) return src;
      }
    }
    var tags = q.tags || '';
    var re = new RegExp(kind + ':([^,\\s]+)');
    var m = tags.match(re);
    if (m) return '/' + m[1].trim();
    return null;
  }
  var result = text;
  // [figN_M] where N=1|2, M=index (1-based), e.g. [fig2_2] = 2nd answerImage
  result = result.replace(/\[fig(\d+)_(\d+)\]/g, function(match, figNumStr, imgIndexStr) {
    var kind = figNumStr === '1' ? 'image' : 'answerImage';
    var idx = parseInt(imgIndexStr, 10) - 1;  // convert to 0-based
    var src = getFigSrc(kind, idx);
    var label = '附图' + figNumStr + '-' + imgIndexStr;
    return src ? '<img src="' + src + '" style="max-width:85%;border-radius:6px;margin:6px 0;" alt="' + label + '" />' : match;
  });
  result = result.replace(/\[fig1\]/g, function() {
    var src = getFigSrc('image');
    return src ? '<img src="' + src + '" style="max-width:85%;border-radius:6px;margin:6px 0;" alt="附图1" />' : '[fig1]';
  });
  result = result.replace(/\[fig2\]/g, function() {
    var src = getFigSrc('answerImage');
    return src ? '<img src="' + src + '" style="max-width:85%;border-radius:6px;margin:6px 0;" alt="附图2" />' : '[fig2]';
  });
  return result;
}

function showToast(msg, type) {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = 'toast toast-' + (type || 'info');
  toast.textContent = msg;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 3000);
}

// ---- 导出/导入（云端已存，导出留作备份）----
function exportJSON() {
  const blob = new Blob([JSON.stringify(questions, null, 2)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `math_quiz_bank_${new Date().toISOString().slice(0,10)}.json`;
  a.click();
}

// ---- 绑定 UI 事件 ----
function bindUI() {
  document.getElementById('menuToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
  });
  document.addEventListener('click', (e) => {
    if (window.innerWidth <= 768) {
      const sidebar = document.getElementById('sidebar');
      const toggle = document.getElementById('menuToggle');
      if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    }
  });

  document.getElementById('addFirstBtn').addEventListener('click', openAddModal);

  document.getElementById('modalClose').addEventListener('click', () => document.getElementById('questionModal').classList.remove('open'));
  document.getElementById('modalCancel').addEventListener('click', () => document.getElementById('questionModal').classList.remove('open'));
  document.getElementById('detailClose').addEventListener('click', () => document.getElementById('detailModal').classList.remove('open'));
  document.querySelectorAll('.modal-overlay').forEach(m => {
    m.addEventListener('click', (e) => {
      if (e.target === m) m.classList.remove('open');
    });
  });

  // collapseAll now inline in HTML

  // 动态填充来源筛选下拉
  (function populateSourceFilter() {
    var sel = document.getElementById('filterSource');
    if (!sel) return;
    var sources = {};
    questions.forEach(function(q) {
      if (q.source) {
        q.source.split(',').forEach(function(s) {
          s = s.trim();
          if (s) sources[s] = true;
        });
      }
    });
    var currentVal = sel.value;
    sel.innerHTML = '<option value="">全部来源</option>';
    Object.keys(sources).sort().forEach(function(s) {
      sel.innerHTML += '<option value="' + s.replace(/"/g, '&quot;') + '">' + s + '</option>';
    });
    if (currentVal) sel.value = currentVal;
  })();

  document.getElementById('filterDifficulty').addEventListener('change', function() {
    currentPage = 1;
    renderList();
  });
  document.getElementById('filterType').addEventListener('change', function() {
    currentPage = 1;
    renderList();
  });
  if (document.getElementById('filterSource')) {
    document.getElementById('filterSource').addEventListener('change', function() {
      currentPage = 1;
      renderList();
    });
  }
  let searchTimer;
  document.getElementById('searchInput').addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(renderList, 300);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
    }
  });

  // 云端已含 30 道种子题，改为「刷新」按钮
  const headerRight = document.querySelector('.header-right');
  const refreshBtn = document.createElement('button');
  refreshBtn.className = 'btn btn-sm';
  refreshBtn.title = '从云端刷新题库';
  refreshBtn.textContent = '🔄 刷新';
  refreshBtn.onclick = async () => {
    refreshBtn.textContent = '⏳ 刷新中...';
    refreshBtn.disabled = true;
    await loadQuestionsFromCloud();
    renderList();
    refreshBtn.textContent = '🔄 刷新';
    refreshBtn.disabled = false;
    showToast('✅ 题库已刷新', 'success');
  };
  headerRight.insertBefore(refreshBtn, headerRight.firstChild);

  // 显示答案开关
  const answerToggle = document.createElement('button');
  answerToggle.className = 'btn btn-sm';
  answerToggle.id = 'answerToggle';
  answerToggle.title = '一键显示/隐藏全部答案';
  answerToggle.textContent = '👁 显示答案';
  answerToggle.onclick = () => {
    showAllAnswers = !showAllAnswers;
    answerToggle.textContent = showAllAnswers ? '🙈 隐藏答案' : '👁 显示答案';
    // 清空单题缓存，让所有题目跟随全局状态
    showAnswerCache = {};
    currentPage = 1;
    renderList();
  };
  headerRight.insertBefore(answerToggle, headerRight.firstChild);

  const exportBtn = document.createElement('button');
  exportBtn.className = 'btn btn-sm';
  exportBtn.title = '导出题库 JSON';
  exportBtn.textContent = '📤 导出';
  exportBtn.onclick = exportJSON;
  headerRight.appendChild(exportBtn);

  updateStats();
}
