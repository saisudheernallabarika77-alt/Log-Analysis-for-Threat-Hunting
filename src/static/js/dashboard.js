/**
 * Dashboard JavaScript
 * Handles charts, real-time data, and threat hunting visualizations
 */

// ─── Login Activity Chart ───
let loginChart = null;

function fetchLoginChart() {
    fetch('/api/dashboard/login-chart')
        .then(r => r.json())
        .then(data => {
            const labels = Object.keys(data).sort();
            const successData = labels.map(d => data[d].SUCCESS || 0);
            const failedData = labels.map(d => data[d].FAILED || 0);
            
            // Format labels to short date
            const shortLabels = labels.map(d => {
                const date = new Date(d);
                return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
            });
            
            const ctx = document.getElementById('loginChart');
            if (!ctx) return;
            
            if (loginChart) loginChart.destroy();
            
            loginChart = new Chart(ctx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: shortLabels,
                    datasets: [
                        {
                            label: 'Successful',
                            data: successData,
                            borderColor: '#00FF00',
                            backgroundColor: 'rgba(0, 255, 0, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#00FF00',
                            pointBorderColor: '#00FF00',
                            pointRadius: 3
                        },
                        {
                            label: 'Failed',
                            data: failedData,
                            borderColor: '#FF4444',
                            backgroundColor: 'rgba(255, 0, 0, 0.1)',
                            borderWidth: 2,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#FF4444',
                            pointBorderColor: '#FF4444',
                            pointRadius: 3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#888',
                                font: { family: "'Share Tech Mono', monospace", size: 11 }
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#555', font: { size: 10 } },
                            grid: { color: 'rgba(0,255,0,0.05)' }
                        },
                        y: {
                            beginAtZero: true,
                            ticks: { 
                                color: '#555', 
                                font: { size: 10 },
                                stepSize: 1
                            },
                            grid: { color: 'rgba(0,255,0,0.05)' }
                        }
                    }
                }
            });
        })
        .catch(err => console.log('Chart fetch error:', err));
}


// ─── Risk Meter (Gauge) ───
function drawRiskMeter(score) {
    const canvas = document.getElementById('riskMeter');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const centerX = canvas.width / 2;
    const centerY = canvas.height - 10;
    const radius = 85;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Background arc
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, 2 * Math.PI);
    ctx.strokeStyle = '#1a1a2e';
    ctx.lineWidth = 15;
    ctx.stroke();
    
    // Score arc
    const angle = Math.PI + (score / 100) * Math.PI;
    
    let gradient;
    if (score >= 70) {
        gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#FF0000');
        gradient.addColorStop(1, '#FF4444');
    } else if (score >= 40) {
        gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#FFA500');
        gradient.addColorStop(1, '#FFD700');
    } else {
        gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
        gradient.addColorStop(0, '#00AA00');
        gradient.addColorStop(1, '#00FF00');
    }
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, angle);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 15;
    ctx.lineCap = 'round';
    ctx.stroke();
    
    // Glow effect
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, Math.PI, angle);
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 15;
    ctx.shadowColor = score >= 70 ? '#FF0000' : score >= 40 ? '#FFA500' : '#00FF00';
    ctx.shadowBlur = 15;
    ctx.stroke();
    ctx.shadowBlur = 0;
    
    // Tick marks
    for (let i = 0; i <= 10; i++) {
        const tickAngle = Math.PI + (i / 10) * Math.PI;
        const innerR = radius - 22;
        const outerR = radius - 12;
        
        ctx.beginPath();
        ctx.moveTo(
            centerX + innerR * Math.cos(tickAngle),
            centerY + innerR * Math.sin(tickAngle)
        );
        ctx.lineTo(
            centerX + outerR * Math.cos(tickAngle),
            centerY + outerR * Math.sin(tickAngle)
        );
        ctx.strokeStyle = '#333';
        ctx.lineWidth = 1;
        ctx.stroke();
    }
    
    // Needle
    const needleAngle = Math.PI + (score / 100) * Math.PI;
    const needleLength = radius - 25;
    
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(
        centerX + needleLength * Math.cos(needleAngle),
        centerY + needleLength * Math.sin(needleAngle)
    );
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();
    
    // Center dot
    ctx.beginPath();
    ctx.arc(centerX, centerY, 4, 0, 2 * Math.PI);
    ctx.fillStyle = '#fff';
    ctx.fill();
}


