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

        // Always load full summary for total income (unfiltered)
        let summaryUrl = `${API_BASE}/summary?customer_id=${customerId}&start_date=${startDateStr}`;
        console.log('Fetching summary:', summaryUrl);
        const summaryResponse = await fetch(summaryUrl);
        
        if (!summaryResponse.ok) {
            const errorText = await summaryResponse.text();
            throw new Error(`Summary API error: ${summaryResponse.status} - ${errorText}`);
        }
        
        const fullSummary = await summaryResponse.json();

        // Load categories with filters
        let categoriesUrl = `${API_BASE}/categories?customer_id=${customerId}&start_date=${startDateStr}`;
        console.log('Fetching categories:', categoriesUrl);
        const categoriesResponse = await fetch(categoriesUrl);
        
        if (!categoriesResponse.ok) {
            const errorText = await categoriesResponse.text();
            throw new Error(`Categories API error: ${categoriesResponse.status} - ${errorText}`);
        }
        
        const categories = await categoriesResponse.json();

        // Load trends (always show full trends regardless of category filter)
        const trendsUrl = `${API_BASE}/trends?customer_id=${customerId}&months=6`;
        console.log('Fetching trends:', trendsUrl);
        const trendsResponse = await fetch(trendsUrl);
        
        if (!trendsResponse.ok) {
            const errorText = await trendsResponse.text();
            throw new Error(`Trends API error: ${trendsResponse.status} - ${errorText}`);
        }
        
        const trends = await trendsResponse.json();

        // Load transactions with filters for the table and filtered calculations
        let transactionsUrl = `${API_BASE}/transactions?customer_id=${customerId}&start_date=${startDateStr}&limit=1000`;
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

        // Calculate filtered statistics from transactions
        const filteredStats = calculateFilteredStats(transactions);

        // Combine: Keep full income, use filtered expenses
        const displayStats = {
            total_transactions: category ? filteredStats.total_transactions : fullSummary.total_transactions,
            total_credits: fullSummary.total_credits, // Always show full income
            total_debits: category ? filteredStats.total_debits : fullSummary.total_debits,
            net_amount: category ? (fullSummary.total_credits - filteredStats.total_debits) : fullSummary.net_amount
        };

        // Update UI with combined data
        updateStats(displayStats, category);
        
        // Update merchant chart title
        const merchantChartTitle = document.getElementById('merchantChartTitle');
        merchantChartTitle.textContent = category ? `🏪 Top Merchants - ${category}` : '🏪 Top Merchants';
        
        const merchantData = calculateMerchantBreakdown(transactions);
        updateMerchantChart(merchantData, category);
        updateTrendsChart(trends);
        updateTransactionsTable(transactions.slice(0, 20)); // Show top 20
        updateFilterInfo(category);
        hideLoading();
    } catch (error) {
        console.error('Dashboard error:', error);
        showError('Failed to load dashboard: ' + error.message);
    }
}

// Calculate statistics from filtered transactions
function calculateFilteredStats(transactions) {
    let totalCredits = 0;
    let totalDebits = 0;
    let totalTransactions = transactions.length;

    transactions.forEach(txn => {
        const amount = parseFloat(txn.amount);
        if (txn.type === 'credit') {
            totalCredits += amount;
        } else {
            totalDebits += amount;
        }
    });

    return {
        total_transactions: totalTransactions,
        total_credits: totalCredits,
        total_debits: totalDebits,
        net_amount: totalCredits - totalDebits
    };
}

// Calculate merchant breakdown from transactions
function calculateMerchantBreakdown(transactions) {
    const merchantMap = {};
    
    transactions.forEach(txn => {
        if (txn.type === 'debit' && txn.merchant) {
            if (!merchantMap[txn.merchant]) {
                merchantMap[txn.merchant] = {
                    merchant: txn.merchant,
                    total_amount: 0,
                    transaction_count: 0
                };
            }
            merchantMap[txn.merchant].total_amount += parseFloat(txn.amount);
            merchantMap[txn.merchant].transaction_count += 1;
        }
    });
    
    const merchantArray = Object.values(merchantMap);
    merchantArray.sort((a, b) => b.total_amount - a.total_amount);
    return merchantArray.slice(0, 10);
}

