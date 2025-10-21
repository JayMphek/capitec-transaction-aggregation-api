const API_BASE = 'http://localhost:8000/api/v1';
let categoryChart, trendsChart;

// Initialize dashboard
async function init() {
    await loadCustomers();
    await loadDashboard();
}

// Load customers
async function loadCustomers() {
    try {
        const response = await fetch(`${API_BASE}/customers`);
        const data = await response.json();

        const select = document.getElementById('customerSelect');
        select.innerHTML = data.customers.map(id =>
            `<option value="${id}">${id}</option>`
        ).join('');
    } catch (error) {
        showError('Failed to load customers: ' + error.message);
    }
}

// Format date for API (without milliseconds)
function formatDateForAPI(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}:${seconds}`;
}

// Load dashboard data
async function loadDashboard() {
    const customerId = document.getElementById('customerSelect').value;
    const days = document.getElementById('periodSelect').value;
    const category = document.getElementById('categorySelect').value;

    if (!customerId) return;

    showLoading();

    try {
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);
        const startDateStr = formatDateForAPI(startDate);

        // Load summary
        const summaryUrl = `${API_BASE}/summary?customer_id=${customerId}&start_date=${startDateStr}`;
        console.log('Fetching summary:', summaryUrl);
        const summaryResponse = await fetch(summaryUrl);

        if (!summaryResponse.ok) {
            const errorText = await summaryResponse.text();
            throw new Error(`Summary API error: ${summaryResponse.status} - ${errorText}`);
        }

        const summary = await summaryResponse.json();

        // Load categories
        const categoriesUrl = `${API_BASE}/categories?customer_id=${customerId}&start_date=${startDateStr}`;
        console.log('Fetching categories:', categoriesUrl);
        const categoriesResponse = await fetch(categoriesUrl);

        if (!categoriesResponse.ok) {
            const errorText = await categoriesResponse.text();
            throw new Error(`Categories API error: ${categoriesResponse.status} - ${errorText}`);
        }

        const categories = await categoriesResponse.json();

        // Load trends
        const trendsUrl = `${API_BASE}/trends?customer_id=${customerId}&months=6`;
        console.log('Fetching trends:', trendsUrl);
        const trendsResponse = await fetch(trendsUrl);

        if (!trendsResponse.ok) {
            const errorText = await trendsResponse.text();
            throw new Error(`Trends API error: ${trendsResponse.status} - ${errorText}`);
        }

        const trends = await trendsResponse.json();

        // Load transactions
        let transactionsUrl = `${API_BASE}/transactions?customer_id=${customerId}&start_date=${startDateStr}&limit=20`;
        if (category) {
            transactionsUrl += `&category=${category}`;
        }
        console.log('Fetching transactions:', transactionsUrl);
        const transactionsResponse = await fetch(transactionsUrl);

        if (!transactionsResponse.ok) {
            const errorText = await transactionsResponse.text();
            throw new Error(`Transactions API error: ${transactionsResponse.status} - ${errorText}`);
        }

        const transactions = await transactionsResponse.json();

        // Update UI
        updateStats(summary);
        updateCategoryChart(categories);
        updateTrendsChart(trends);
        updateTransactionsTable(transactions);

        hideLoading();
    } catch (error) {
        console.error('Dashboard error:', error);
        showError('Failed to load dashboard: ' + error.message);
    }
}

// Update statistics
function updateStats(summary) {
    document.getElementById('totalTransactions').textContent = summary.total_transactions.toLocaleString();
    document.getElementById('totalCredits').textContent = 'R' + summary.total_credits.toLocaleString('en-ZA', { minimumFractionDigits: 2 });
    document.getElementById('totalDebits').textContent = 'R' + summary.total_debits.toLocaleString('en-ZA', { minimumFractionDigits: 2 });
    document.getElementById('netAmount').textContent = 'R' + summary.net_amount.toLocaleString('en-ZA', { minimumFractionDigits: 2 });

    // Update net amount card styling based on positive/negative
    const netCard = document.getElementById('netAmount').closest('.stat-card');
    const netChange = document.getElementById('netChange');
    if (summary.net_amount >= 0) {
        netCard.classList.add('positive');
        netCard.classList.remove('negative');
        netChange.textContent = '✓ Positive balance';
    } else {
        netCard.classList.add('negative');
        netCard.classList.remove('positive');
        netChange.textContent = '⚠ Negative balance';
    }
}

// Update category chart
function updateCategoryChart(categories) {
    const ctx = document.getElementById('categoryChart');

    if (categoryChart) {
        categoryChart.destroy();
    }

    const colors = [
        '#0066CC', '#E30613', '#00A651', '#FFC107',
        '#004080', '#9B1B29', '#007A3D', '#FF9800',
        '#0052A3', '#C41E3A', '#00662B', '#F57C00'
    ];

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.category),
            datasets: [{
                data: categories.map(c => c.total_amount),
                backgroundColor: colors,
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            return label + ': R' + value.toLocaleString('en-ZA', { minimumFractionDigits: 2 });
                        }
                    }
                }
            }
        }
    });
}

// Update trends chart
function updateTrendsChart(trends) {
    const ctx = document.getElementById('trendsChart');

    if (trendsChart) {
        trendsChart.destroy();
    }

    trendsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: trends.map(t => `${t.month.substring(0, 3)} ${t.year}`),
            datasets: [
                {
                    label: 'Income',
                    data: trends.map(t => t.total_credits),
                    borderColor: '#00A651',
                    backgroundColor: 'rgba(0, 166, 81, 0.1)',
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#00A651'
                },
                {
                    label: 'Expenses',
                    data: trends.map(t => t.total_debits),
                    borderColor: '#E30613',
                    backgroundColor: 'rgba(227, 6, 19, 0.1)',
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 4,
                    pointBackgroundColor: '#E30613'
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                tooltip: {
                    callbacks: {
                        label: function (context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            return label + ': R' + value.toLocaleString('en-ZA', { minimumFractionDigits: 2 });
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function (value) {
                            return 'R' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Update transactions table
function updateTransactionsTable(transactions) {
    const tbody = document.getElementById('transactionsBody');

    tbody.innerHTML = transactions.map(t => `
        <tr>
            <td>${new Date(t.timestamp).toLocaleDateString('en-ZA')}</td>
            <td>${t.description}</td>
            <td>${t.category}</td>
            <td>${t.merchant || '-'}</td>
            <td><span class="badge ${t.type}">${t.type}</span></td>
            <td><strong>R${t.amount.toLocaleString('en-ZA', { minimumFractionDigits: 2 })}</strong></td>
        </tr>
    `).join('');
}

// Show loading
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}

// Hide loading
function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
}

// Show error
function showError(message) {
    document.getElementById('error').textContent = message;
    document.getElementById('error').style.display = 'block';
    document.getElementById('loading').style.display = 'none';
    document.getElementById('dashboard').style.display = 'none';
}

// Initialize on page load
init();