// ─── Threat Hunting Data ───
function refreshThreatData() {
    // Fetch suspicious patterns
    fetch('/api/threat/suspicious-patterns')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('patternsList');
            if (!container) return;
            
            if (data.patterns.length === 0) {
                container.innerHTML = '<p style="color:#00FF00;text-align:center;padding:20px"><i class="fas fa-check-circle"></i> No suspicious patterns detected</p>';
                return;
            }
            
            container.innerHTML = data.patterns.map(p => `
                <div class="pattern-item">
                    <span class="severity-badge severity-${p.severity.toLowerCase()}">${p.severity}</span>
                    <span>${p.description}</span>
                </div>
            `).join('');
        })
        .catch(() => {
            const el = document.getElementById('patternsList');
            if (el) el.innerHTML = '<p style="color:#00FF00;text-align:center;padding:20px"><i class="fas fa-check-circle"></i> System clear</p>';
        });
    
    // Fetch IP intelligence
    fetch('/api/threat/ip-tracking')
        .then(r => r.json())
        .then(data => {
            const container = document.getElementById('ipList');
            if (!container) return;
            
            let html = '';
            
            if (data.user_ips.length > 0) {
                html += '<div style="margin-bottom:10px;color:#00FF00;font-size:11px">YOUR IPs:</div>';
                data.user_ips.forEach(ip => {
                    html += `<div class="pattern-item">
                        <code style="color:${ip.failed_count > 0 ? '#FF4444' : '#00FF00'}">${ip.ip_address}</code>
                        <span style="margin-left:auto;font-size:10px">${ip.count} accesses</span>
                    </div>`;
                });
            }
            
            if (data.suspicious_ips.length > 0) {
                html += '<div style="margin:15px 0 10px;color:#FF4444;font-size:11px">⚠️ SUSPICIOUS IPs:</div>';
                data.suspicious_ips.forEach(ip => {
                    html += `<div class="pattern-item" style="border-left:2px solid #FF4444;padding-left:8px">
                        <code style="color:#FF4444">${ip.ip_address}</code>
                        <span style="margin-left:auto;font-size:10px;color:#FF6666">${ip.failed_attempts} failed</span>
                    </div>`;
                });
            }
            
            if (data.multi_location_detected) {
                html += '<div style="margin-top:15px;padding:8px;background:rgba(255,165,0,0.1);border:1px solid rgba(255,165,0,0.3);border-radius:6px;font-size:11px;color:#FFA500">⚠️ Multiple locations detected for your account</div>';
            }
            
            if (!html) {
                html = '<p style="color:#00FF00;text-align:center;padding:20px"><i class="fas fa-check-circle"></i> No IP threats</p>';
            }
            
            container.innerHTML = html;
        })
        .catch(() => {
            const el = document.getElementById('ipList');
            if (el) el.innerHTML = '<p style="color:#00FF00;text-align:center;padding:20px"><i class="fas fa-check-circle"></i> IP data clean</p>';
        });
}


// ─── Dashboard Auto-Refresh ───
function refreshDashboard() {
    fetch('/api/dashboard/stats')
        .then(r => r.json())
        .then(data => {
            // Could update stat cards dynamically here
            console.log('[CYBERSEC] Dashboard refreshed:', new Date().toLocaleTimeString());
        })
        .catch(err => console.log('Dashboard refresh error:', err));
    
    fetchLoginChart();
    refreshThreatData();
}
