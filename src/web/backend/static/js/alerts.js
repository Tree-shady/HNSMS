// 告警页面专用脚本

// 告警状态更新间隔（毫秒）
const ALERT_REFRESH_INTERVAL = 5000;

// 页面加载完成后执行
$(document).ready(function() {
    // 加载告警列表
    loadAlerts();
    
    // 绑定事件
    $('#refresh-alerts').click(loadAlerts);
    $('#search-btn').click(searchAlerts);
    $('#alert-search').keypress(function(e) {
        if (e.which === 13) {
            searchAlerts();
        }
    });
    $('#alert-status-filter').change(filterAlerts);
    
    // 批量操作事件
    $('#acknowledge-all-new').click(acknowledgeAllNew);
    $('#close-all-resolved').click(closeAllResolved);
    
    // 模态框关闭事件
    $('#alert-detail-modal').on('hidden.bs.modal', function() {
        $('#alert-detail-content').empty();
    });
    
    // 启动自动刷新
    startAutoRefresh();
    
    // 检查是否有未处理告警
    checkUnacknowledgedAlerts();
});

// 启动自动刷新
function startAutoRefresh() {
    setInterval(function() {
        // 只在当前页面是告警页面时自动刷新
        if (window.location.pathname.endsWith('/alerts')) {
            loadAlerts();
        }
    }, ALERT_REFRESH_INTERVAL);
}

// 加载告警列表
function loadAlerts() {
    $.getJSON('/api/alerts', function(data) {
        if (data.success) {
            const alerts = data.data.alerts;
            const tbody = $('#alerts-list');
            
            tbody.empty();
            $('#alert-count').text(`共 ${alerts.length} 个告警`);
            
            if (alerts.length === 0) {
                tbody.append('<tr><td colspan="7" class="text-center">暂无告警</td></tr>');
                return;
            }
            
            alerts.forEach(alert => {
                const statusClass = {
                    'new': 'badge bg-danger',
                    'acknowledged': 'badge bg-warning',
                    'resolved': 'badge bg-success',
                    'closed': 'badge bg-secondary'
                }[alert.status] || 'badge bg-secondary';
                
                const datetime = new Date(alert.timestamp * 1000).toLocaleString();
                
                tbody.append(`
                    <tr data-alert-id="${alert.alert_id}">
                        <td>${datetime}</td>
                        <td>${alert.alert_type}</td>
                        <td>${alert.severity}</td>
                        <td>${alert.source}</td>
                        <td>${alert.description}</td>
                        <td><span class="${statusClass}">${alert.status}</span></td>
                        <td>
                            <div class="btn-group" role="group">
                                <button class="btn btn-sm btn-info view-alert" data-alert-id="${alert.alert_id}">
                                    <i class="fa fa-eye"></i>
                                </button>
                                <button class="btn btn-sm btn-primary acknowledge-alert" data-alert-id="${alert.alert_id}">
                                    <i class="fa fa-check"></i>
                                </button>
                                <button class="btn btn-sm btn-success resolve-alert" data-alert-id="${alert.alert_id}">
                                    <i class="fa fa-check-circle"></i>
                                </button>
                                <button class="btn btn-sm btn-danger close-alert" data-alert-id="${alert.alert_id}">
                                    <i class="fa fa-times"></i>
                                </button>
                            </div>
                        </td>
                    </tr>
                `);
            });
            
            // 绑定查看告警详情事件
            $('.view-alert').click(function() {
                const alertId = $(this).data('alert-id');
                loadAlertDetail(alertId);
            });
            
            // 绑定告警操作事件
            $('.acknowledge-alert').click(function() {
                const alertId = $(this).data('alert-id');
                acknowledgeAlert(alertId);
            });
            
            $('.resolve-alert').click(function() {
                const alertId = $(this).data('alert-id');
                resolveAlert(alertId);
            });
            
            $('.close-alert').click(function() {
                const alertId = $(this).data('alert-id');
                closeAlert(alertId);
            });
        }
    });
}

// 搜索告警
function searchAlerts() {
    const keyword = $('#alert-search').val().toLowerCase();
    const statusFilter = $('#alert-status-filter').val();
    const rows = $('#alerts-table tbody tr');
    
    rows.each(function() {
        const text = $(this).text().toLowerCase();
        const alertId = $(this).data('alert-id');
        const status = $(this).find('.badge').text().toLowerCase();
        
        const matchesKeyword = text.includes(keyword);
        const matchesStatus = statusFilter === 'all' || status === statusFilter;
        
        $(this).toggle(matchesKeyword && matchesStatus);
    });
}

// 筛选告警
function filterAlerts() {
    searchAlerts(); // 复用搜索函数，因为它已经包含了状态筛选逻辑
}

