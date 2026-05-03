/* =================================================================
   SmartFin – Tam API Entegrasyonu
   API sunucusu farklı port/adreste çalışıyorsa aşağıyı değiştirin:
   ================================================================= */
const API_BASE = 'http://localhost:8000/api/v1';

// ─── Token Yönetimi ────────────────────────────────────────────────
const Token = {
    get access()  { return localStorage.getItem('sf_access'); },
    get refresh() { return localStorage.getItem('sf_refresh'); },
    get user()    { const u = localStorage.getItem('sf_user'); return u ? JSON.parse(u) : null; },
    save(access, refresh, user) {
        localStorage.setItem('sf_access',  access);
        localStorage.setItem('sf_refresh', refresh);
        localStorage.setItem('sf_user',    JSON.stringify(user));
    },
    clear() {
        ['sf_access','sf_refresh','sf_user'].forEach(k => localStorage.removeItem(k));
    },
};

// ─── HTTP İstekleri ────────────────────────────────────────────────
async function http(path, opts = {}) {
    const headers = { ...(opts.headers || {}) };
    if (!(opts.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    if (Token.access) headers['Authorization'] = `Bearer ${Token.access}`;

    let res = await fetch(`${API_BASE}${path}`, { ...opts, headers });

    // 401 → token yenile
    if (res.status === 401 && Token.refresh) {
        const rr = await fetch(`${API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: Token.refresh }),
        });
        if (rr.ok) {
            const d = await rr.json();
            Token.save(d.access_token, d.refresh_token, d.user);
            headers['Authorization'] = `Bearer ${d.access_token}`;
            res = await fetch(`${API_BASE}${path}`, { ...opts, headers });
        } else {
            Token.clear();
            showAuth();
            return null;
        }
    }
    return res;
}

const GET    = async (p)    => { const r = await http(p); if (!r||!r.ok) return null; return r.json(); };
const POST   = (p, b)       => http(p, { method:'POST',   body: JSON.stringify(b) });
const DELETE = (p)          => http(p, { method:'DELETE' });
const UPLOAD = (p, form)    => http(p, { method:'POST',   body: form });

// ─── Toast ─────────────────────────────────────────────────────────
function toast(msg, type = 'info') {
    const c = document.getElementById('toastContainer');
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.innerHTML = `<span>${msg}</span>`;
    c.appendChild(t);
    requestAnimationFrame(() => t.classList.add('show'));
    setTimeout(() => { t.classList.remove('show'); setTimeout(() => t.remove(), 350); }, 4000);
}

// ─── Buton Yükleme Durumu ──────────────────────────────────────────
function setLoading(btn, loading, originalHTML) {
    if (loading) {
        btn._original = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span>';
    } else {
        btn.disabled = false;
        btn.innerHTML = originalHTML !== undefined ? originalHTML : btn._original;
    }
    lucide.createIcons();
}

// ─── Auth Ekranı ───────────────────────────────────────────────────
function showAuth() {
    document.getElementById('authScreen').style.display = 'flex';
    document.getElementById('appScreen').style.display  = 'none';
    lucide.createIcons();
}

function showApp() {
    document.getElementById('authScreen').style.display = 'none';
    document.getElementById('appScreen').style.display  = 'flex';
}

function switchTab(tab) {
    document.getElementById('loginForm').style.display    = tab === 'login'    ? 'flex' : 'none';
    document.getElementById('registerForm').style.display = tab === 'register' ? 'flex' : 'none';
    document.getElementById('tabLogin').classList.toggle('active',    tab === 'login');
    document.getElementById('tabRegister').classList.toggle('active', tab === 'register');
    document.getElementById('loginError').textContent    = '';
    document.getElementById('registerError').textContent = '';
}

// ─── Login ─────────────────────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();
    const btn = document.getElementById('loginBtn');
    setLoading(btn, true);
    document.getElementById('loginError').textContent = '';

    const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            email:    document.getElementById('loginEmail').value.trim(),
            password: document.getElementById('loginPassword').value,
        }),
    });

    setLoading(btn, false, '<i data-lucide="log-in"></i> Giriş Yap');

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        document.getElementById('loginError').textContent = err.detail || 'Giriş başarısız.';
        return;
    }
    const data = await res.json();
    Token.save(data.access_token, data.refresh_token, data.user);
    initApp(data.user);
}

// ─── Register ──────────────────────────────────────────────────────
async function handleRegister(e) {
    e.preventDefault();
    const btn = document.getElementById('registerBtn');
    setLoading(btn, true);
    document.getElementById('registerError').textContent = '';

    const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            full_name: document.getElementById('regName').value.trim(),
            email:     document.getElementById('regEmail').value.trim(),
            password:  document.getElementById('regPassword').value,
        }),
    });

    setLoading(btn, false, '<i data-lucide="user-plus"></i> Kayıt Ol');

    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        document.getElementById('registerError').textContent = err.detail || 'Kayıt başarısız.';
        return;
    }
    toast('Kayıt başarılı! Giriş yapabilirsiniz.', 'success');
    switchTab('login');
    document.getElementById('loginEmail').value = document.getElementById('regEmail').value;
}

// ─── Logout ────────────────────────────────────────────────────────
function handleLogout() {
    Token.clear();
    showAuth();
    toast('Çıkış yapıldı.', 'info');
}

// ─── Şifre Değiştir ────────────────────────────────────────────────
async function handleChangePassword(e) {
    e.preventDefault();
    document.getElementById('pwError').textContent = '';
    const res = await POST('/auth/change-password', {
        current_password: document.getElementById('currentPassword').value,
        new_password:     document.getElementById('newPassword').value,
    });
    if (res && res.status === 204) {
        closeModal('changePasswordModal');
        toast('Şifre başarıyla değiştirildi.', 'success');
        e.target.reset();
    } else {
        const err = await res?.json().catch(() => ({}));
        document.getElementById('pwError').textContent = err.detail || 'Hata oluştu.';
    }
}

// ─── Uygulama Başlatma ─────────────────────────────────────────────
async function initApp(user) {
    const u = user || Token.user;
    if (!u) { showAuth(); return; }

    showApp();
    document.getElementById('sidebarName').textContent = u.full_name;
    document.getElementById('sidebarRole').textContent =
        u.role === 'admin' ? 'Yönetici' : u.role === 'analyst' ? 'Analist' : 'Kullanıcı';
    document.getElementById('avatarImg').src =
        `https://ui-avatars.com/api/?name=${encodeURIComponent(u.full_name)}&background=2E86AB&color=fff&size=80`;

    if (u.role === 'admin') {
        document.getElementById('navAdmin').style.display = 'flex';
        document.body.classList.add('admin-theme');
    } else {
        document.getElementById('navAdmin').style.display = 'none';
        document.body.classList.remove('admin-theme');
    }

    lucide.createIcons();

    // Dashboard varsayılan görünüm
    switchView('dashboard', document.querySelector('[data-view="dashboard"]'), false);
    loadNotifications();
}

// ─── Görünüm Geçişi ────────────────────────────────────────────────
const VIEWS = ['dashboard','companies','reports','subscription','admin'];

async function switchView(view, navEl, loadData = true) {
    VIEWS.forEach(v => {
        document.getElementById(`view-${v}`).style.display = v === view ? 'block' : 'none';
    });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    if (navEl) navEl.classList.add('active');
    else document.querySelector(`[data-view="${view}"]`)?.classList.add('active');

    lucide.createIcons();

    if (!loadData) return;
    if (view === 'dashboard')    loadDashboard();
    if (view === 'companies')    loadCompanies();
    if (view === 'reports')      await initReportsView();
    if (view === 'subscription') loadSubscriptionView();
    if (view === 'admin')        loadAdminView();
}

// ─── Dashboard ─────────────────────────────────────────────────────
async function loadDashboard() {
    const [comps, sub] = await Promise.all([
        GET('/companies?page=1&page_size=1'),
        GET('/subscriptions/my-subscription'),
    ]);

    if (comps !== null) {
        document.getElementById('statCompanies').textContent = comps.total ?? 0;
    }

    renderSubStats(sub);

    // Son raporlar: ilk 5 şirketten son 3'er rapor
    const allComps = await GET('/companies?page=1&page_size=5');
    if (!allComps?.items?.length) {
        document.getElementById('statReports').textContent = 0;
        document.getElementById('recentReportsBody').innerHTML =
            '<tr><td colspan="5" class="text-center text-muted">Henüz rapor yok.</td></tr>';
        return;
    }

    let allReports = [];
    let totalCount = 0;
    for (const c of allComps.items) {
        const r = await GET(`/financial/companies/${c.id}/reports?page=1&page_size=3`);
        if (r?.items) {
            totalCount += r.total || r.items.length;
            r.items.forEach(rep => { rep._company_name = c.name; });
            allReports = allReports.concat(r.items);
        }
    }
    allReports.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    document.getElementById('statReports').textContent = totalCount;
    renderRecentReports(allReports.slice(0, 5));
}

function renderSubStats(sub) {
    if (!sub || sub.status === 'no_subscription') {
        document.getElementById('statAiUsed').textContent  = 'Yok';
        document.getElementById('statSubEnd').textContent  = '—';
        document.getElementById('statSubStatus').textContent = 'Abonelik yok';
        renderSubscriptionWidget(null);
        return;
    }
    const used  = sub.ai_calls_used  ?? 0;
    const limit = sub.ai_calls_limit ?? '∞';
    document.getElementById('statAiUsed').textContent  = `${used} / ${limit}`;
    document.getElementById('statAiLimit').textContent = 'AI Çağrı (Bu Ay)';
    document.getElementById('statSubEnd').textContent  =
        sub.end_date ? new Date(sub.end_date).toLocaleDateString('tr-TR') : '—';
    document.getElementById('statSubStatus').textContent =
        sub.status === 'active' ? 'Aktif' : sub.status;
    renderSubscriptionWidget(sub);
}

function renderRecentReports(reports) {
    const tbody = document.getElementById('recentReportsBody');
    if (!reports.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Rapor bulunamadı.</td></tr>';
        return;
    }
    tbody.innerHTML = reports.map(r => `
        <tr>
            <td><div class="company-cell">
                <div class="company-logo">${(r._company_name||'?')[0].toUpperCase()}</div>
                <span>${escHtml(r._company_name||'—')}</span>
            </div></td>
            <td>${r.fiscal_year}</td>
            <td>${reportTypeLabel(r.report_type)}</td>
            <td>${r.is_ai_generated
                ? '<span class="status-badge success">AI</span>'
                : '<span class="status-badge warning">Manuel</span>'}</td>
            <td>
                <button class="action-btn" onclick="downloadPptx(${r.id})" title="PPTX İndir">
                    <i data-lucide="download"></i>
                </button>
            </td>
        </tr>
    `).join('');
    lucide.createIcons();
}

function renderSubscriptionWidget(sub) {
    const el = document.getElementById('subscriptionWidget');
    if (!sub) {
        el.innerHTML = `
            <p class="ai-comment">Aktif aboneliğiniz yok. AI analizi kullanmak için bir paket satın alın.</p>
            <button class="btn-outline-primary full-width" onclick="switchView('subscription', document.querySelector('[data-view=subscription]'))">
                <i data-lucide="credit-card"></i> Paketleri Gör
            </button>`;
        lucide.createIcons();
        return;
    }
    const limit = sub.ai_calls_limit || 0;
    const used  = sub.ai_calls_used  || 0;
    const pct   = limit ? Math.min(Math.round(used/limit*100), 100) : 0;
    const rlimit = sub.reports_limit || 0;
    const rused  = sub.reports_used  || 0;
    const rpct   = rlimit ? Math.min(Math.round(rused/rlimit*100), 100) : 0;

    el.innerHTML = `
        <p class="sub-package-name">${escHtml(sub.package||'—')}</p>
        <div class="sub-usage"><span>AI Çağrı</span><span>${used} / ${sub.ai_calls_limit??'∞'}</span></div>
        <div class="progress-bar"><div class="progress-fill" style="width:${pct}%"></div></div>
        <div class="sub-usage" style="margin-top:.6rem"><span>Raporlar</span><span>${rused} / ${sub.reports_limit??'∞'}</span></div>
        <div class="progress-bar" style="margin-bottom:.75rem"><div class="progress-fill" style="width:${rpct}%"></div></div>
        <div class="ai-tags">
            <span class="tag ${sub.status==='active'?'positive':'info'}">${sub.status==='active'?'Aktif':sub.status}</span>
        </div>
        <button class="btn-outline-primary full-width" style="margin-top:1rem"
            onclick="switchView('subscription', document.querySelector('[data-view=subscription]'))">
            <i data-lucide="credit-card"></i> Paket Yönet
        </button>`;
    lucide.createIcons();
}

// ─── Şirketler ─────────────────────────────────────────────────────
let companiesPage = 1;
let _companySearchTimer = null;

function debounceCompanySearch(val) {
    clearTimeout(_companySearchTimer);
    _companySearchTimer = setTimeout(() => { companiesPage = 1; loadCompanies(val); }, 300);
}

async function loadCompanies(search = '') {
    const searchVal = search || document.getElementById('companySearch')?.value || '';
    const q = searchVal ? `&search=${encodeURIComponent(searchVal)}` : '';
    const data = await GET(`/companies?page=${companiesPage}&page_size=15${q}`);
    if (!data) return;

    const tbody = document.getElementById('companiesBody');
    if (!data.items?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Şirket bulunamadı.</td></tr>';
        document.getElementById('companiesPagination').innerHTML = '';
        return;
    }

    tbody.innerHTML = data.items.map(c => `
        <tr>
            <td><div class="company-cell">
                <div class="company-logo" style="background:${strColor(c.name)}">${c.name[0].toUpperCase()}</div>
                <span>${escHtml(c.name)}</span>
            </div></td>
            <td>${escHtml(c.tax_id||'—')}</td>
            <td>${escHtml(c.sector||'—')}</td>
            <td>${new Date(c.created_at).toLocaleDateString('tr-TR')}</td>
            <td style="display:flex;gap:4px;align-items:center">
                <button class="action-btn" title="Raporlarını Gör"
                    onclick="goToReports(${c.id})">
                    <i data-lucide="file-text"></i>
                </button>
                <button class="action-btn" title="Rapor Yükle"
                    onclick="openUploadModal(${c.id})">
                    <i data-lucide="upload"></i>
                </button>
                <button class="action-btn danger-btn" title="Sil"
                    onclick="deleteCompany(${c.id},'${escAttr(c.name)}')">
                    <i data-lucide="trash-2"></i>
                </button>
            </td>
        </tr>
    `).join('');
    lucide.createIcons();

    renderPagination('companiesPagination', data.page, data.pages, p => {
        companiesPage = p;
        loadCompanies(document.getElementById('companySearch')?.value || '');
    });
}

function goToReports(companyId) {
    // Rapor sekmesine geç ve şirket filtresini set et
    _pendingCompanyFilter = companyId;
    switchView('reports', document.querySelector('[data-view="reports"]'));
}

async function handleCreateCompany(e) {
    e.preventDefault();
    const btn = document.getElementById('createCompanyBtn');
    setLoading(btn, true);
    document.getElementById('companyError').textContent = '';

    const body = {
        name:                       document.getElementById('newCompanyName').value.trim(),
        tax_id:                     document.getElementById('newCompanyTaxId').value.trim() || null,
        commercial_register_number: document.getElementById('newCompanyRegisterNo').value.trim() || null,
        establishment_date:         document.getElementById('newCompanyEstDate').value || null,
        sector:                     document.getElementById('newCompanySector').value.trim() || null,
        description:                document.getElementById('newCompanyDesc').value.trim() || null,
        authorized_person_name:     document.getElementById('newCompanyAuthPerson').value.trim() || null,
        contact_info:               document.getElementById('newCompanyContact').value.trim() || null,
        address:                    document.getElementById('newCompanyAddress').value.trim() || null,
        annual_turnover_estimate:   parseFloat(document.getElementById('newCompanyTurnover').value) || null,
        contract_value:             parseFloat(document.getElementById('newCompanyContractValue').value) || null,
        contract_start_date:        document.getElementById('newCompanyContractStart').value || null,
        contract_end_date:          document.getElementById('newCompanyContractEnd').value || null,
        contract_type:              document.getElementById('newCompanyContractType').value || null,
    };

    const res = await POST('/companies', body);
    setLoading(btn, false, '<i data-lucide="plus"></i> Oluştur');

    if (!res || !res.ok) {
        const err = await res?.json().catch(() => ({}));
        document.getElementById('companyError').textContent = err.detail || 'Hata oluştu.';
        return;
    }
    closeModal('createCompanyModal');
    document.getElementById('createCompanyForm').reset();
    toast('Şirket başarıyla oluşturuldu.', 'success');
    loadCompanies();
    refreshCompanySelects();
}

async function deleteCompany(id, name) {
    if (!confirm(`"${name}" şirketini ve TÜM raporlarını silmek istediğinize emin misiniz?\nBu işlem geri alınamaz.`)) return;
    const res = await DELETE(`/companies/${id}`);
    if (res?.status === 204) {
        toast('Şirket silindi.', 'success');
        loadCompanies();
        refreshCompanySelects();
    } else {
        toast('Silme işlemi başarısız.', 'error');
    }
}

function openCreateCompanyModal() {
    document.getElementById('createCompanyForm').reset();
    document.getElementById('companyError').textContent = '';
    document.getElementById('createCompanyModal').classList.add('active');
    resetMetadataDropZone();
    lucide.createIcons();
}

function resetMetadataDropZone() {
    document.getElementById('metadataProgress').style.display = 'none';
    document.getElementById('metadataProgressFill').style.width = '0%';
    const dz = document.getElementById('companyMetadataDropZone');
    dz.innerHTML = `
        <i data-lucide="file-up" style="width: 20px; height: 20px;"></i>
        <p style="font-size: 0.8rem;">Dosya seç veya sürükle</p>
        <input type="file" id="companyMetadataFile" style="display:none" accept=".pdf,.png,.jpg,.jpeg,.webp">`;
    lucide.createIcons();
    dz.onclick = () => document.getElementById('companyMetadataFile').click();
    document.getElementById('companyMetadataFile').onchange = e => {
        if (e.target.files[0]) handleMetadataUpload(e.target.files[0]);
    };
}

async function handleMetadataUpload(file) {
    const dz = document.getElementById('companyMetadataDropZone');
    const prog = document.getElementById('metadataProgress');
    const fill = document.getElementById('metadataProgressFill');
    const status = document.getElementById('metadataStatus');

    prog.style.display = 'block';
    fill.style.width = '20%';
    status.textContent = 'Dosya yükleniyor...';

    const form = new FormData();
    form.append('file', file);

    const res = await UPLOAD('/companies/extract-metadata', form);
    if (!res || !res.ok) {
        toast('Bilgi çıkarma başarısız.', 'error');
        prog.style.display = 'none';
        return;
    }

    fill.style.width = '100%';
    status.textContent = 'Bilgiler çıkarıldı!';
    
    const data = await res.json();
    if (data.name) document.getElementById('newCompanyName').value = data.name;
    if (data.tax_id) document.getElementById('newCompanyTaxId').value = data.tax_id;
    if (data.commercial_register_number) document.getElementById('newCompanyRegisterNo').value = data.commercial_register_number;
    if (data.establishment_date) document.getElementById('newCompanyEstDate').value = data.establishment_date;
    if (data.sector) document.getElementById('newCompanySector').value = data.sector;
    if (data.description) document.getElementById('newCompanyDesc').value = data.description;
    if (data.authorized_person_name) document.getElementById('newCompanyAuthPerson').value = data.authorized_person_name;
    if (data.contact_info) document.getElementById('newCompanyContact').value = data.contact_info;
    if (data.address) document.getElementById('newCompanyAddress').value = data.address;
    if (data.annual_turnover_estimate) document.getElementById('newCompanyTurnover').value = data.annual_turnover_estimate;
    if (data.contract_value) document.getElementById('newCompanyContractValue').value = data.contract_value;
    if (data.contract_start_date) document.getElementById('newCompanyContractStart').value = data.contract_start_date;
    if (data.contract_end_date) document.getElementById('newCompanyContractEnd').value = data.contract_end_date;
    if (data.contract_type) document.getElementById('newCompanyContractType').value = data.contract_type;
    
    toast('Şirket bilgileri otomatik dolduruldu.', 'success');
    setTimeout(() => { prog.style.display = 'none'; }, 2000);
}

// ─── Raporlar ──────────────────────────────────────────────────────
let _companyCache     = [];  // tüm şirketler: {id, name}
let _pendingCompanyFilter = null;
let reportsPage = 1;

async function initReportsView() {
    await loadCompanyFilter();
    buildYearFilter();

    if (_pendingCompanyFilter) {
        document.getElementById('filterCompany').value = String(_pendingCompanyFilter);
        _pendingCompanyFilter = null;
    }
    loadAllReports();
}

async function loadCompanyFilter() {
    const data = await GET('/companies?page=1&page_size=100');
    _companyCache = data?.items || [];

    const sel = document.getElementById('filterCompany');
    const currentVal = sel.value;
    sel.innerHTML = '<option value="">Şirket Seçin...</option>';
    _companyCache.forEach(c => {
        const o = document.createElement('option');
        o.value = c.id; o.textContent = c.name;
        sel.appendChild(o);
    });
    if (currentVal) sel.value = currentVal;
}

function buildYearFilter() {
    const sel = document.getElementById('filterYear');
    const curYear = new Date().getFullYear();
    sel.innerHTML = '<option value="">Tüm Yıllar</option>';
    for (let y = curYear; y >= 2018; y--) {
        const o = document.createElement('option'); o.value = y; o.textContent = y;
        sel.appendChild(o);
    }
}

async function loadAllReports() {
    const companyId = document.getElementById('filterCompany').value;
    const year      = document.getElementById('filterYear').value;
    const type      = document.getElementById('filterType').value;
    const tbody     = document.getElementById('reportsBody');

    if (!companyId) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Yukarıdan bir şirket seçin.</td></tr>';
        document.getElementById('reportsPagination').innerHTML = '';
        return;
    }

    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Yükleniyor...</td></tr>';

    let url = `/financial/companies/${companyId}/reports?page=${reportsPage}&page_size=20`;
    if (year) url += `&fiscal_year=${year}`;
    if (type) url += `&report_type=${type}`;

    const data = await GET(url);
    if (!data) return;

    const compName = _companyCache.find(c => String(c.id) === String(companyId))?.name || '—';

    if (!data.items?.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Bu şirkete ait rapor bulunamadı.</td></tr>';
        document.getElementById('reportsPagination').innerHTML = '';
        return;
    }

    tbody.innerHTML = data.items.map(r => {
        let ratios = {};
        try { ratios = typeof r.ai_ratios === 'string' ? JSON.parse(r.ai_ratios) : (r.ai_ratios || {}); } catch(e) {}
        const score = ratios.financial_score ?? null;
        const scoreBadge = score != null
            ? `<span class="score-badge ${score >= 70 ? 'good' : score >= 40 ? 'avg' : 'bad'}" title="Finansal Skor">${score}</span>`
            : '—';
        return `
        <tr>
            <td><div class="company-cell">
                <div class="company-logo" style="background:${strColor(compName)}">${compName[0].toUpperCase()}</div>
                <span>${escHtml(compName)}</span>
            </div></td>
            <td>${r.fiscal_year}</td>
            <td>${reportTypeLabel(r.report_type)}</td>
            <td>${periodLabel(r.period)}</td>
            <td>${r.is_ai_generated
                ? '<span class="status-badge success">AI</span>'
                : '<span class="status-badge warning">Manuel</span>'}</td>
            <td>${scoreBadge}</td>
            <td>
                <div style="display:flex;gap:4px;flex-wrap:wrap">
                    <button class="action-btn" title="Detayları Gör" onclick="viewReportDetail(${r.id})">
                        <i data-lucide="eye"></i>
                    </button>
                    <button class="action-btn" title="AI Analiz Başlat" id="analyzeBtn-${r.id}"
                        onclick="triggerAnalysis(${r.id}, this)">
                        <i data-lucide="sparkles"></i>
                    </button>
                    <button class="action-btn" title="PPTX İndir"
                        onclick="downloadPptx(${r.id})">
                        <i data-lucide="presentation"></i>
                    </button>
                    <button class="action-btn danger-btn" title="Raporu Sil"
                        onclick="deleteReport(${r.id})">
                        <i data-lucide="trash-2"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    }).join('');
    lucide.createIcons();

    renderPagination('reportsPagination', data.page, data.pages, p => {
        reportsPage = p; loadAllReports();
    });
}

async function triggerAnalysis(reportId, btn) {
    setLoading(btn, true);
    toast('AI analizi başlatıldı. Bu biraz sürebilir...', 'info');
    const res = await http(`/financial/reports/${reportId}/analyze`, { method: 'POST' });
    setLoading(btn, false);
    lucide.createIcons();
    if (res?.status === 402 || res?.status === 429) {
        const err = await res.json().catch(() => ({}));
        toast(err.detail || 'Bu özellik için abonelik gereklidir.', 'error');
        showPremiumModal();
        return;
    }
    if (res?.ok) {
        toast('AI analizi tamamlandı!', 'success');
        loadAllReports();
        loadDashboard();
    } else {
        const err = await res?.json().catch(() => ({}));
        toast(err.detail || 'Analiz başarısız.', 'error');
    }
}

async function deleteReport(reportId) {
    if (!confirm('Bu raporu silmek istediğinize emin misiniz?')) return;
    const res = await DELETE(`/financial/reports/${reportId}`);
    if (res?.status === 204) {
        toast('Rapor silindi.', 'success');
        loadAllReports();
    } else {
        toast('Silme başarısız.', 'error');
    }
}

async function downloadPptx(reportId) {
    toast('PPTX hazırlanıyor...', 'info');
    const res = await http(`/financial/reports/${reportId}/export/pptx`);
    if (!res?.ok) { toast('İndirme başarısız.', 'error'); return; }
    downloadBlob(await res.blob(), `rapor_${reportId}.pptx`);
}

async function downloadCsv(reportId) {
    const res = await http(`/financial/reports/${reportId}/export/csv`);
    if (!res?.ok) { toast('İndirme başarısız.', 'error'); return; }
    downloadBlob(await res.blob(), `rapor_${reportId}.csv`);
}

function downloadBlob(blob, name) {
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement('a'), { href: url, download: name });
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
}

// ─── Upload Modal ──────────────────────────────────────────────────
let _selectedFile = null;
let _progressTimer = null;

async function openUploadModal(presetCompanyId = null) {
    // Şirket listesini güncelle
    await refreshCompanySelects(presetCompanyId);
    document.getElementById('uploadFiscalYear').value = new Date().getFullYear();
    document.getElementById('uploadError').textContent = '';
    resetDropZone();
    document.getElementById('uploadModal').classList.add('active');
    lucide.createIcons();
}

async function refreshCompanySelects(presetId = null) {
    const data = await GET('/companies?page=1&page_size=100');
    const companies = data?.items || [];
    _companyCache = companies;

    const sel = document.getElementById('uploadCompanyId');
    sel.innerHTML = '<option value="">Şirket seçin...</option>';
    companies.forEach(c => {
        const o = document.createElement('option');
        o.value = c.id; o.textContent = c.name;
        sel.appendChild(o);
    });
    if (presetId) sel.value = String(presetId);
}

function resetDropZone() {
    _selectedFile = null;
    clearInterval(_progressTimer);
    document.getElementById('uploadProgress').style.display = 'none';
    document.getElementById('progressFill').style.width = '0%';
    document.getElementById('uploadStatus').textContent = 'Belge yükleniyor...';
    document.getElementById('startAnalysis').disabled = true;

    const dz = document.getElementById('dropZone');
    dz.innerHTML = `
        <i data-lucide="upload-cloud"></i>
        <p>Sürükle bırak veya <span>dosya seç</span></p>
        <small>PDF, PNG, JPG, WEBP (Maks. 20MB)</small>
        <input type="file" id="fileInput" style="display:none" accept=".pdf,.png,.jpg,.jpeg,.webp">`;
    lucide.createIcons();

    dz.onclick = () => document.getElementById('fileInput').click();
    document.getElementById('fileInput').onchange = e => {
        if (e.target.files[0]) setUploadFile(e.target.files[0]);
    };
}

function setUploadFile(file) {
    const validTypes = ['application/pdf','image/png','image/jpeg','image/jpg','image/webp'];
    if (!validTypes.includes(file.type)) {
        toast('Geçersiz dosya türü. PDF, PNG, JPG veya WEBP yükleyin.', 'error'); return;
    }
    if (file.size > 20 * 1024 * 1024) {
        toast('Dosya 20MB sınırını aşıyor.', 'error'); return;
    }
    _selectedFile = file;
    const dz = document.getElementById('dropZone');
    dz.innerHTML = `
        <i data-lucide="file-check" style="color:var(--success)"></i>
        <p style="color:var(--text-main);font-weight:600">${escHtml(file.name)}</p>
        <small style="color:var(--text-muted)">${(file.size/1024/1024).toFixed(2)} MB</small>
        <input type="file" id="fileInput" style="display:none" accept=".pdf,.png,.jpg,.jpeg,.webp">`;
    lucide.createIcons();
    dz.onclick = () => document.getElementById('fileInput').click();
    document.getElementById('fileInput').onchange = e => {
        if (e.target.files[0]) setUploadFile(e.target.files[0]);
    };
    document.getElementById('startAnalysis').disabled = false;
}

// Drag & drop
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('dropZone')?.addEventListener('dragover', e => {
        e.preventDefault();
        e.currentTarget.style.borderColor = 'var(--primary)';
        e.currentTarget.style.background  = 'var(--glass)';
    });
    document.getElementById('dropZone')?.addEventListener('dragleave', e => {
        e.currentTarget.style.borderColor = '';
        e.currentTarget.style.background  = '';
    });
    document.getElementById('dropZone')?.addEventListener('drop', e => {
        e.preventDefault();
        e.currentTarget.style.borderColor = '';
        e.currentTarget.style.background  = '';
        if (e.dataTransfer.files[0]) setUploadFile(e.dataTransfer.files[0]);
    });
});

async function handleUpload() {
    const companyId  = document.getElementById('uploadCompanyId').value;
    const fiscalYear = document.getElementById('uploadFiscalYear').value;
    document.getElementById('uploadError').textContent = '';

    if (!companyId)   { document.getElementById('uploadError').textContent = 'Lütfen şirket seçin.'; return; }
    if (!fiscalYear)  { document.getElementById('uploadError').textContent = 'Lütfen mali yıl girin.'; return; }
    if (!_selectedFile) { document.getElementById('uploadError').textContent = 'Lütfen dosya seçin.'; return; }

    const btn = document.getElementById('startAnalysis');
    setLoading(btn, true);
    document.getElementById('uploadProgress').style.display = 'block';
    startProgressAnimation();

    const form = new FormData();
    form.append('file', _selectedFile);
    form.append('fiscal_year', fiscalYear);
    form.append('period', 'annual');

    const res = await UPLOAD(`/financial/companies/${companyId}/upload-document`, form);

    clearInterval(_progressTimer);
    document.getElementById('progressFill').style.width = '100%';
    setLoading(btn, false, '<i data-lucide="sparkles"></i> Analizi Başlat');

    if (res?.status === 402 || res?.status === 429) {
        document.getElementById('uploadProgress').style.display = 'none';
        closeModal('uploadModal');
        showPremiumModal();
        return;
    }
    if (!res?.ok) {
        const err = await res?.json().catch(() => ({}));
        document.getElementById('uploadProgress').style.display = 'none';
        document.getElementById('uploadError').textContent = err.detail || 'Yükleme başarısız.';
        return;
    }

    const data = await res.json();
    closeModal('uploadModal');
    
    // Analizi otomatik başlat (rasyolar ve grafikler için)
    if (data.report_id) {
        await triggerAnalysis(data.report_id);
    }

    const conf = data.confidence_score ? ` (Güven: %${(data.confidence_score*100).toFixed(0)})` : '';
    toast(`Belge işlendi ve analiz tamamlandı!${conf}`, 'success');

    // Eğer raporlar ekranındaysak yenile
    if (document.getElementById('view-reports').style.display !== 'none') loadAllReports();
    loadDashboard();
}

function startProgressAnimation() {
    const fill   = document.getElementById('progressFill');
    const status = document.getElementById('uploadStatus');
    const steps  = [
        [15, 'Dosya sunucuya yükleniyor...'],
        [35, 'Gemini AI belgeyi işliyor...'],
        [60, 'Finansal veriler çıkarılıyor...'],
        [80, 'Veriler doğrulanıyor...'],
        [90, 'Tamamlanıyor...'],
    ];
    let i = 0;
    fill.style.width = '5%';
    _progressTimer = setInterval(() => {
        if (i < steps.length) {
            fill.style.width  = steps[i][0] + '%';
            status.textContent = steps[i][1];
            i++;
        }
    }, 1800);
}

// ─── Abonelik ──────────────────────────────────────────────────────
async function loadSubscriptionView() {
    const [sub, packages] = await Promise.all([
        GET('/subscriptions/my-subscription'),
        GET('/subscriptions/packages'),
    ]);

    const card = document.getElementById('currentSubCard');
    if (!sub || sub.status === 'no_subscription') {
        card.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:1rem">Aktif abonelik bulunmuyor.</p>';
    } else {
        card.innerHTML = `
            <div class="sub-info-row"><span>Paket</span><strong>${escHtml(sub.package||'—')}</strong></div>
            <div class="sub-info-row"><span>Durum</span>
                <strong class="tag ${sub.status==='active'?'positive':'info'}" style="padding:3px 10px">
                    ${sub.status==='active'?'Aktif':sub.status}
                </strong>
            </div>
            <div class="sub-info-row"><span>Bitiş Tarihi</span>
                <strong>${sub.end_date ? new Date(sub.end_date).toLocaleDateString('tr-TR') : '—'}</strong>
            </div>
            <div class="sub-info-row"><span>AI Çağrılar</span>
                <strong>${sub.ai_calls_used??0} / ${sub.ai_calls_limit??'∞'}</strong>
            </div>
            <div class="sub-info-row"><span>Raporlar</span>
                <strong>${sub.reports_used??0} / ${sub.reports_limit??'∞'}</strong>
            </div>
            <div style="margin-top:1rem">
                <button class="btn-outline-primary" onclick="document.getElementById('changePasswordModal').classList.add('active'); lucide.createIcons()">
                    <i data-lucide="key"></i> Şifre Değiştir
                </button>
            </div>`;
    }

    const grid = document.getElementById('packagesGrid');
    if (!packages?.length) {
        grid.innerHTML = '<p class="text-muted">Paket bulunamadı.</p>'; return;
    }
    grid.innerHTML = packages.map(p => `
        <div class="package-card">
            <h3>${escHtml(p.name)}</h3>
            <p class="package-price">₺${parseFloat(p.price).toLocaleString('tr-TR')}<span> /ay</span></p>
            <p class="package-desc">${escHtml(p.description||'')}</p>
            <ul class="package-features">
                <li><i data-lucide="check"></i> ${p.max_companies} şirket</li>
                <li><i data-lucide="check"></i> ${p.max_reports_per_month} rapor / ay</li>
                <li><i data-lucide="check"></i> ${p.max_ai_calls_per_month} AI çağrı / ay</li>
                ${p.features?.ocr ? '<li><i data-lucide="check"></i> OCR Destekli</li>' : ''}
                ${p.features?.priority_support ? '<li><i data-lucide="check"></i> Öncelikli Destek</li>' : ''}
            </ul>
            <button class="btn-primary full-width" onclick="requestPurchase(${p.id},'${escAttr(p.name)}')">
                Satın Al
            </button>
        </div>
    `).join('');
    lucide.createIcons();
}

async function requestPurchase(packageId, packageName) {
    const res = await POST('/subscriptions/purchase', { package_id: packageId });
    if (!res) return;
    if (res.ok) {
        toast(`"${packageName}" paketi başarıyla aktif edildi.`, 'success');
        loadSubscriptionView();
    } else {
        const err = await res.json().catch(() => ({}));
        toast(err.detail || 'Talep oluşturulamadı.', 'error');
    }
}

// ─── Admin Paneli ──────────────────────────────────────────────────
let adminRequestsPage = 1;
let adminUsersPage    = 1;
let adminLogsPage     = 1;

// Cache for enriching purchase requests with user/package names
let _adminUserCache    = {};
let _adminPackageCache = {};

async function loadAdminView() {
    // Pre-fetch users and packages for name resolution
    const [usersData, pkgData] = await Promise.all([
        GET('/admin/users?page=1&page_size=200'),
        GET('/subscriptions/packages'),
    ]);
    if (usersData?.items) usersData.items.forEach(u => { _adminUserCache[u.id] = u; });
    if (pkgData) pkgData.forEach(p => { _adminPackageCache[p.id] = p; });

    // Load the active tab (requests by default)
    loadAdminRequests();
}

function switchAdminTab(tab, btn) {
    document.querySelectorAll('.admin-tab-pane').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.admin-tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`admin-tab-${tab}`).style.display = 'block';
    btn.classList.add('active');
    lucide.createIcons();
    if (tab === 'requests') loadAdminRequests();
    if (tab === 'users')    loadAdminUsers();
    if (tab === 'stats')    loadAdminStats();
    if (tab === 'logs')     loadAdminLogs();
}

async function loadAdminRequests() {
    const data = await GET(`/admin/purchase-requests?page=${adminRequestsPage}&page_size=20&status_filter=pending`);
    const tbody = document.getElementById('adminRequestsBody');
    if (!data?.items?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Bekleyen paket isteği yok.</td></tr>';
        document.getElementById('adminPagination').innerHTML = '';
        return;
    }
    tbody.innerHTML = data.items.map(r => {
        const user = _adminUserCache[r.user_id];
        const pkg  = _adminPackageCache[r.package_id];
        return `
        <tr>
            <td>
                <div class="company-cell">
                    <div class="company-logo">${(user?.full_name||'?')[0].toUpperCase()}</div>
                    <div>
                        <div style="font-weight:600;font-size:.88rem">${escHtml(user?.full_name||r.user_id)}</div>
                        <div style="font-size:.75rem;color:var(--text-muted)">${escHtml(user?.email||'')}</div>
                    </div>
                </div>
            </td>
            <td><strong>${escHtml(pkg?.name||String(r.package_id))}</strong>
                ${pkg ? `<div style="font-size:.75rem;color:var(--text-muted)">₺${parseFloat(pkg.price).toLocaleString('tr-TR')}/ay</div>` : ''}
            </td>
            <td>${new Date(r.created_at).toLocaleDateString('tr-TR')}</td>
            <td><span class="tag info">${r.status}</span></td>
            <td>
                <div style="display:flex;gap:4px">
                    <button class="action-btn" title="Onayla" onclick="reviewPurchaseRequest(${r.id},'approved')" style="color:var(--success)">
                        <i data-lucide="check-circle"></i>
                    </button>
                    <button class="action-btn danger-btn" title="Reddet" onclick="reviewPurchaseRequest(${r.id},'rejected')">
                        <i data-lucide="x-circle"></i>
                    </button>
                </div>
            </td>
        </tr>`;
    }).join('');
    lucide.createIcons();
    renderPagination('adminPagination', data.page, data.pages, p => {
        adminRequestsPage = p; loadAdminRequests();
    });
}

async function loadAdminUsers() {
    const data = await GET(`/admin/users?page=${adminUsersPage}&page_size=20`);
    const tbody = document.getElementById('adminUsersBody');
    if (!data?.items?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Kullanıcı bulunamadı.</td></tr>';
        document.getElementById('adminUsersPagination').innerHTML = '';
        return;
    }
    tbody.innerHTML = data.items.map(u => `
        <tr>
            <td><div class="company-cell">
                <div class="company-logo" style="background:${strColor(u.full_name)}">${u.full_name[0].toUpperCase()}</div>
                <span>${escHtml(u.full_name)}</span>
            </div></td>
            <td>${escHtml(u.email)}</td>
            <td><span class="tag ${u.role==='admin'?'positive':'info'}">${u.role}</span></td>
            <td>${new Date(u.created_at).toLocaleDateString('tr-TR')}</td>
            <td>
                <button class="action-btn danger-btn" title="Kullanıcıyı Sil"
                    onclick="deleteAdminUser(${u.id},'${escAttr(u.full_name)}')">
                    <i data-lucide="trash-2"></i>
                </button>
            </td>
        </tr>
    `).join('');
    lucide.createIcons();
    renderPagination('adminUsersPagination', data.page, data.pages, p => {
        adminUsersPage = p; loadAdminUsers();
    });
}

async function deleteAdminUser(id, name) {
    if (!confirm(`"${name}" kullanıcısını silmek istediğinize emin misiniz?`)) return;
    const res = await DELETE(`/admin/users/${id}`);
    if (res?.status === 204) {
        toast('Kullanıcı silindi.', 'success');
        loadAdminUsers();
    } else {
        const err = await res?.json().catch(() => ({}));
        toast(err.detail || 'Silme başarısız.', 'error');
    }
}

async function loadAdminStats() {
    const [stats, aiStats] = await Promise.all([
        GET('/admin/stats/platform'),
        GET('/admin/stats/ai'),
    ]);
    const grid = document.getElementById('adminStatsGrid');
    if (!stats) { grid.innerHTML = '<p class="text-muted">İstatistikler yüklenemedi.</p>'; return; }
    grid.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon purple"><i data-lucide="users"></i></div>
            <div class="stat-details">
                <h3>Kullanıcılar</h3>
                <p class="stat-value">${stats.users?.total ?? 0}</p>
                <span class="stat-trend">${stats.users?.active ?? 0} aktif</span>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon blue"><i data-lucide="building-2"></i></div>
            <div class="stat-details">
                <h3>Şirketler</h3>
                <p class="stat-value">${stats.companies?.total ?? 0}</p>
                <span class="stat-trend">Toplam kayıtlı</span>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon orange"><i data-lucide="file-text"></i></div>
            <div class="stat-details">
                <h3>Raporlar</h3>
                <p class="stat-value">${stats.reports?.total ?? 0}</p>
                <span class="stat-trend">${stats.reports?.ai_generated ?? 0} AI üretimi</span>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon green"><i data-lucide="credit-card"></i></div>
            <div class="stat-details">
                <h3>Aktif Abonelik</h3>
                <p class="stat-value">${stats.subscriptions?.active ?? 0}</p>
                <span class="stat-trend">${stats.subscriptions?.pending_purchases ?? 0} bekleyen</span>
            </div>
        </div>
        ${aiStats ? `
        <div class="stat-card">
            <div class="stat-icon blue"><i data-lucide="cpu"></i></div>
            <div class="stat-details">
                <h3>AI Çağrıları</h3>
                <p class="stat-value">${aiStats.total_calls ?? 0}</p>
                <span class="stat-trend">%${aiStats.success_rate ?? 0} başarı</span>
            </div>
        </div>
        <div class="stat-card">
            <div class="stat-icon orange"><i data-lucide="zap"></i></div>
            <div class="stat-details">
                <h3>Toplam Token</h3>
                <p class="stat-value">${(aiStats.total_tokens_used ?? 0).toLocaleString('tr-TR')}</p>
                <span class="stat-trend">Ort. ${aiStats.avg_duration_ms ?? 0} ms</span>
            </div>
        </div>` : ''}
    `;
    lucide.createIcons();
}

async function loadAdminLogs() {
    const data = await GET(`/admin/logs/audit?page=${adminLogsPage}&page_size=30`);
    const tbody = document.getElementById('adminLogsBody');
    if (!data?.items?.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Log bulunamadı.</td></tr>';
        document.getElementById('adminLogsPagination').innerHTML = '';
        return;
    }
    tbody.innerHTML = data.items.map(l => `
        <tr>
            <td style="font-size:.78rem;white-space:nowrap">${l.timestamp ? new Date(l.timestamp).toLocaleString('tr-TR') : '—'}</td>
            <td style="font-size:.82rem">${escHtml(String(l.user_id||'—'))}</td>
            <td><span class="tag info" style="font-size:.72rem">${escHtml(l.action||'—')}</span></td>
            <td style="font-size:.82rem">${escHtml(l.resource_type||'—')}</td>
            <td style="font-size:.75rem;color:var(--text-muted);max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                ${escHtml(l.details||'')}
            </td>
        </tr>
    `).join('');
    lucide.createIcons();
    renderPagination('adminLogsPagination', data.page, data.pages, p => {
        adminLogsPage = p; loadAdminLogs();
    });
}

async function reviewPurchaseRequest(id, status) {
    if (!confirm(`Talebi ${status === 'approved' ? 'onaylamak' : 'reddetmek'} istediğinize emin misiniz?`)) return;
    const res = await POST(`/admin/purchase-requests/${id}/review`, { status: status, admin_note: '' });
    if (res && res.ok) {
        toast(`Talep ${status === 'approved' ? 'onaylandı' : 'reddedildi'}.`, 'success');
        loadAdminView();
    } else {
        const err = await res?.json().catch(() => ({}));
        toast(err.detail || 'İşlem başarısız.', 'error');
    }
}

// ─── Bildirimler ───────────────────────────────────────────────────
async function loadNotifications() {
    const data = await GET('/notifications?page=1&page_size=30&unread_only=false');
    if (!data) return;

    const unread = (data.items||[]).filter(n => !n.is_read).length;
    const badge  = document.getElementById('notifBadge');
    badge.style.display = unread ? 'flex' : 'none';
    if (unread) badge.textContent = unread > 9 ? '9+' : unread;

    const list = document.getElementById('notifList');
    if (!data.items?.length) {
        list.innerHTML = '<p class="notif-empty">Bildirim yok.</p>'; return;
    }
    list.innerHTML = data.items.map(n => `
        <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="readNotif(${n.id}, this)">
            <p class="notif-title">${escHtml(n.title)}</p>
            <p class="notif-body">${escHtml(n.body)}</p>
            <p class="notif-time">${new Date(n.created_at).toLocaleString('tr-TR')}</p>
        </div>
    `).join('');
}

function toggleNotifications(e) {
    e?.stopPropagation();
    const p = document.getElementById('notifPanel');
    const isHidden = p.style.display === 'none' || !p.style.display;
    p.style.display = isHidden ? 'block' : 'none';
    if (isHidden) loadNotifications();
}

async function readNotif(id, el) {
    await http(`/notifications/${id}/read`, { method: 'POST' });
    el.classList.remove('unread');
    loadNotifications();
}

async function markAllRead() {
    await http('/notifications/read-all', { method: 'POST' });
    toast('Tüm bildirimler okundu işaretlendi.', 'info');
    loadNotifications();
}

// ─── Modal Yönetimi ────────────────────────────────────────────────
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    if (id === 'uploadModal') resetDropZone();
}

function modalBackdropClose(e, modalId) {
    if (e.target === document.getElementById(modalId)) closeModal(modalId);
}

// ─── Global Arama ──────────────────────────────────────────────────
let _searchTimer = null;
function handleGlobalSearch(val) {
    clearTimeout(_searchTimer);
    _searchTimer = setTimeout(() => {
        const active = [...VIEWS].find(v => document.getElementById(`view-${v}`).style.display !== 'none');
        if (active === 'companies') { companiesPage = 1; loadCompanies(val); }
        if (active === 'reports') {
            // Şirket adı araması için filter company'yi güncelle
            const match = _companyCache.find(c => c.name.toLowerCase().includes(val.toLowerCase()));
            if (match) { document.getElementById('filterCompany').value = match.id; loadAllReports(); }
        }
    }, 300);
}

// ─── Sayfalama ─────────────────────────────────────────────────────
function renderPagination(containerId, page, pages, onPage) {
    const el = document.getElementById(containerId);
    if (!el) return;
    if (!pages || pages <= 1) { el.innerHTML = ''; return; }

    let html = '';
    if (page > 1) html += `<button class="page-btn" onclick="_pg(${page-1})">‹ Önceki</button>`;
    const start = Math.max(1, page-2), end = Math.min(pages, page+2);
    for (let i = start; i <= end; i++) {
        html += `<button class="page-btn ${i===page?'active':''}" onclick="_pg(${i})">${i}</button>`;
    }
    if (page < pages) html += `<button class="page-btn" onclick="_pg(${page+1})">Sonraki ›</button>`;
    el.innerHTML = html;
    el._onPage = onPage;

    window._pg = p => {
        if (el._onPage) el._onPage(p);
    };
}

// ─── Yardımcılar ───────────────────────────────────────────────────
function reportTypeLabel(t) {
    return { balance_sheet:'Bilanço', income_statement:'Gelir Tablosu',
             cash_flow:'Nakit Akışı', combined:'Kombine' }[t] || t;
}
function periodLabel(p) {
    return { annual:'Yıllık', q1:'Ç1', q2:'Ç2', q3:'Ç3', q4:'Ç4' }[p] || p;
}
function escHtml(s) {
    if (!s) return '';
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
                    .replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}
function escAttr(s) {
    return String(s||'').replace(/'/g,"\\'").replace(/"/g,'&quot;');
}
function strColor(str) {
    let h = 0;
    for (const c of (str||'')) h = c.charCodeAt(0) + ((h<<5)-h);
    return `hsl(${Math.abs(h)%360},45%,35%)`;
}

// ─── Premium Modal ─────────────────────────────────────────────────
async function showPremiumModal() {
    document.getElementById('premiumModal').classList.add('active');
    lucide.createIcons();
    const packages = await GET('/subscriptions/packages');
    const grid = document.getElementById('premiumPackagesGrid');
    if (!packages?.length) { grid.innerHTML = '<p class="text-muted">Paket bulunamadı.</p>'; return; }
    grid.innerHTML = packages.map(p => `
        <div class="package-card">
            <h3>${escHtml(p.name)}</h3>
            <p class="package-price">₺${parseFloat(p.price).toLocaleString('tr-TR')}<span> /ay</span></p>
            <p class="package-desc">${escHtml(p.description||'')}</p>
            <ul class="package-features">
                <li><i data-lucide="check"></i> ${p.max_companies} şirket</li>
                <li><i data-lucide="check"></i> ${p.max_reports_per_month} rapor/ay</li>
                <li><i data-lucide="check"></i> ${p.max_ai_calls_per_month} AI çağrı/ay</li>
                ${p.features?.ocr ? '<li><i data-lucide="check"></i> OCR Destekli</li>' : ''}
            </ul>
            <button class="btn-primary full-width"
                onclick="requestPurchase(${p.id},'${escAttr(p.name)}');closeModal('premiumModal')">
                <i data-lucide="shopping-cart"></i> Talep Oluştur
            </button>
        </div>
    `).join('');
    lucide.createIcons();
}

// ─── Dark Mode Toggle (O2) ─────────────────────────────────────────
function toggleDarkMode() {
    const isLight = document.body.classList.toggle('light-mode');
    const btn = document.getElementById('darkModeBtn');
    btn.innerHTML = isLight ? '<i data-lucide="moon"></i>' : '<i data-lucide="sun"></i>';
    localStorage.setItem('sf_theme', isLight ? 'light' : 'dark');
    lucide.createIcons();
}

// ─── Click-outside kapanma ─────────────────────────────────────────
document.addEventListener('click', e => {
    // Bildirim paneli
    const panel = document.getElementById('notifPanel');
    const btn   = document.getElementById('notifBtn');
    if (panel && panel.style.display !== 'none') {
        if (!panel.contains(e.target) && !btn.contains(e.target)) {
            panel.style.display = 'none';
        }
    }
});

// Bildirim butonuna click listener
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('notifBtn')?.addEventListener('click', e => toggleNotifications(e));
});

// ─── Uygulama Başlat ───────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    // Restore theme preference
    if (localStorage.getItem('sf_theme') === 'light') {
        document.body.classList.add('light-mode');
        const btn = document.getElementById('darkModeBtn');
        if (btn) { btn.innerHTML = '<i data-lucide="moon"></i>'; }
    }

    if (Token.access && Token.user) {
        // Token'ı API ile doğrula
        fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${Token.access}` }
        }).then(r => {
            if (r.ok) return r.json();
            return null;
        }).then(user => {
            if (user) {
                Token.save(Token.access, Token.refresh, user);
                initApp(user);
            } else {
                Token.clear();
                showAuth();
                lucide.createIcons();
            }
        }).catch(() => {
            showAuth();
            lucide.createIcons();
        });
    } else {
        showAuth();
        lucide.createIcons();
    }
});

// ─── Rapor Detay Modal & Grafikler ──────────────────────────────────
let currentRevenueChart = null;
let currentAssetChart = null;

async function viewReportDetail(reportId) {
    const r = await GET(`/financial/reports/${reportId}`);
    if (!r) return;

    document.getElementById('reportDetailTitle').textContent = `${r.company.name} - ${r.fiscal_year} Raporu`;
    document.getElementById('reportDetailModal').classList.add('active');
    
    // Veri sekmesini doldur
    renderReportData(r);
    
    // AI sekmesini hazırla
    renderReportAiAnalysis(r);
    
    // Download butonu
    document.getElementById('downloadPptxBtn').onclick = () => downloadPptx(r.id);
    
    switchReportTab('data', document.querySelector('.report-detail-tabs button'));
    lucide.createIcons();
}

function switchReportTab(tab, btn) {
    document.querySelectorAll('.report-tab-pane').forEach(p => p.style.display = 'none');
    document.querySelectorAll('.report-detail-tabs button').forEach(b => b.classList.remove('active'));
    document.getElementById(`report-tab-${tab}`).style.display = 'block';
    btn.classList.add('active');
}

function renderReportData(r) {
    const el = document.getElementById('reportDataContent');
    el.innerHTML = `
        <div class="stats-grid">
            <div class="stat-card"><h3>Toplam Varlık</h3><p>${fmtNum(r.total_assets)}</p></div>
            <div class="stat-card"><h3>Toplam Borç</h3><p>${fmtNum(r.total_liabilities)}</p></div>
            <div class="stat-card"><h3>Gelir</h3><p>${fmtNum(r.revenue)}</p></div>
            <div class="stat-card"><h3>Net Kar</h3><p>${fmtNum(r.net_income)}</p></div>
        </div>
        <div style="margin-top: 1rem;">
            <p><strong>Rapor Türü:</strong> ${reportTypeLabel(r.report_type)}</p>
            <p><strong>Dönem:</strong> ${periodLabel(r.period)}</p>
            <p><strong>Oluşturulma:</strong> ${new Date(r.created_at).toLocaleString('tr-TR')}</p>
        </div>
    `;
}

function renderReportAiAnalysis(r) {
    let ratios = {};
    try { ratios = typeof r.ai_ratios === 'string' ? JSON.parse(r.ai_ratios) : (r.ai_ratios || {}); } catch(e) {}
    
    const assessment = document.getElementById('aiOverallAssessment');
    assessment.textContent = ratios.overall_assessment || 'Bu rapor için henüz AI analizi yapılmamış.';
    
    const ratiosGrid = document.getElementById('aiRatiosGrid');
    ratiosGrid.innerHTML = '';
    
    if (ratios.liquidity) {
        ratiosGrid.innerHTML += renderRatioCard('Likidite', [
            ['Cari Oran', ratios.liquidity.current_ratio],
            ['Asit-Test', ratios.liquidity.quick_ratio]
        ]);
    }
    if (ratios.leverage) {
        ratiosGrid.innerHTML += renderRatioCard('Kaldıraç', [
            ['Borç/Varlık', ratios.leverage.debt_to_assets],
            ['Borç/Özkaynak', ratios.leverage.debt_to_equity]
        ]);
    }
    if (ratios.profitability) {
        ratiosGrid.innerHTML += renderRatioCard('Kârlılık', [
            ['Net Marj', pct(ratios.profitability.net_margin)],
            ['ROE', pct(ratios.profitability.roe)]
        ]);
    }

    // Grafiklerin çizimi
    if (ratios.chart_data) {
        setTimeout(() => renderCharts(ratios.chart_data), 100);
    }
}

function renderRatioCard(title, items) {
    return `
        <div class="card" style="padding: 1rem;">
            <h4 style="margin-bottom: 0.5rem; color: var(--secondary);">${title}</h4>
            ${items.map(it => `
                <div style="display:flex; justify-content:space-between; margin-bottom: 0.25rem;">
                    <span style="font-size: 0.85rem;">${it[0]}</span>
                    <strong style="font-size: 0.9rem;">${it[1] ?? '—'}</strong>
                </div>
            `).join('')}
        </div>
    `;
}

function renderCharts(chartData) {
    if (currentRevenueChart) currentRevenueChart.destroy();
    if (currentAssetChart) currentAssetChart.destroy();

    const revCtx = document.getElementById('revenueChart').getContext('2d');
    const assetCtx = document.getElementById('assetChart').getContext('2d');

    const revData = chartData.revenue_expense || {};
    currentRevenueChart = new Chart(revCtx, {
        type: 'bar',
        data: {
            labels: revData.labels || [],
            datasets: [
                {
                    label: 'Tutar',
                    data: revData.revenue || [],
                    backgroundColor: 'rgba(46, 134, 171, 0.7)',
                    borderColor: '#2E86AB',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'Gelir & Gider Analizi' } }
        }
    });

    const assetData = chartData.asset_structure || {};
    currentAssetChart = new Chart(assetCtx, {
        type: 'doughnut',
        data: {
            labels: assetData.labels || [],
            datasets: [{
                data: assetData.values || [],
                backgroundColor: [
                    '#2E86AB', '#A239CA', '#4717F6', '#E74C3C', '#27AE60'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: { title: { display: true, text: 'Varlık & Özkaynak Yapısı' } }
        }
    });
}

function fmtNum(n) {
    if (n === null || n === undefined) return '—';
    return new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY' }).format(n);
}
function pct(n) {
    if (n === null || n === undefined) return '—';
    return (n * 100).toFixed(1) + '%';
}
