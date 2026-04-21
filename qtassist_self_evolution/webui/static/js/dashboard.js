/**
 * 自我进化系统控制面板 - 仪表板交互脚本
 * 
 * 功能：
 * 1. 实时更新系统状态和监控数据
 * 2. 绘制性能图表
 * 3. 管理系统警报
 * 4. 控制系统的启动/停止
 * 5. 定期刷新数据
 */

// 全局变量
let performanceChart = null;
let refreshInterval = null;
let lastMetrics = {
    cpu_usage: null,
    memory_usage: null,
    disk_usage: null,
    function_execution_time: null
};
let chartData = {
    timestamps: [],
    cpu: [],
    memory: [],
    disk: []
};

// 初始化函数
document.addEventListener('DOMContentLoaded', function() {
    // 更新时间
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // 初始化图表
    initializeChart();
    
    // 绑定事件监听器
    bindEvents();
    
    // 开始定期刷新数据
    startDataRefresh();
    
    // 初始加载数据
    loadAllData();
});

// 备用：页面加载完成后也尝试加载数据
window.addEventListener('load', function() {
    setTimeout(loadAllData, 500);
});

/**
 * 更新当前时间
 */
function updateCurrentTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('zh-CN');
    const dateStr = now.toLocaleDateString('zh-CN');
    
    document.getElementById('current-time').textContent = `${dateStr} ${timeStr}`;
}

/**
 * 初始化性能图表
 */
function initializeChart() {
    // 确保canvas存在
    const canvas = document.getElementById('performance-chart');
    if (!canvas) {
        console.error('Canvas元素不存在');
        return;
    }
    
    // 设置canvas尺寸
    canvas.width = canvas.parentElement.clientWidth - 20;
    canvas.height = 280;
    
    // 初始化示例数据
    const now = new Date();
    const labels = [];
    const cpuData = [];
    const memoryData = [];
    const diskData = [];
    
    for (let i = 20; i >= 0; i--) {
        const time = new Date(now - i * 60000);
        labels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }));
        cpuData.push(Math.random() * 30 + 10);
        memoryData.push(Math.random() * 40 + 20);
        diskData.push(Math.random() * 20 + 50);
    }
    
    const ctx = canvas.getContext('2d');
    
    // 确认Chart可用
    if (typeof Chart === 'undefined') {
        console.error('Chart.js未加载，请刷新页面重试');
        return;
    }
    
    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'CPU使用率 (%)',
                    data: cpuData,
                    borderColor: '#2962ff',
                    backgroundColor: 'rgba(41, 98, 255, 0.15)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#2962ff',
                    pointBorderColor: '#131722',
                    pointBorderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: '内存使用率 (%)',
                    data: memoryData,
                    borderColor: '#00c076',
                    backgroundColor: 'rgba(0, 192, 118, 0.15)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#00c076',
                    pointBorderColor: '#131722',
                    pointBorderWidth: 2,
                    pointRadius: 3
                },
                {
                    label: '磁盘使用率 (%)',
                    data: diskData,
                    borderColor: '#ff9800',
                    backgroundColor: 'rgba(255, 152, 0, 0.15)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true,
                    pointBackgroundColor: '#ff9800',
                    pointBorderColor: '#131722',
                    pointBorderWidth: 2,
                    pointRadius: 3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: {
                duration: 500
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 15,
                        color: '#d1d4dc',
                        font: {
                            size: 12,
                            family: 'system-ui, -apple-system, sans-serif'
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#1e222d',
                    titleColor: '#d1d4dc',
                    bodyColor: '#d1d4dc',
                    borderColor: '#2a2e39',
                    borderWidth: 1,
                    cornerRadius: 4,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '时间',
                        color: '#787b86',
                        font: {
                            size: 12,
                            family: 'system-ui, -apple-system, sans-serif'
                        }
                    },
                    ticks: {
                        maxTicksLimit: 10,
                        color: '#787b86',
                        font: {
                            size: 11,
                            family: 'system-ui, -apple-system, sans-serif'
                        }
                    },
                    grid: {
                        color: '#2a2e39',
                        borderColor: '#2a2e39'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '使用率 (%)',
                        color: '#787b86',
                        font: {
                            size: 12,
                            family: 'system-ui, -apple-system, sans-serif'
                        }
                    },
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        },
                        color: '#787b86',
                        font: {
                            size: 11,
                            family: 'system-ui, -apple-system, sans-serif'
                        }
                    },
                    grid: {
                        color: '#2a2e39',
                        borderColor: '#2a2e39'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    });
    
    // 强制渲染图表
    performanceChart.update();
}