// 加载告警详情
function loadAlertDetail(alertId) {
    $.getJSON('/api/alerts', function(data) {
        if (data.success) {
            const alerts = data.data.alerts;
            const alert = alerts.find(a => a.alert_id === alertId);
            
            if (alert) {
                const content = $('#alert-detail-content');
                const datetime = new Date(alert.timestamp * 1000).toLocaleString();
                
                content.html(`
                    <div class="row">
                        <div class="col-md-6">
                            <h6>基本信息</h6>
                            <table class="table table-sm">
                                <tbody>
                                    <tr>
                                        <td>告警ID</td>
                                        <td>${alert.alert_id}</td>
                                    </tr>
                                    <td>时间</td>
                                    <td>${datetime}</td>
                                    </tr>
                                    <tr>
                                        <td>类型</td>
                                        <td>${alert.alert_type}</td>
                                    </tr>
                                    <tr>
                                        <td>严重程度</td>
                                        <td>${alert.severity}</td>
                                    </tr>
                                    <tr>
                                        <td>来源</td>
                                        <td>${alert.source}</td>
                                    </tr>
                                    <tr>
                                        <td>状态</td>
                                        <td>
                                            <span class="badge bg-${(
                                                {
                                                    'new': 'danger',
                                                    'acknowledged': 'warning',
                                                    'resolved': 'success',
                                                    'closed': 'secondary'
                                                }[alert.status] || 'secondary'
                                            )}">${alert.status}</span>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6>告警详情</h6>
                            <table class="table table-sm">
                                <tbody>
                                    <tr>
                                        <td>描述</td>
                                        <td>${alert.description}</td>
                                    </tr>
                                    <tr>
                                        <td>详细信息</td>
                                        <td>
                                            <pre class="small">${JSON.stringify(alert.details, null, 2)}</pre>
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                `);
                
                // 显示模态框
                const modal = new bootstrap.Modal('#alert-detail-modal');
                modal.show();
                
                // 绑定告警操作按钮事件
                $('#acknowledge-alert-btn').off('click').click(function() {
                    acknowledgeAlert(alertId);
                    const modal = bootstrap.Modal.getInstance('#alert-detail-modal');
                    modal.hide();
                });
                
                $('#resolve-alert-btn').off('click').click(function() {
                    resolveAlert(alertId);
                    const modal = bootstrap.Modal.getInstance('#alert-detail-modal');
                    modal.hide();
                });
                
                $('#close-alert-btn').off('click').click(function() {
                    closeAlert(alertId);
                    const modal = bootstrap.Modal.getInstance('#alert-detail-modal');
                    modal.hide();
                });
            }
        }
    });
}

// 确认告警
function acknowledgeAlert(alertId) {
    $.ajax({
        url: `/api/alerts/${alertId}/acknowledge`,
        type: 'POST',
        success: function(data) {
            if (data.success) {
                loadAlerts();
                // 检查是否还有未处理告警
                checkUnacknowledgedAlerts();
            } else {
                alert('确认告警失败: ' + data.error);
            }
        },
        error: function() {
            alert('确认告警失败，请检查网络连接');
        }
    });
}

// 解决告警
function resolveAlert(alertId) {
    $.ajax({
        url: `/api/alerts/${alertId}/resolve`,
        type: 'POST',
        success: function(data) {
            if (data.success) {
                loadAlerts();
                // 检查是否还有未处理告警
                checkUnacknowledgedAlerts();
            } else {
                alert('解决告警失败: ' + data.error);
            }
        },
        error: function() {
            alert('解决告警失败，请检查网络连接');
        }
    });
}

// 关闭告警
function closeAlert(alertId) {
    $.ajax({
        url: `/api/alerts/${alertId}/close`,
        type: 'POST',
        success: function(data) {
            if (data.success) {
                loadAlerts();
                // 检查是否还有未处理告警
                checkUnacknowledgedAlerts();
            } else {
                alert('关闭告警失败: ' + data.error);
            }
        },
        error: function() {
            alert('关闭告警失败，请检查网络连接');
        }
    });
}

// 确认所有新告警
function acknowledgeAllNew() {
    if (confirm('确定要确认所有新告警吗？')) {
        $.getJSON('/api/alerts', function(data) {
            if (data.success) {
                const newAlerts = data.data.alerts.filter(a => a.status === 'new');
                let count = 0;
                let completed = 0;
                
                newAlerts.forEach(alert => {
                    acknowledgeAlert(alert.alert_id);
                    count++;
                });
                
                // 延迟显示提示，确保所有操作都已完成
                setTimeout(function() {
                    alert(`已确认 ${count} 个新告警`);
                    // 检查是否还有未处理告警
                    checkUnacknowledgedAlerts();
                }, 1000);
            }
        });
    }
}

// 关闭所有已解决告警
function closeAllResolved() {
    if (confirm('确定要关闭所有已解决告警吗？')) {
        $.getJSON('/api/alerts', function(data) {
            if (data.success) {
                const resolvedAlerts = data.data.alerts.filter(a => a.status === 'resolved');
                let count = 0;
                
                resolvedAlerts.forEach(alert => {
                    closeAlert(alert.alert_id);
                    count++;
                });
                
                // 延迟显示提示，确保所有操作都已完成
                setTimeout(function() {
                    alert(`已关闭 ${count} 个已解决告警`);
                    // 检查是否还有未处理告警
                    checkUnacknowledgedAlerts();
                }, 1000);
            }
        });
    }
}

// 检查是否有未处理告警
function checkUnacknowledgedAlerts() {
    $.getJSON('/api/alerts', function(data) {
        if (data.success) {
            const alerts = data.data.alerts;
            const unacknowledgedAlerts = alerts.filter(a => a.status === 'new' || a.status === 'acknowledged');
            
            // 更新页面标题，显示未处理告警数量
            if (unacknowledgedAlerts.length > 0) {
                document.title = `告警中心 (${unacknowledgedAlerts.length} 未处理)`;
            } else {
                document.title = '告警中心';
            }
        }
    });
}