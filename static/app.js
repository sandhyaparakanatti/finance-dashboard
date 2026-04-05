// Global State
let currentPage = 1;
let totalPages = 1;
let searchTimeout = null;

// ==========================================
// TOAST NOTIFICATIONS
// ==========================================
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = '<i class="fas fa-check-circle"></i>';
    if(type === 'error') icon = '<i class="fas fa-exclamation-circle"></i>';
    
    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// ==========================================
// DASHBOARD LOGIC (Chart.js Integration)
// ==========================================
async function loadDashboardData() {
    try {
        const response = await fetch('/api/summary');
        if (!response.ok) throw new Error("Unauthorized");
        
        const data = await response.json();
        
        // Update stats
        updateStat('total-income', data.total_income);
        updateStat('total-expense', data.total_expense);
        updateStat('net-balance', data.net_balance, true);
        
        // Render Charts
        renderCategoryChart(data.category_data);
        renderBalanceChart(data.total_income, data.total_expense);
        
        // Update Recent Table
        const tbody = document.getElementById('recent-table-body');
        if (tbody) {
            tbody.innerHTML = data.recent.map(r => `
                <tr>
                    <td>${r.date}</td>
                    <td><span class="badge" style="background:#e2e8f0; color:#475569;">${r.category}</span></td>
                    <td><span class="type-indicator ${r.type}">${r.type}</span></td>
                    <td class="amount-${r.type}">$${r.amount.toFixed(2)}</td>
                </tr>
            `).join('') || '<tr><td colspan="4" class="text-center">No recent records.</td></tr>';
        }
    } catch (error) {
        console.error("Dashboard error:", error);
    }
}

function updateStat(id, val, isBalance = false) {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerText = `$${val.toLocaleString()}`;
    if(isBalance) el.style.color = val >= 0 ? 'var(--success-color)' : 'var(--error-color)';
}

function renderCategoryChart(catData) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(catData),
            datasets: [{
                data: Object.values(catData),
                backgroundColor: ['#4361ee', '#4cc9f0', '#ef476f', '#ffd166', '#7209b7', '#f72585']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom' } }
        }
    });
}

function renderBalanceChart(income, expense) {
    const ctx = document.getElementById('balanceChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Income', 'Expense'],
            datasets: [{
                label: 'USD ($)',
                data: [income, expense],
                backgroundColor: ['#4cc9f0', '#ef476f'],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } },
            plugins: { legend: { display: false } }
        }
    });
}

// ==========================================
// RECORDS MANAGEMENT (Pagination/Filtering)
// ==========================================
async function loadRecordsData() {
    const tableBody = document.getElementById('records-table-body');
    if (!tableBody) return;
    
    const type = document.getElementById('filter-type')?.value;
    const category = document.getElementById('filter-category')?.value;
    const search = document.getElementById('record-search')?.value;
    
    let url = `/api/records?page=${currentPage}&per_page=10`;
    if (type) url += `&type=${type}`;
    if (category) url += `&category=${category}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    
    try {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="spinner"></div> Loading...</td></tr>';
        
        const response = await fetch(url);
        const data = await response.json();
        
        totalPages = data.total_pages;
        updatePaginationUI(data);
        
        tableBody.innerHTML = data.records.map(r => `
            <tr>
                <td>${r.date}</td>
                <td title="${r.description}">${r.description || '-'}</td>
                <td><span class="badge" style="background:#e2e8f0; color:#475569;">${r.category}</span></td>
                <td><span class="badge" style="background:${r.type === 'income' ? 'rgba(76,201,240,0.1)' : 'rgba(239,71,111,0.1)'}; color:${r.type === 'income' ? 'var(--success-color)' : 'var(--error-color)'}">${r.type}</span></td>
                <td class="font-bold">$${r.amount.toFixed(2)}</td>
                ${USER_ROLE === 'Admin' ? `
                    <td>
                        <div style="display:flex; gap:5px;">
                            <a href="/edit-record/${r.id}" class="btn btn-sm btn-outline btn-primary" title="Edit">
                                <i class="fas fa-edit"></i>
                            </a>
                            <button class="btn btn-sm btn-outline btn-danger" onclick="deleteRecord(${r.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                ` : ''}
            </tr>
        `).join('') || '<tr><td colspan="6" class="text-center text-muted">No records matched your criteria.</td></tr>';
    } catch (error) {
        showToast("Error loading records.", "error");
    }
}

async function submitUpdate(event, id) {
    event.preventDefault();
    const btn = document.getElementById('update-btn');
    const loading = document.getElementById('edit-loading');
    
    const formData = {
        amount: document.getElementById('edit-amount').value,
        type: document.getElementById('edit-type').value,
        category: document.getElementById('edit-category').value,
        date: document.getElementById('edit-date').value,
        description: document.getElementById('edit-description').value
    };
    
    try {
        btn.disabled = true;
        loading.style.display = 'inline-block';
        
        const response = await fetch(`/api/records/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (response.ok) {
            showToast("Record updated successfully!");
            setTimeout(() => window.location.href = '/records', 800);
        } else {
            const resData = await response.json();
            showToast(resData.error || "Update failed.", "error");
        }
    } catch (error) {
        showToast("Network error.", "error");
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
}

function updatePaginationUI(data) {
    const info = document.getElementById('pagination-info');
    if (info) info.innerText = `Page ${data.current_page} of ${data.total_pages || 1}`;
    
    document.getElementById('prev-button')?.toggleAttribute('disabled', !data.has_prev);
    document.getElementById('next-button')?.toggleAttribute('disabled', !data.has_next);
}

function changePage(delta) {
    const next = currentPage + delta;
    if (next > 0 && next <= totalPages) {
        currentPage = next;
        loadRecordsData();
    }
}

function onSearchChange() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage = 1;
        loadRecordsData();
    }, 500);
}

// ==========================================
// FORM SUBMISSION Logic
// ==========================================
async function submitForm(event) {
    event.preventDefault();
    const btn = document.getElementById('submit-btn');
    const loading = document.getElementById('loading');
    
    const formData = {
        amount: document.getElementById('form-amount').value,
        type: document.getElementById('form-type').value,
        category: document.getElementById('form-category').value,
        date: document.getElementById('form-date').value,
        description: document.getElementById('form-description').value
    };
    
    try {
        btn.disabled = true;
        loading.style.display = 'inline-block';
        
        const response = await fetch('/api/records', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        const resData = await response.json();
        
        if (response.ok) {
            showToast("Record added successfully!");
            setTimeout(() => window.location.href = '/records', 800);
        } else {
            showToast(resData.error || "Failed to add record.", "error");
        }
    } catch (error) {
        showToast("Network error.", "error");
    } finally {
        btn.disabled = false;
        loading.style.display = 'none';
    }
}

async function deleteRecord(id) {
    if (!confirm("Are you sure you want to delete this record? This cannot be undone.")) return;
    
    try {
        const response = await fetch(`/api/records/${id}`, { method: 'DELETE' });
        if (response.ok) {
            showToast("Record deleted.");
            loadRecordsData();
        } else {
            throw new Error();
        }
    } catch (error) {
        showToast("Access denied or server error.", "error");
    }
}
