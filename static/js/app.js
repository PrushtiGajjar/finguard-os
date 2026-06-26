// FINGUARD_OS Global State
const API_URL = "";
let transactions = [];
let flagCount = 0;
let safeCount = 0;
let totalVolume = 0;
let shapChart = null;
let riskDonutChart = null;
let autoPilotInterval = null;

document.addEventListener("DOMContentLoaded", () => {
    checkApiHealth();
    initRiskDonutChart();
    
    // Forms & Buttons
    document.getElementById("tx-form").addEventListener("submit", handleTransactionSubmit);
    document.getElementById("load-legit-template").addEventListener("click", loadLegitimateTemplate);
    document.getElementById("load-fraud-template").addEventListener("click", loadFraudTemplate);
    document.getElementById("toggle-autopilot").addEventListener("click", toggleAutoPilot);
    
    // Modal
    const modal = document.getElementById("explanation-modal");
    document.querySelector(".close-btn").addEventListener("click", () => modal.style.display = "none");
    
    // Account Dossier Modal
    const accountModal = document.getElementById("account-modal");
    document.getElementById("close-account-modal").addEventListener("click", () => accountModal.style.display = "none");
    document.getElementById("btn-freeze-account").addEventListener("click", freezeAccount);
    
    window.addEventListener("click", (e) => { 
        if (e.target === modal) modal.style.display = "none"; 
        if (e.target === accountModal) accountModal.style.display = "none";
    });
    
    // Search Listener
    const searchInput = document.getElementById("account-search-input");
    searchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter" && searchInput.value.trim() !== "") {
            fetchAccountDossier(searchInput.value.trim());
        }
    });
});

async function checkApiHealth() {
    const dot = document.getElementById("api-dot");
    const text = document.getElementById("api-status-text");
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            dot.className = "status-dot online";
            text.textContent = "SYS_ONLINE";
        } else {
            dot.className = "status-dot offline";
            text.textContent = "ERR_503";
        }
    } catch (error) {
        dot.className = "status-dot offline";
        text.textContent = "OFFLINE";
    }
}

function generateRandomAccount(prefix) {
    return prefix + Math.floor(Math.random() * 1000000000).toString().padStart(9, '0');
}

function loadLegitimateTemplate() {
    const amount = (Math.random() * 900 + 10).toFixed(2);
    const oldBalance = (parseFloat(amount) + Math.random() * 5000 + 100).toFixed(2);
    const newBalance = (parseFloat(oldBalance) - parseFloat(amount)).toFixed(2);
    
    document.getElementById("tx-type").value = "PAYMENT";
    document.getElementById("tx-step").value = Math.floor(Math.random() * 744) + 1;
    document.getElementById("tx-amount").value = amount;
    document.getElementById("tx-orig").value = generateRandomAccount("C");
    document.getElementById("tx-orig-old").value = oldBalance;
    document.getElementById("tx-orig-new").value = newBalance;
    document.getElementById("tx-dest").value = generateRandomAccount("M");
    document.getElementById("tx-dest-old").value = "0.00";
    document.getElementById("tx-dest-new").value = "0.00";
}

function loadFraudTemplate() {
    const amount = (Math.random() * 800000 + 50000).toFixed(2);
    
    document.getElementById("tx-type").value = "TRANSFER";
    document.getElementById("tx-step").value = Math.floor(Math.random() * 744) + 1;
    document.getElementById("tx-amount").value = amount;
    document.getElementById("tx-orig").value = generateRandomAccount("C");
    document.getElementById("tx-orig-old").value = amount;
    document.getElementById("tx-orig-new").value = "0.00";
    document.getElementById("tx-dest").value = generateRandomAccount("C");
    document.getElementById("tx-dest-old").value = "0.00";
    document.getElementById("tx-dest-new").value = "0.00";
}