/**
 * 绑定事件监听器
 */
function bindEvents() {
    // 刷新按钮
    document.getElementById('refresh-status').addEventListener('click', function() {
        loadAllData();
        showNotification('数据刷新中...', 'info');
    });
    
    // 启动系统按钮
    document.getElementById('start-system').addEventListener('click', function() {
        startSystem();
    });
    
    // 停止系统按钮
    document.getElementById('stop-system').addEventListener('click', function() {
        stopSystem();
    });
    
    // 图表时间范围选择
    document.getElementById('chart-range').addEventListener('change', function() {
        loadPerformanceData(parseInt(this.value));
    });
}

/**
 * 开始定期刷新数据
 */
function startDataRefresh() {
    // 清除现有定时器
    if (refreshInterval) {
        clearInterval(refreshInterval);
    }
    
    // 设置新的定时器：每10秒刷新一次
    refreshInterval = setInterval(function() {
        loadSystemStatus();
        loadCurrentMetrics();
        loadAlerts();
    }, 10000); // 10秒
}

/**
 * 加载所有数据
 */
function loadAllData() {
    showLoading(true);
    
    // 顺序加载所有数据
    Promise.all([
        loadSystemStatus(),
        loadMonitoringStatus(),
        loadCurrentMetrics(),
        loadPerformanceData(5), // 默认加载最近5分钟数据
        loadAlerts(),
        loadMLStatus()
    ]).finally(() => {
        showLoading(false);
    });
}

/**
 * 显示/隐藏加载动画
 */
function showLoading(show) {
    const spinner = document.getElementById('loading-spinner');
    if (show) {
        spinner.style.display = 'block';
    } else {
        spinner.style.display = 'none';
    }
}

/**
 * 显示通知
 */
