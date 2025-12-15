// 主JavaScript文件

// 页面加载完成后执行
$(document).ready(function() {
    // 初始化所有功能
    initDashboard();
    initDevices();
    initAlerts();
    initTraffic();
    initSettings();
});

// 仪表盘初始化
function initDashboard() {
    // 定时更新仪表盘数据
    if (window.location.pathname === '/dashboard') {
        setInterval(function() {
            updateDashboardData();
        }, 30000); // 每30秒更新一次
    }
}

// 设备管理初始化
function initDevices() {
    // 如果是设备页面，初始化设备列表
    if (window.location.pathname === '/devices') {
        // 这里可以添加设备列表的交互逻辑
        initDeviceFilters();
        initDeviceActions();
    }
}

// 告警管理初始化
function initAlerts() {
    // 如果是告警页面，初始化告警列表
    if (window.location.pathname === '/alerts') {
        // 这里可以添加告警列表的交互逻辑
        initAlertFilters();
        initAlertActions();
    }
}

// 流量监控初始化
function initTraffic() {
    // 如果是流量页面，初始化流量图表
    if (window.location.pathname === '/traffic') {
        // 这里可以添加流量图表的初始化逻辑
        initTrafficCharts();
    }
}

// 设置页面初始化
function initSettings() {
    // 如果是设置页面，初始化表单
    if (window.location.pathname === '/settings') {
        // 这里可以添加设置页面的交互逻辑
        initSettingForms();
    }
}

// 更新仪表盘数据
function updateDashboardData() {
    // 从API获取最新数据并更新页面
    $.ajax({
        url: '/api/status',
        type: 'GET',
        success: function(response) {
            if (response.success) {
                // 更新状态数据
                updateStatusIndicators(response.data);
            }
        },
        error: function(xhr, status, error) {
            console.error('Failed to update dashboard data:', error);
        }
    });
}

// 更新状态指示器
function updateStatusIndicators(data) {
    // 这里可以添加状态指示器的更新逻辑
    // 例如：更新设备在线数量、告警数量等
}

// 初始化设备过滤器
function initDeviceFilters() {
    // 设备过滤逻辑
}

// 初始化设备操作
function initDeviceActions() {
    // 设备隔离、释放等操作逻辑
}

// 初始化告警过滤器
function initAlertFilters() {
    // 告警过滤逻辑
}

// 初始化告警操作
function initAlertActions() {
    // 告警确认、解决等操作逻辑
}

// 初始化流量图表
function initTrafficCharts() {
    // 流量图表初始化逻辑
}

// 初始化设置表单
function initSettingForms() {
    // 设置表单交互逻辑
}

// 通用函数：显示成功消息
function showSuccessMessage(message) {
    alert(message || '操作成功');
}

// 通用函数：显示错误消息
function showErrorMessage(message) {
    alert(message || '操作失败');
}

// 通用函数：加载状态指示器
function showLoading(element) {
    $(element).append('<div class="loading-indicator"></div>');
}

function hideLoading(element) {
    $(element).find('.loading-indicator').remove();
}

// 通用函数：格式化日期时间
function formatDateTime(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

// 通用函数：格式化大小（字节转KB/MB/GB）
function formatSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 通用函数：获取IP地址类型
function getIpAddressType(ip) {
    if (!ip) return '';
    
    if (ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.16.')) {
        return 'local';
    } else {
        return 'public';
    }
}

// 通用函数：检查是否为移动设备
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

// 响应式调整
$(window).resize(function() {
    // 窗口大小变化时的调整逻辑
    if (window.location.pathname === '/traffic') {
        // 重新调整流量图表大小
        resizeTrafficCharts();
    }
});

// 调整流量图表大小
function resizeTrafficCharts() {
    // 流量图表大小调整逻辑
}
