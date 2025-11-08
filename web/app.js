(() => {
  let BASE_URL = 'http://localhost:8000';

  const els = {
    baseUrl: document.getElementById('baseUrl'),
    applyBaseUrl: document.getElementById('applyBaseUrl'),
    refreshListBtn: document.getElementById('refreshListBtn'),
    initIndexBtn: document.getElementById('initIndexBtn'),
    uploadForm: document.getElementById('uploadForm'),
    filesTableBody: document.querySelector('#filesTable tbody'),
    indexResultBody: document.querySelector('#indexResultTable tbody'),
    docDetailWrapper: document.getElementById('docDetailWrapper'),
    docDetailBody: document.querySelector('#docDetailTable tbody'),
  };

  // Apply backend base URL
  els.applyBaseUrl.addEventListener('click', () => {
    const url = (els.baseUrl.value || '').trim();
    if (!url) return alert('请输入后端地址');
    BASE_URL = url.replace(/\/$/, '');
    alert(`后端地址已设置为：${BASE_URL}`);
  });

  // Fetch helper
  async function api(path, options = {}) {
    const url = `${BASE_URL}${path}`;
    const res = await fetch(url, options);
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(`请求失败 ${res.status}: ${msg}`);
    }
    // 尝试解析 JSON
    const contentType = res.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      return res.json();
    }
    return res.text();
  }

  // 列出文档：GET /documents
  async function fetchDocuments() {
    try {
      const items = await api('/documents');
      // items 是字典列表：{ id, filename, metadata: { size } }
      renderFiles(items);
    } catch (e) {
      console.error(e);
      alert(`获取文档列表失败：${e.message}`);
    }
  }

  function renderFiles(items = []) {
    els.filesTableBody.innerHTML = '';
    if (!Array.isArray(items)) {
      return;
    }
    items.forEach(item => {
      const tr = document.createElement('tr');
      const size = item?.metadata?.size ?? '';
      tr.innerHTML = `
        <td class="mono">${escapeHtml(item.id)}</td>
        <td>${escapeHtml(item.filename || '')}</td>
        <td>${size}</td>
        <td>
          <button data-id="${item.id}" class="detail-btn">详情</button>
          <button data-id="${item.id}" class="danger delete-btn">删除</button>
        </td>
      `;
      els.filesTableBody.appendChild(tr);
    });

    // 绑定操作按钮
    els.filesTableBody.querySelectorAll('.delete-btn').forEach(btn => {
      btn.addEventListener('click', async (ev) => {
        const docId = ev.currentTarget.getAttribute('data-id');
        if (!docId) return;
        if (!confirm(`确认删除文档 ${docId} ?`)) return;
        try {
          await api(`/documents/${encodeURIComponent(docId)}`, { method: 'DELETE' });
          await fetchDocuments();
        } catch (e) {
          console.error(e);
          alert(`删除失败：${e.message}`);
        }
      });
    });

    els.filesTableBody.querySelectorAll('.detail-btn').forEach(btn => {
      btn.addEventListener('click', async (ev) => {
        const docId = ev.currentTarget.getAttribute('data-id');
        if (!docId) return;
        try {
          const detail = await api(`/documents/${encodeURIComponent(docId)}`);
          renderDocDetail(detail);
        } catch (e) {
          console.error(e);
          alert(`获取详情失败：${e.message}`);
        }
      });
    });
  }

  function renderDocDetail(detail) {
    els.docDetailWrapper.style.display = 'block';
    els.docDetailBody.innerHTML = '';
    Object.entries(detail || {}).forEach(([k, v]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${escapeHtml(k)}</td><td class="mono">${escapeHtml(String(v ?? ''))}</td>`;
      els.docDetailBody.appendChild(tr);
    });
  }

  // 上传文档：POST /documents (multipart/form-data)
  els.uploadForm.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const fileInput = document.getElementById('fileInput');
    const docType = document.getElementById('docType').value.trim();
    const sourcePath = document.getElementById('sourcePath').value.trim();
    const metadata = document.getElementById('metadata').value.trim();
    if (!fileInput.files?.length) {
      alert('请选择文件');
      return;
    }
    const fd = new FormData();
    fd.append('file', fileInput.files[0]);
    if (docType) fd.append('doc_type', docType);
    if (sourcePath) fd.append('source_path', sourcePath);
    if (metadata) fd.append('metadata', metadata);
    try {
      const resp = await api('/documents', { method: 'POST', body: fd });
      alert(`上传成功：doc_id=${resp?.doc_id ?? ''}`);
      await fetchDocuments();
      // 清理表单
      els.uploadForm.reset();
    } catch (e) {
      console.error(e);
      alert(`上传失败：${e.message}`);
    }
  });

  // 构建索引：POST /index/init
  els.initIndexBtn.addEventListener('click', async () => {
    try {
      const result = await api('/index/init', { method: 'POST' });
      renderIndexResult(result);
    } catch (e) {
      console.error(e);
      alert(`索引构建失败：${e.message}`);
    }
  });

  function renderIndexResult(result) {
    els.indexResultBody.innerHTML = '';
    const entries = Object.entries(result || {});
    if (!entries.length) {
      const tr = document.createElement('tr');
      tr.innerHTML = '<td class="muted">无结果</td><td></td>';
      els.indexResultBody.appendChild(tr);
      return;
    }
    entries.forEach(([k, v]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td>${escapeHtml(k)}</td><td class="mono">${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}</td>`;
      els.indexResultBody.appendChild(tr);
    });
  }

  // 工具函数
  function escapeHtml(s) {
    return String(s)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }

  // 绑定刷新
  els.refreshListBtn.addEventListener('click', fetchDocuments);

  // 初始化加载
  fetchDocuments();
})();