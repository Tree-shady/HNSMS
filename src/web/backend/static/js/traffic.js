// 流量监控页面脚本

// 固定的模拟数据，用于流量排名
const mockTopTalkers = [
    { "ip": "192.168.0.1", "bytes": 1000000, "packets": 1000 },
    { "ip": "192.168.0.2", "bytes": 500000, "packets": 500 },
    { "ip": "192.168.0.3", "bytes": 250000, "packets": 250 },
    { "ip": "192.168.0.4", "bytes": 125000, "packets": 125 },
    { "ip": "192.168.0.5", "bytes": 62500, "packets": 62 }
];

// 固定的协议分布数据
const mockProtocolDistribution = {
    "TCP": 1000,
    "UDP": 500,
    "ICMP": 250,
    "ARP": 100,
    "Other": 50
};

// 页面加载完成后初始化
$(document).ready(function() {
    // 初始化流量统计
    initTrafficStats();
    
    // 初始化流量排名
    initTopTalkers();
    
    // 初始化协议分布
    initProtocolDistribution();
    
    // 初始化流量图表
    initTrafficChart();
});

// 初始化流量统计
function initTrafficStats() {
    // 使用模拟数据更新流量统计
    const stats = {
        "inbound_bytes": 1000000,
        "inbound_packets": 10000,
        "outbound_bytes": 500000,
        "outbound_packets": 5000,
        "packets_per_second": 100,
        "total_bytes": 1500000,
        "total_packets": 15000,
        "traffic_rate": 102400
    };
    
    updateTrafficStats(stats);
}

// 更新流量统计显示
function updateTrafficStats(stats) {
    // 更新实时流量
    $('#inbound-traffic').text(formatBytes(stats.inbound_bytes));
    $('#outbound-traffic').text(formatBytes(stats.outbound_bytes));
    $('#total-traffic').text(formatBytes(stats.total_bytes));
    $('#packets-per-second').text(stats.packets_per_second);
}

// 初始化流量排名
function initTopTalkers() {
    // 直接使用模拟数据更新流量排名
    updateTopTalkers(mockTopTalkers);
}

// 更新流量排名显示
function updateTopTalkers(topTalkers) {
    const $tableBody = $('#top-talkers-table tbody');
    $tableBody.empty();
    
    // 添加每个Top Talker到表格
    topTalkers.forEach((talker, index) => {
        const $row = $('<tr></tr>');
        $row.append(`<td>${index + 1}</td>`);
        $row.append(`<td>${talker.ip}</td>`);
        $row.append(`<td>${formatBytes(talker.bytes)}</td>`);
        $row.append(`<td>${talker.packets}</td>`);
        $tableBody.append($row);
    });
}

// 初始化协议分布
function initProtocolDistribution() {
    // 直接使用模拟数据更新协议分布
    updateProtocolDistribution(mockProtocolDistribution);
}

// 更新协议分布显示
function updateProtocolDistribution(distribution) {
    const $chart = $('#protocol-chart');
    const $tableBody = $('#protocol-table tbody');
    
    // 清空现有的图表和表格
    $chart.empty();
    $tableBody.empty();
    
    // 准备数据用于图表
    const chartData = [];
    for (const [protocol, count] of Object.entries(distribution)) {
        chartData.push([protocol, count]);
        
        // 添加到表格
        const $row = $('<tr></tr>');
        $row.append(`<td>${protocol}</td>`);
        $row.append(`<td>${count}</td>`);
        $tableBody.append($row);
    }
    
    // 简单的文字图表展示
    $chart.append('<h4>协议分布</h4>');
    chartData.forEach(([protocol, count]) => {
        const barWidth = Math.min(count / 10, 100); // 限制最大宽度为100%
        $chart.append(`
            <div class="chart-item">
                <span class="chart-label">${protocol}:</span>
                <div class="chart-bar-container">
                    <div class="chart-bar" style="width: ${barWidth}%"></div>
                </div>
                <span class="chart-value">${count}</span>
            </div>
        `);
    });
}

// 初始化流量图表
function initTrafficChart() {
    // 简单的流量趋势图
    const $chart = $('#traffic-chart');
    $chart.append('<h4>流量趋势（最近5分钟）</h4>');
    $chart.append('<div class="chart-placeholder">流量趋势图将在后续版本中实现</div>');
}

// 格式化字节数
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const dm = decimals < 0 ? 0 : decimals;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
}