async function handleTransactionSubmit(event) {
    if (event) event.preventDefault();
    
    const submitBtn = document.getElementById("btn-submit");
    submitBtn.textContent = "PROCESSING...";
    submitBtn.style.color = "#a200ff";
    
    const payload = {
        step: parseInt(document.getElementById("tx-step").value),
        type: document.getElementById("tx-type").value,
        amount: parseFloat(document.getElementById("tx-amount").value),
        nameOrig: document.getElementById("tx-orig").value,
        oldbalanceOrg: parseFloat(document.getElementById("tx-orig-old").value),
        newbalanceOrig: parseFloat(document.getElementById("tx-orig-new").value),
        nameDest: document.getElementById("tx-dest").value,
        oldbalanceDest: parseFloat(document.getElementById("tx-dest-old").value),
        newbalanceDest: parseFloat(document.getElementById("tx-dest-new").value)
    };
    
    try {
        const response = await fetch(`${API_URL}/api/v1/transactions/evaluate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const evaluation = await response.json();
        
        const loggedTx = {
            id: uuidv4(),
            type: payload.type,
            amount: payload.amount,
            nameOrig: payload.nameOrig,
            nameDest: payload.nameDest,
            score: evaluation.fraud_score,
            isFraud: evaluation.is_fraud,
            explanations: evaluation.explanations
        };
        
        transactions.unshift(loggedTx);
        if (transactions.length > 50) transactions.pop(); // Keep table from getting too huge
        
        updateMetrics(loggedTx);
        renderTransactionsTable();
        updateDonutChart();
        
        if (loggedTx.isFraud) {
            triggerToast(loggedTx.amount);
            document.getElementById("radar-target").classList.add("detected");
            setTimeout(() => document.getElementById("radar-target").classList.remove("detected"), 2000);
        }
        
    } catch (error) {
        console.error("Evaluation failed:", error);
    } finally {
        submitBtn.textContent = "EXECUTE INJECTION";
        submitBtn.style.color = "var(--cyan-glow)";
        // Randomize latency stat
        document.getElementById("stat-latency").textContent = `${Math.floor(Math.random() * 30 + 10)}ms`;
    }
}

/* --- AUTO PILOT MODE --- */
function toggleAutoPilot() {
    const btn = document.getElementById("toggle-autopilot");
    
    if (autoPilotInterval) {
        // Turn off
        clearInterval(autoPilotInterval);
        autoPilotInterval = null;
        btn.innerHTML = `<span class="icon">⚡</span> ENGAGE AUTO-PILOT`;
        btn.classList.remove("active");
        btn.style.borderColor = "var(--purple-ai)";
        btn.style.color = "var(--text-main)";
    } else {
        // Turn on
        btn.innerHTML = `<span class="icon">⏹</span> SYSTEM ON AUTO`;
        btn.classList.add("active");
        
        // Run immediately then loop
        triggerAutoPilotTransaction();
        autoPilotInterval = setInterval(triggerAutoPilotTransaction, 3000); // every 3 seconds
    }
}

function triggerAutoPilotTransaction() {
    // 15% chance to generate a FRAUD transaction, 85% chance for SAFE
    if (Math.random() < 0.15) {
        loadFraudTemplate();
    } else {
        loadLegitimateTemplate();
    }
    handleTransactionSubmit(); // Fire it
}

/* --- METRICS & CHARTS --- */
function updateMetrics(tx) {
    if (tx.isFraud) {
        flagCount++;
        document.getElementById("stat-threats").textContent = flagCount;
    } else {
        safeCount++;
    }
    totalVolume += tx.amount;
    document.getElementById("stat-vol").textContent = `$${(totalVolume / 1000).toFixed(1)}k`;
}

function initRiskDonutChart() {
    const ctx = document.getElementById("riskDonutChart").getContext("2d");
    riskDonutChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Safe', 'Threats'],
            datasets: [{
                data: [1, 0], // Start with fake data until real data arrives
                backgroundColor: ['#00ff66', '#ff003c'],
                borderWidth: 0,
                hoverOffset: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { position: 'bottom', labels: { color: '#4b5563', font: { family: "'Roboto', sans-serif", weight: 700, size: 13 } } }
            }
        }
    });
}

function updateDonutChart() {
    if (safeCount === 0 && flagCount === 0) return;
    riskDonutChart.data.datasets[0].data = [safeCount, flagCount];
    riskDonutChart.update();
}

/* --- TABLE RENDERING --- */
function renderTransactionsTable() {
    const tbody = document.getElementById("transactions-body");
    tbody.innerHTML = "";
    
    transactions.forEach((tx, index) => {
        const tr = document.createElement("tr");
        if (tx.isFraud) tr.className = "row-fraud";
        if (index === 0) tr.classList.add("row-new"); // Animation for new row
        
        const riskColorClass = tx.isFraud ? "text-red" : (tx.score > 0.15 ? "text-purple" : "text-cyan");
        const riskPercent = (tx.score * 100).toFixed(1);
        
        tr.innerHTML = `
            <td>${tx.type}</td>
            <td>$${tx.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}</td>
            <td>${tx.nameOrig} &rarr; ${tx.nameDest}</td>
            <td class="${riskColorClass}">${riskPercent}%</td>
            <td>
                ${tx.isFraud 
                    ? `<button class="btn-audit" onclick="openExplanationModal('${tx.id}')">[ AUDIT ]</button>`
                    : `-`
                }
            </td>
        `;
        tbody.appendChild(tr);
    });
}

const featureNameMap = {
    'errorBalanceOrig': 'Sender Bal Error',
    'errorBalanceDest': 'Receiver Bal Error',
    'amount': 'Transfer Amount',
    'oldbalanceOrg': 'Sender Start Bal',
    'newbalanceOrig': 'Sender End Bal',
    'oldbalanceDest': 'Receiver Start Bal',
    'newbalanceDest': 'Receiver End Bal',
    'is_merchant_dest': 'Merchant Payment',
    'type_CASH_IN': 'Cash In',
    'type_CASH_OUT': 'Cash Out',
    'type_DEBIT': 'Debit',
    'type_PAYMENT': 'Payment',
    'type_TRANSFER': 'Transfer',
    'velocity_count_24h': 'High Frequency Trades',
    'velocity_amount_24h': 'Spike in Outgoing Funds'
};

function getHumanReadableFeature(rawName) {
    return featureNameMap[rawName] || rawName;
}

/* --- EXPLAINABLE AI MODAL --- */
function openExplanationModal(txId) {
    const tx = transactions.find(t => t.id === txId);
    if (!tx || !tx.explanations) return;
    
    const modal = document.getElementById("explanation-modal");
    document.getElementById("modal-fraud-score").textContent = `${(tx.score * 100).toFixed(1)}%`;
    
    const shapData = tx.explanations;
    const sortedFeatures = Object.entries(shapData).sort((a, b) => b[1] - a[1]);
    const topPositive = sortedFeatures[0];
    
    let summaryText = "";
    if (topPositive && topPositive[1] > 0) {
        const readableFeature = getHumanReadableFeature(topPositive[0]);
        summaryText = `SECURITY ALERT: This transaction was blocked to protect your funds. Our AI detected highly suspicious behavior, specifically regarding the "${readableFeature}". This math does not add up and strongly indicates a hacker is attempting to illegally drain the account.`;
    } else {
        summaryText = `SECURITY ALERT: This transaction was blocked due to multiple unusual patterns that match known hacking techniques.`;
    }
    document.getElementById("modal-summary-desc").textContent = summaryText;
    
    renderShapChart(tx.explanations);
    modal.style.display = "flex";
}

function renderShapChart(explanations) {
    const ctx = document.getElementById("shapChart").getContext("2d");
    const sortedData = Object.entries(explanations).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])); 
    const labels = sortedData.map(item => getHumanReadableFeature(item[0]));
    
    // Use absolute values so bars always go UP (like a standard bar chart), but keep colors for context
    const values = sortedData.map(item => Math.abs(item[1]));
    const backgroundColors = sortedData.map(item => item[1] >= 0 ? '#ff003c' : '#00ff66');
    
    if (shapChart) shapChart.destroy();
    
    shapChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{ data: values, backgroundColor: backgroundColors, borderRadius: 2 }]
        },
        options: {
            indexAxis: 'x', responsive: true, maintainAspectRatio: false,
            animation: false, // Disable animation so it renders instantly for print preview
            layout: { padding: { bottom: 20 } },
            plugins: { legend: { display: false } },
            scales: {
                x: { 
                    grid: { display: false }, 
                    ticks: { color: '#000000', font: { family: "'JetBrains Mono', monospace", size: 11, weight: 'bold' }, autoSkip: false, maxRotation: 45, minRotation: 45 } 
                },
                y: { 
                    grid: { color: '#e2e8f0' }, 
                    ticks: { color: '#000000', font: { family: "'Open Sans', sans-serif", size: 12, weight: 'bold' } } 
                }
            }
        }
    });
}

function triggerToast(amountOrMessage, isSms = false) {
    const container = document.getElementById("toast-container");
    const toast = document.createElement("div");
    toast.className = "toast";
    if (isSms) {
        toast.style.borderLeftColor = "var(--primary-color)";
        toast.innerHTML = `<strong style="color: var(--primary-color);">📱 SMS DISPATCHED</strong><br/>${amountOrMessage}`;
    } else {
        toast.innerHTML = `<strong>THREAT INTERCEPTED</strong> [$${amountOrMessage.toLocaleString()}]`;
    }
    container.appendChild(toast);
    setTimeout(() => { toast.remove(); }, 4000);
}

function uuidv4() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/* --- CUSTOMER LOOKUP SEARCH --- */
async function fetchAccountDossier(accountId) {
    const searchInput = document.getElementById("account-search-input");
    searchInput.disabled = true;
    
    try {
        const response = await fetch(`${API_URL}/api/v1/accounts/${accountId}`);
        if (!response.ok) {
            triggerToast(`ACCOUNT NOT FOUND: ${accountId}`);
            searchInput.disabled = false;
            return;
        }
        
        const data = await response.json();
        
        // Populate profile
        document.getElementById("dossier-id").textContent = data.account_id;
        document.getElementById("dossier-name").textContent = data.customer_name;
        document.getElementById("dossier-status").textContent = data.status.toUpperCase();
        document.getElementById("dossier-status").className = "";
        document.getElementById("dossier-balance").textContent = `$${data.current_balance.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        document.getElementById("dossier-risk").textContent = `${(data.risk_score * 100).toFixed(1)}%`;
        
        // Reset Freeze Button
        const freezeBtn = document.getElementById("btn-freeze-account");
        if (data.status.toUpperCase() === "LOCKED_BY_ADMIN" || data.status.toUpperCase() === "FROZEN") {
            freezeBtn.disabled = true;
            freezeBtn.textContent = "[ ACCOUNT FROZEN ]";
            document.getElementById("dossier-status").className = "text-red";
        } else {
            freezeBtn.disabled = false;
            freezeBtn.textContent = "[ ⚠ FREEZE ACCOUNT ]";
        }
        
        // Risk styling
        if (data.risk_score > 0.8) {
            document.getElementById("dossier-risk").className = "text-red glitch-text";
            document.getElementById("dossier-risk").setAttribute("data-text", `${(data.risk_score * 100).toFixed(1)}%`);
        } else {
            document.getElementById("dossier-risk").className = "text-cyan";
        }
        
        // Populate transaction table
        const tbody = document.getElementById("dossier-body");
        tbody.innerHTML = "";
        
        if (data.transactions.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5">NO RECORDED TRANSACTIONS</td></tr>`;
        } else {
            data.transactions.forEach(tx => {
                const tr = document.createElement("tr");
                const date = new Date(tx.timestamp).toLocaleString();
                const riskClass = tx.is_fraud ? "text-red" : "text-green";
                const status = tx.is_fraud ? "BLOCKED" : "CLEARED";
                
                tr.innerHTML = `
                    <td>${date}</td>
                    <td>${tx.type}</td>
                    <td>$${tx.amount.toLocaleString()}</td>
                    <td>${tx.origin_account_id} &rarr; ${tx.dest_account_id}</td>
                    <td class="${riskClass}">${status}</td>
                `;
                tbody.appendChild(tr);
            });
        }
        
        // Show modal
        document.getElementById("account-modal").style.display = "flex";
        searchInput.value = "";
        
    } catch (error) {
        console.error("Dossier fetch failed", error);
        triggerToast("SERVER COMM ERROR");
    } finally {
        searchInput.disabled = false;
    }
}

function freezeAccount() {
    const statusEl = document.getElementById("dossier-status");
    const btn = document.getElementById("btn-freeze-account");
    const accId = document.getElementById("dossier-id").textContent;
    
    // Update UI
    statusEl.textContent = "LOCKED_BY_ADMIN";
    statusEl.className = "text-red glitch-text";
    
    btn.disabled = true;
    btn.textContent = "[ ACCOUNT FROZEN ]";
    
    // Simulate SMS dispatch
    triggerToast(`Lock alert sent to customer device for ${accId}`, true);
}