function showNotification(message, type = 'info') {
    // 创建通知元素 - 使用TradingView样式
    const notification = document.createElement('div');
    
    // 映射类型到TradingView样式
    const typeMap = {
        'info': 'tv-alert-info',
        'success': 'tv-alert-success', 
        'warning': 'tv-alert-warning',
        'danger': 'tv-alert-critical'
    };
    
    notification.className = `tv-alert ${typeMap[type] || 'tv-alert-info'} tv-notification`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 1050;
        min-width: 300px;
        max-width: 400px;
        box-shadow: var(--tv-shadow-md);
    `;
    
    notification.innerHTML = `
        <div class="tv-alert-content">${message}</div>
        <button type="button" class="tv-alert-close" data-dismiss="tv-alert">&times;</button>
    `;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 添加关闭按钮事件
    const closeButton = notification.querySelector('.tv-alert-close');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            if (notification.parentNode) {
                notification.remove();
            }
        });
    }
    
    // 5秒后自动移除
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

/**
 * 加载系统状态
 */
async function loadSystemStatus() {
    try {
        const response = await fetch('/api/system/status');
        const data = await response.json();
        
        console.log('系统状态响应:', data);
        
        if (data.status === '成功' || data.status === 'success' || data.is_running) {
            updateSystemStatus(data);
        } else {
            console.error('加载系统状态失败:', data.message);
        }
    } catch (error) {
        console.error('加载系统状态时出错:', error);
    }
}

/**
 * 更新系统状态显示
 */
function updateSystemStatus(data) {
    // 系统状态指示器
    const statusIndicator = document.getElementById('system-status-indicator');
    const systemStatusBadge = document.getElementById('system-status-badge');
    
    if (data.is_running) {
        // 使用TradingView风格的状态指示器
        if (statusIndicator) {
            statusIndicator.className = 'tv-status-indicator tv-status-active';
        }
        if (systemStatusBadge) {
            systemStatusBadge.className = 'tv-badge tv-badge-success';
            systemStatusBadge.textContent = '状态: 运行中';
        }
        
        // 启用/禁用控制按钮
        document.getElementById('start-system').disabled = true;
        document.getElementById('stop-system').disabled = false;
    } else {
        // 使用TradingView风格的状态指示器
        if (statusIndicator) {
            statusIndicator.className = 'tv-status-indicator tv-status-inactive';
        }
        if (systemStatusBadge) {
            systemStatusBadge.className = 'tv-badge tv-badge-danger';
            systemStatusBadge.textContent = '状态: 已停止';
        }
        
        // 启用/禁用控制按钮
        document.getElementById('start-system').disabled = false;
        document.getElementById('stop-system').disabled = true;
    }
    
    // 系统阶段
    const systemPhaseElement = document.getElementById('system-phase');
    if (systemPhaseElement) {
        systemPhaseElement.textContent = data.current_phase || '未知';
    }
    
    // 心跳时间
    const heartbeatEl = document.getElementById('last-heartbeat');
    if (heartbeatEl && data.last_heartbeat) {
        const heartbeatTime = new Date(data.last_heartbeat);
        heartbeatEl.textContent = heartbeatTime.toLocaleTimeString('zh-CN');
    } else if (heartbeatEl) {
        heartbeatEl.textContent = '--:--:--';
    }
    
    // 运行时长（简单计算）
    const uptimeElement = document.getElementById('uptime');
    if (uptimeElement) {
        if (data.last_heartbeat && data.is_running) {
            const heartbeatTime = new Date(data.last_heartbeat);
            const now = new Date();
            const diffMs = now - heartbeatTime;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 1) {
                uptimeElement.textContent = '刚刚';
            } else if (diffMins < 60) {
                uptimeElement.textContent = `${diffMins}分钟前`;
            } else {
                const hours = Math.floor(diffMins / 60);
                uptimeElement.textContent = `${hours}小时前`;
            }
        } else {
            uptimeElement.textContent = '--';
        }
    }
    
    // 任务统计
    const activeTasksElement = document.getElementById('active-tasks');
    const completedTasksElement = document.getElementById('completed-tasks');
    if (activeTasksElement) {
        activeTasksElement.textContent = data.active_tasks || 0;
    }
    if (completedTasksElement) {
        completedTasksElement.textContent = data.completed_tasks || 0;
    }
    
    // 模块状态
    if (data.module_status) {
        updateModuleStatus(data.module_status);
    }
    
    // 更新全局主题状态
    if (window.tvTheme && window.tvTheme.updateSystemStatus) {
        window.tvTheme.updateSystemStatus(data.is_running ? 'running' : 'stopped');
    }
}

/**
 * 更新模块状态显示
 */
function updateModuleStatus(moduleStatus) {
    const modules = [
        { id: 'usage-tracker', key: 'usage_tracker', dotId: 'module-usage-tracker-dot' },
        { id: 'demand-analyzer', key: 'demand_analyzer', dotId: 'module-demand-analyzer-dot' },
        { id: 'auto-optimizer', key: 'auto_optimizer', dotId: 'module-auto-optimizer-dot' },
        { id: 'auto-installer', key: 'auto_installer', dotId: 'module-auto-installer-dot' },
        { id: 'new-function-creator', key: 'new_function_creator', dotId: 'module-new-function-creator-dot' },
        { id: 'ml-predictor', key: 'ml_predictor', dotId: 'module-ml-predictor-dot' },
        { id: 'real-time-monitor', key: 'real_time_monitor', dotId: 'module-real-time-monitor-dot' }
    ];
    
    modules.forEach(module => {
        const dotElement = document.getElementById(module.dotId);
        if (dotElement) {
            if (moduleStatus[module.key]) {
                dotElement.className = 'tv-status-indicator tv-status-active';
            } else {
                dotElement.className = 'tv-status-indicator tv-status-inactive';
            }
        }
        
        // 也更新全局主题状态
        if (window.tvTheme && window.tvTheme.updateModuleStatus) {
            const status = moduleStatus[module.key] ? 'active' : 'inactive';
            window.tvTheme.updateModuleStatus(`module-${module.id}`, status);
        }
    });
}

/**
 * 加载监控状态
 */
async function loadMonitoringStatus() {
    try {
        const response = await fetch('/api/monitoring/status');
        const data = await response.json();
        
        if (data.status === '成功') {
            updateMonitoringStatus(data);
        } else {
            console.error('加载监控状态失败:', data.message);
        }
    } catch (error) {
        console.error('加载监控状态时出错:', error);
    }
}

/**
 * 更新监控状态显示
 */
function updateMonitoringStatus(data) {
    document.getElementById('monitoring-status').textContent = 
        data.monitoring_available ? '已启用' : '不可用';
    
    if (data.monitoring_available) {
        document.getElementById('collection-interval').textContent = 
            data.collection_interval ? `${data.collection_interval}秒` : '--秒';
        document.getElementById('alerts-enabled').textContent = 
            data.alerts_enabled ? '是' : '否';
        document.getElementById('retention-days').textContent = '30天'; // 默认值
    } else {
        document.getElementById('collection-interval').textContent = '--秒';
        document.getElementById('alerts-enabled').textContent = '--';
        document.getElementById('retention-days').textContent = '--天';
    }
}

/**
 * 加载当前指标
 */
async function loadCurrentMetrics() {
    try {
        const response = await fetch('/api/monitoring/current-metrics');
        const data = await response.json();
        
        if (data.status === '成功' && data.metrics_available) {
            updateCurrentMetrics(data.data?.metrics || {});
        } else {
            console.error('加载当前指标失败:', data.message);
        }
    } catch (error) {
        console.error('加载当前指标时出错:', error);
    }
}

/**
 * 更新当前指标显示
 */
function updateCurrentMetrics(metrics) {
    // 从API返回的指标对象中提取实际值
    // API返回的指标结构: {metric_name: {current, avg, min, max, count}}
    
    // 提取CPU使用率 - 使用cpu_usage_total.current
    let currentCpu = null;
    if (metrics.cpu_usage_total && metrics.cpu_usage_total.current !== undefined) {
        currentCpu = parseFloat(metrics.cpu_usage_total.current);
    }
    
    // 提取内存使用率 - 使用memory_usage_total.current
    let currentMemory = null;
    if (metrics.memory_usage_total && metrics.memory_usage_total.current !== undefined) {
        currentMemory = parseFloat(metrics.memory_usage_total.current);
    }
    
    // 提取磁盘使用率 - 使用disk_usage_/.current（根分区）
    let currentDisk = null;
    if (metrics['disk_usage_/'] && metrics['disk_usage_/'].current !== undefined) {
        currentDisk = parseFloat(metrics['disk_usage_/'].current);
    }
    
    // 函数执行时间 - 当前API未提供，暂时使用0
    let currentFunctionTime = 0;
    
    // 更新CPU使用率显示
    if (currentCpu !== null) {
        const cpuElement = document.getElementById('cpu-usage');
        const cpuChange = document.getElementById('cpu-change');
        
        cpuElement.textContent = `${currentCpu.toFixed(1)}%`;
        
        // 计算变化
        if (lastMetrics.cpu_usage !== null) {
            const change = currentCpu - lastMetrics.cpu_usage;
            cpuChange.textContent = change >= 0 ? `+${change.toFixed(1)}%` : `${change.toFixed(1)}%`;
            cpuChange.className = `tv-metric-change ${change >= 0 ? 'negative' : 'positive'}`;
        } else {
            cpuChange.textContent = '--';
        }
        
        lastMetrics.cpu_usage = currentCpu;
        
        // 根据阈值设置颜色 - 使用TradingView样式
        if (currentCpu > 90) {
            cpuElement.className = 'tv-metric-value negative';
        } else if (currentCpu > 80) {
            cpuElement.className = 'tv-metric-value warning';
        } else {
            cpuElement.className = 'tv-metric-value neutral';
        }
    } else {
        // 如果CPU数据不可用，显示默认值
        document.getElementById('cpu-usage').textContent = '--%';
        document.getElementById('cpu-change').textContent = '--';
    }
    
    // 更新内存使用率显示
    if (currentMemory !== null) {
        const memoryElement = document.getElementById('memory-usage');
        const memoryChange = document.getElementById('memory-change');
        
        memoryElement.textContent = `${currentMemory.toFixed(1)}%`;
        
        // 计算变化
        if (lastMetrics.memory_usage !== null) {
            const change = currentMemory - lastMetrics.memory_usage;
            memoryChange.textContent = change >= 0 ? `+${change.toFixed(1)}%` : `${change.toFixed(1)}%`;
            memoryChange.className = `tv-metric-change ${change >= 0 ? 'negative' : 'positive'}`;
        } else {
            memoryChange.textContent = '--';
        }
        
        lastMetrics.memory_usage = currentMemory;
        
        // 根据阈值设置颜色 - 使用TradingView样式
        if (currentMemory > 95) {
            memoryElement.className = 'tv-metric-value negative';
        } else if (currentMemory > 85) {
            memoryElement.className = 'tv-metric-value warning';
        } else {
            memoryElement.className = 'tv-metric-value neutral';
        }
    } else {
        // 如果内存数据不可用，显示默认值
        document.getElementById('memory-usage').textContent = '--%';
        document.getElementById('memory-change').textContent = '--';
    }
    
    // 更新磁盘使用率显示
    if (currentDisk !== null) {
        const diskElement = document.getElementById('disk-usage');
        const diskChange = document.getElementById('disk-change');
        
        diskElement.textContent = `${currentDisk.toFixed(1)}%`;
        
        // 计算变化
        if (lastMetrics.disk_usage !== null) {
            const change = currentDisk - lastMetrics.disk_usage;
            diskChange.textContent = change >= 0 ? `+${change.toFixed(1)}%` : `${change.toFixed(1)}%`;
            diskChange.className = `tv-metric-change ${change >= 0 ? 'negative' : 'positive'}`;
        } else {
            diskChange.textContent = '--';
        }
        
        lastMetrics.disk_usage = currentDisk;
        
        // 根据阈值设置颜色 - 使用TradingView样式
        if (currentDisk > 95) {
            diskElement.className = 'tv-metric-value negative';
        } else if (currentDisk > 85) {
            diskElement.className = 'tv-metric-value warning';
        } else {
            diskElement.className = 'tv-metric-value neutral';
        }
    } else {
        // 如果磁盘数据不可用，显示默认值
        document.getElementById('disk-usage').textContent = '--%';
        document.getElementById('disk-change').textContent = '--';
    }
    
    // 更新函数执行时间显示（暂时使用0）
    const functionElement = document.getElementById('function-time');
    const functionChange = document.getElementById('function-change');
    
    functionElement.textContent = `${currentFunctionTime.toFixed(1)}ms`;
    functionChange.textContent = '--';
    
    // 根据阈值设置颜色 - 使用TradingView样式
    if (currentFunctionTime > 30000) { // 30秒
        functionElement.className = 'tv-metric-value negative';
    } else if (currentFunctionTime > 10000) { // 10秒
        functionElement.className = 'tv-metric-value warning';
    } else {
        functionElement.className = 'tv-metric-value positive';
    }
}

/**
 * 加载性能数据
 */
async function loadPerformanceData(minutes) {
    try {
        const response = await fetch(`/api/monitoring/performance-summary?minutes=${minutes}`);
        const data = await response.json();
        
        if (data.status === '成功' && data.summary_available) {
            updatePerformanceChart(data.data);
        } else {
            console.error('加载性能数据失败:', data.message);
        }
    } catch (error) {
        console.error('加载性能数据时出错:', error);
    }
}

/**
 * 更新性能图表
 */
function updatePerformanceChart(summary) {
    // 清空现有数据
    chartData.timestamps = [];
    chartData.cpu = [];
    chartData.memory = [];
    chartData.disk = [];
    
    // 如果有性能数据，填充图表
    if (summary.cpu_history && summary.cpu_history.length > 0) {
        summary.cpu_history.forEach((item, index) => {
            const time = new Date(item.timestamp);
            const timeStr = time.toLocaleTimeString('zh-CN', { 
                hour: '2-digit', 
                minute: '2-digit',
                second: '2-digit'
            });
            
            chartData.timestamps.push(timeStr);
            chartData.cpu.push(item.value);
            
            // 如果没有对应的内存和磁盘数据，使用默认值
            if (summary.memory_history && summary.memory_history[index]) {
                chartData.memory.push(summary.memory_history[index].value);
            } else {
                chartData.memory.push(0);
            }
            
            if (summary.disk_history && summary.disk_history[index]) {
                chartData.disk.push(summary.disk_history[index].value);
            } else {
                chartData.disk.push(0);
            }
        });
    }
    
    // 更新图表
    if (performanceChart) {
        performanceChart.data.labels = chartData.timestamps;
        performanceChart.data.datasets[0].data = chartData.cpu;
        performanceChart.data.datasets[1].data = chartData.memory;
        performanceChart.data.datasets[2].data = chartData.disk;
        performanceChart.update();
    }
}

/**
 * 加载警报
 */
async function loadAlerts() {
    try {
        const response = await fetch('/api/monitoring/alerts?hours=24');
        const data = await response.json();
        
        if (data.status === '成功' && data.alerts_available) {
            updateAlerts(data.data, data.count);
        } else {
            console.error('加载警报失败:', data.message);
            updateAlerts([], 0);
        }
    } catch (error) {
        console.error('加载警报时出错:', error);
        updateAlerts([], 0);
    }
}

/**
 * 更新警报显示
 */
function updateAlerts(alerts, count) {
    const alertsContainer = document.getElementById('alerts-container');
    const alertCount = document.getElementById('alert-count');
    
    // 更新警报计数 - 使用TradingView样式
    alertCount.textContent = count;
    if (count > 0) {
        alertCount.className = 'tv-badge tv-badge-danger';
    } else {
        alertCount.className = 'tv-badge tv-badge-success';
    }
    
    // 更新侧边栏警报计数
    const sidebarAlertCount = document.getElementById('sidebar-alert-count');
    if (sidebarAlertCount) {
        sidebarAlertCount.textContent = count;
        if (count > 0) {
            sidebarAlertCount.className = 'tv-badge tv-badge-danger ms-auto';
        } else {
            sidebarAlertCount.className = 'tv-badge tv-badge-success ms-auto';
        }
    }
    
    // 清空现有警报
    alertsContainer.innerHTML = '';
    
    // 如果没有警报
    if (alerts.length === 0) {
        const noAlerts = document.createElement('div');
        noAlerts.className = 'tv-alert tv-alert-info';
        noAlerts.innerHTML = `
            <div class="tv-alert-title">无警报</div>
            <div class="tv-alert-content">系统运行正常，未检测到任何警报。</div>
        `;
        alertsContainer.appendChild(noAlerts);
        return;
    }
    
    // 添加警报项
    alerts.forEach(alert => {
        const alertElement = document.createElement('div');
        
        // 确定警报级别和样式 - 使用TradingView样式
        let alertClass = 'tv-alert-info';
        if (alert.severity === 'error' || alert.severity === 'critical') {
            alertClass = 'tv-alert-critical';
        } else if (alert.severity === 'warning') {
            alertClass = 'tv-alert-warning';
        }
        
        // 格式化时间
        let timeText = '刚刚';
        if (alert.timestamp) {
            const alertTime = new Date(alert.timestamp);
            const now = new Date();
            const diffMs = now - alertTime;
            const diffMins = Math.floor(diffMs / 60000);
            
            if (diffMins < 1) {
                timeText = '刚刚';
            } else if (diffMins < 60) {
                timeText = `${diffMins}分钟前`;
            } else {
                const hours = Math.floor(diffMins / 60);
                timeText = `${hours}小时前`;
            }
        }
        
        alertElement.className = `tv-alert ${alertClass}`;
        alertElement.innerHTML = `
            <div class="tv-alert-title">${alert.title || '系统警报'}</div>
            <div class="tv-alert-content">${alert.message || '无详细描述'}</div>
            <div class="tv-alert-time">${timeText}</div>
        `;
        
        // 添加点击事件来确认警报
        if (!alert.acknowledged) {
            alertElement.style.cursor = 'pointer';
            alertElement.title = '点击确认警报';
            alertElement.addEventListener('click', function() {
                acknowledgeAlert(alert.id);
            });
        }
        
        alertsContainer.appendChild(alertElement);
    });
}

/**
 * 确认警报
 */
async function acknowledgeAlert(alertId) {
    try {
        const response = await fetch('/api/monitoring/acknowledge-alert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                alert_id: alertId,
                acknowledged_by: 'webui'
            })
        });
        
        const data = await response.json();
        
        if (data.status === '成功' && data.acknowledged) {
            showNotification('警报已确认', 'success');
            // 刷新警报列表
            loadAlerts();
        } else {
            showNotification('确认警报失败: ' + (data.message || '未知错误'), 'danger');
        }
    } catch (error) {
        console.error('确认警报时出错:', error);
        showNotification('确认警报时出错: ' + error.message, 'danger');
    }
}

/**
 * 加载机器学习状态
 */
async function loadMLStatus() {
    try {
        const response = await fetch('/api/ml/stats');
        const data = await response.json();
        
        if (data.status === '成功') {
            updateMLStatus(data);
        } else {
            console.error('加载机器学习状态失败:', data.message);
            updateMLStatus({ ml_available: false });
        }
    } catch (error) {
        console.error('加载机器学习状态时出错:', error);
        updateMLStatus({ ml_available: false });
    }
}

/**
 * 更新机器学习状态显示
 */
function updateMLStatus(data) {
    const mlContainer = document.getElementById('ml-status');
    
    if (!mlContainer) return;
    
    if (data.ml_available) {
        const stats = data.stats || {};
        
        mlContainer.innerHTML = `
            <div class="tv-grid tv-grid-cols-2 tv-gap-3 tv-mb-4">
                <div class="tv-stat-item">
                    <div class="tv-stat-label">预测总数</div>
                    <div class="tv-stat-value">${stats.total_predictions || 0}</div>
                </div>
                <div class="tv-stat-item">
                    <div class="tv-stat-label">准确率</div>
                    <div class="tv-stat-value ${(typeof stats.accuracy === 'number' && !isNaN(stats.accuracy) && stats.accuracy >= 0.7) ? 'positive' : ((typeof stats.accuracy === 'number' && !isNaN(stats.accuracy) && stats.accuracy >= 0.5) ? 'neutral' : 'negative')}">
                        ${(typeof stats.accuracy === 'number' && !isNaN(stats.accuracy)) ? `${(stats.accuracy * 100).toFixed(1)}%` : '--'}
                    </div>
                </div>
                <div class="tv-stat-item">
                    <div class="tv-stat-label">模型状态</div>
                    <div class="tv-stat-value ${stats.model_trained ? 'positive' : 'negative'}">
                        ${stats.model_trained ? '已训练' : '未训练'}
                    </div>
                </div>
                <div class="tv-stat-item">
                    <div class="tv-stat-label">备用预测</div>
                    <div class="tv-stat-value">${stats.fallback_predictions || 0}</div>
                </div>
            </div>
            <div class="tv-flex tv-justify-center">
                <button class="tv-btn tv-btn-primary tv-btn-sm" onclick="loadMLPredictions()">
                    <span class="tv-btn-icon">⚡</span> 查看预测
                </button>
            </div>
        `;
    } else {
        mlContainer.innerHTML = `
            <div class="tv-flex tv-flex-col tv-items-center tv-justify-center tv-py-4">
                <div class="tv-icon tv-icon-warning tv-mb-2">
                    ⚠️
                </div>
                <div class="tv-text tv-text-secondary">机器学习模块不可用</div>
            </div>
        `;
    }
}

/**
 * 加载机器学习预测
 */
async function loadMLPredictions() {
    try {
        const response = await fetch('/api/ml/predictions?top_n=5');
        const data = await response.json();
        
        if (data.status === '成功') {
            showMLPredictions(data);
        } else {
            showNotification('加载预测失败: ' + data.message, 'warning');
        }
    } catch (error) {
        console.error('加载预测时出错:', error);
        showNotification('加载预测时出错: ' + error.message, 'danger');
    }
}

/**
 * 显示机器学习预测
 */
function showMLPredictions(data) {
    const predictions = data.predictions || [];
    
    if (predictions.length === 0) {
        showNotification('暂无预测数据', 'info');
        return;
    }
    
    // 创建预测列表 - 使用TradingView样式
    let predictionList = '<div class="tv-list">';
    predictions.forEach((pred, index) => {
        const confidencePercent = (pred.confidence * 100).toFixed(1);
        const functionName = pred.predicted_value || pred.target || '未知功能';
        const explanation = pred.explanation || '基于历史使用模式';
        
        // 根据置信度设置徽章类名
        let badgeClass = 'tv-badge tv-badge-info';
        if (pred.confidence >= 0.8) {
            badgeClass = 'tv-badge tv-badge-success';
        } else if (pred.confidence >= 0.6) {
            badgeClass = 'tv-badge tv-badge-warning';
        }
        
        predictionList += `
            <div class="tv-list-item">
                <div class="tv-flex tv-justify-between tv-items-center tv-mb-1">
                    <span class="tv-text-primary">${index + 1}. ${functionName}</span>
                    <span class="${badgeClass}">${confidencePercent}%</span>
                </div>
                <div class="tv-text-secondary tv-text-sm">${explanation}</div>
            </div>
        `;
    });
    predictionList += '</div>';
    
    // 显示模态框 - 使用TradingView样式
    const modalHtml = `
        <div class="tv-modal" id="mlPredictionsModal" tabindex="-1">
            <div class="tv-modal-overlay"></div>
            <div class="tv-modal-dialog tv-modal-centered">
                <div class="tv-modal-content">
                    <div class="tv-modal-header">
                        <h5 class="tv-modal-title">
                            <span class="tv-modal-icon">⚡</span> 功能预测
                        </h5>
                        <button type="button" class="tv-modal-close" data-dismiss="tv-modal">&times;</button>
                    </div>
                    <div class="tv-modal-body">
                        <p class="tv-text-secondary tv-mb-3">根据历史使用模式预测用户下一步可能使用的功能：</p>
                        ${predictionList}
                    </div>
                    <div class="tv-modal-footer">
                        <button type="button" class="tv-btn tv-btn-secondary" data-dismiss="tv-modal">关闭</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // 添加模态框到页面
    const modalContainer = document.createElement('div');
    modalContainer.innerHTML = modalHtml;
    document.body.appendChild(modalContainer);
    
    // 获取模态框元素
    const modalElement = document.getElementById('mlPredictionsModal');
    
    // 显示模态框
    setTimeout(() => {
        modalElement.classList.add('tv-show');
        modalElement.style.display = 'block';
    }, 10);
    
    // 关闭按钮事件
    const closeButton = modalElement.querySelector('.tv-modal-close');
    const footerCloseButton = modalElement.querySelector('.tv-modal-footer .tv-btn[data-dismiss="tv-modal"]');
    
    function closeModal() {
        modalElement.classList.remove('tv-show');
        setTimeout(() => {
            if (modalContainer.parentNode) {
                modalContainer.remove();
            }
        }, 300);
    }
    
    if (closeButton) {
        closeButton.addEventListener('click', closeModal);
    }
    
    if (footerCloseButton) {
        footerCloseButton.addEventListener('click', closeModal);
    }
    
    // 点击遮罩层关闭
    const overlay = modalElement.querySelector('.tv-modal-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeModal);
    }
    
    // ESC键关闭
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape' && modalElement.classList.contains('tv-show')) {
            closeModal();
            document.removeEventListener('keydown', escHandler);
        }
    });
}

/**
 * 启动系统
 */
async function startSystem() {
    try {
        const response = await fetch('/api/system/control/start', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === '成功') {
            showNotification('系统启动成功', 'success');
            // 刷新系统状态
            setTimeout(() => loadSystemStatus(), 1000);
        } else {
            showNotification('系统启动失败: ' + data.message, 'danger');
        }
    } catch (error) {
        console.error('启动系统时出错:', error);
        showNotification('启动系统时出错: ' + error.message, 'danger');
    }
}

/**
 * 停止系统
 */
async function stopSystem() {
    if (!confirm('确定要停止自我进化系统吗？')) {
        return;
    }
    
    try {
        const response = await fetch('/api/system/control/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.status === '成功') {
            showNotification('系统停止成功', 'success');
            // 刷新系统状态
            setTimeout(() => loadSystemStatus(), 1000);
        } else {
            showNotification('系统停止失败: ' + data.message, 'danger');
        }
    } catch (error) {
        console.error('停止系统时出错:', error);
        showNotification('停止系统时出错: ' + error.message, 'danger');
    }
}