// Update filter info banner
function updateFilterInfo(category) {
    const filterInfo = document.getElementById('filterInfo');
    const filterText = document.getElementById('filterText');
    
    if (category) {
        const periodSelect = document.getElementById('periodSelect');
        const periodText = periodSelect.options[periodSelect.selectedIndex].text;
        filterText.textContent = `🔍 Filtered by: ${category} | ${periodText}`;
        filterInfo.style.display = 'flex';
    } else {
        filterInfo.style.display = 'none';
    }
}

// Clear all filters
function clearFilters() {
    document.getElementById('categorySelect').value = '';
    document.getElementById('periodSelect').value = '30';
    loadDashboard();
}

// Update statistics
function updateStats(stats, categoryFilter) {
    document.getElementById('totalTransactions').textContent = stats.total_transactions.toLocaleString();
    document.getElementById('totalCredits').textContent = 'R' + stats.total_credits.toLocaleString('en-ZA', {minimumFractionDigits: 2});
    document.getElementById('totalDebits').textContent = 'R' + stats.total_debits.toLocaleString('en-ZA', {minimumFractionDigits: 2});
    document.getElementById('netAmount').textContent = 'R' + stats.net_amount.toLocaleString('en-ZA', {minimumFractionDigits: 2});
    
    // Update labels based on filter
    const periodSelect = document.getElementById('periodSelect');
    const periodText = periodSelect.options[periodSelect.selectedIndex].text;
    
    // Update card titles and descriptions
    if (categoryFilter) {
        document.getElementById('totalTransactionsLabel').textContent = `${categoryFilter} Transactions`;
        document.getElementById('totalCreditsLabel').textContent = 'Total Income'; // Always show full income
        document.getElementById('totalDebitsLabel').textContent = `${categoryFilter} Expenses`;
        document.getElementById('netAmountLabel').textContent = 'Net Amount';
        
        document.getElementById('totalTransactionsChange').textContent = `${periodText}`;
        document.getElementById('totalCreditsChange').textContent = 'All categories'; // Clarify this is total
        document.getElementById('totalDebitsChange').textContent = `${categoryFilter} only`;
    } else {
        document.getElementById('totalTransactionsLabel').textContent = 'Total Transactions';
        document.getElementById('totalCreditsLabel').textContent = 'Total Income';
        document.getElementById('totalDebitsLabel').textContent = 'Total Expenses';
        document.getElementById('netAmountLabel').textContent = 'Net Amount';
        
        document.getElementById('totalTransactionsChange').textContent = periodText;
        document.getElementById('totalCreditsChange').textContent = 'Credits received';
        document.getElementById('totalDebitsChange').textContent = 'Debits made';
    }
    
    // Update net amount card styling based on positive/negative
    const netCard = document.getElementById('netAmount').closest('.stat-card');
    const netChange = document.getElementById('netChange');
    if (stats.net_amount >= 0) {
        netCard.classList.add('positive');
        netCard.classList.remove('negative');
        if (categoryFilter) {
            netChange.textContent = `After ${categoryFilter} expenses`;
        } else {
            netChange.textContent = '✓ Positive balance';
        }
    } else {
        netCard.classList.add('negative');
        netCard.classList.remove('positive');
        if (categoryFilter) {
            netChange.textContent = `After ${categoryFilter} expenses`;
        } else {
            netChange.textContent = '⚠ Negative balance';
        }
    }
}

// Update merchant chart (formerly category chart)
function updateMerchantChart(merchantData, categoryFilter) {
    const ctx = document.getElementById('categoryChart');
    
    if (categoryChart) {
        categoryChart.destroy();
    }

    const colors = [
        '#0066CC', '#E30613', '#00A651', '#FFC107',
        '#004080', '#9B1B29', '#007A3D', '#FF9800',
        '#0052A3', '#C41E3A', '#00662B', '#F57C00'
    ];

    const chartTitle = categoryFilter ? `Top Merchants - ${categoryFilter}` : 'Top Merchants';

    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: merchantData.map(m => m.merchant),
            datasets: [{
                data: merchantData.map(m => m.total_amount),
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
                title: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: R${value.toLocaleString('en-ZA', {minimumFractionDigits: 2})} (${percentage}%)`;
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
                        label: function(context) {
                            const label = context.dataset.label || '';
                            const value = context.parsed.y || 0;
                            return label + ': R' + value.toLocaleString('en-ZA', {minimumFractionDigits: 2});
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
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
            <td><strong>R${t.amount.toLocaleString('en-ZA', {minimumFractionDigits: 2})}</strong></td>
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