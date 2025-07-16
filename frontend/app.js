// AI 时间管理系统 - 前端 JavaScript

class AITimeManager {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentDate = new Date().toISOString().split('T')[0];
        this.currentWeek = 1;
        this.isLoading = false;
        
        this.init();
    }

    // 初始化
    init() {
        this.bindEvents();
        this.checkConnection();
        this.setCurrentDate();
        this.loadCurrentData();
    }

    // 绑定事件
    bindEvents() {
        // 导航按钮
        document.getElementById('chatBtn').addEventListener('click', () => this.showPage('chat'));
        document.getElementById('dailyBtn').addEventListener('click', () => this.showPage('daily'));
        document.getElementById('weeklyBtn').addEventListener('click', () => this.showPage('weekly'));

        // 聊天功能
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 快捷按钮
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.dataset.message;
                document.getElementById('chatInput').value = message;
                this.sendMessage();
            });
        });

        // 日期控制
        document.getElementById('dateSelector').addEventListener('change', (e) => {
            this.currentDate = e.target.value;
            this.loadDailyTasks();
        });
        
        document.getElementById('prevDay').addEventListener('click', () => this.changeDate(-1));
        document.getElementById('nextDay').addEventListener('click', () => this.changeDate(1));
        document.getElementById('todayBtn').addEventListener('click', () => {
            this.currentDate = new Date().toISOString().split('T')[0];
            document.getElementById('dateSelector').value = this.currentDate;
            this.loadDailyTasks();
        });

        // 周控制
        document.getElementById('prevWeek').addEventListener('click', () => this.changeWeek(-1));
        document.getElementById('nextWeek').addEventListener('click', () => this.changeWeek(1));
        document.getElementById('currentWeekBtn').addEventListener('click', () => {
            this.currentWeek = this.getCurrentWeek();
            this.updateWeekDisplay();
            this.loadWeeklyTasks();
        });

        // 工具面板关闭
        document.getElementById('closeToolsBtn').addEventListener('click', () => {
            document.getElementById('toolsPanel').classList.add('hidden');
        });
    }

    // 页面切换
    showPage(pageName) {
        // 隐藏所有页面
        document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
        document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));

        // 显示目标页面
        document.getElementById(`${pageName}Page`).classList.add('active');
        document.getElementById(`${pageName}Btn`).classList.add('active');

        // 根据页面加载数据
        switch(pageName) {
            case 'daily':
                this.loadDailyTasks();
                break;
            case 'weekly':
                this.loadWeeklyTasks();
                break;
        }
    }

    // 检查连接状态
    async checkConnection() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            if (response.ok) {
                this.updateConnectionStatus(true);
            } else {
                this.updateConnectionStatus(false);
            }
        } catch (error) {
            this.updateConnectionStatus(false);
        }
    }

    // 更新连接状态
    updateConnectionStatus(isOnline) {
        const statusElement = document.getElementById('connectionStatus');
        if (isOnline) {
            statusElement.textContent = '在线';
            statusElement.className = 'status online';
        } else {
            statusElement.textContent = '离线';
            statusElement.className = 'status offline';
        }
    }

    // 设置当前日期
    setCurrentDate() {
        document.getElementById('dateSelector').value = this.currentDate;
        this.currentWeek = this.getCurrentWeek();
        this.updateWeekDisplay();
    }

    // 获取当前周数
    getCurrentWeek() {
        const now = new Date();
        const start = new Date(now.getFullYear(), 0, 1);
        const days = Math.floor((now - start) / (24 * 60 * 60 * 1000));
        return Math.ceil((days + start.getDay() + 1) / 7);
    }

    // 发送消息
    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message || this.isLoading) return;

        // 清空输入框
        input.value = '';
        
        // 显示用户消息
        this.addMessage(message, 'user');
        
        // 显示加载状态
        this.setLoading(true);

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/chat/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: 'default'
                })
            });

            const data = await response.json();

            if (data.success) {
                // 显示 AI 响应
                this.addMessage(data.response, 'bot', data.tools_used);
                
                // 如果使用了工具，显示工具面板
                if (data.tools_used && data.tools_used.length > 0) {
                    this.showToolsPanel(data.tools_used);
                }

                // 刷新数据（AI 可能已修改了计划）
                this.loadCurrentData();
            } else {
                this.addMessage('抱歉，处理您的请求时出现了错误。', 'bot');
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.addMessage('连接服务器失败，请检查网络连接。', 'bot');
        } finally {
            this.setLoading(false);
        }
    }

    // 添加消息到聊天界面
    addMessage(content, type, tools = []) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const currentTime = new Date().toLocaleString('zh-CN');
        
        let toolsHtml = '';
        if (tools && tools.length > 0) {
            toolsHtml = `
                <div class="tools-used">
                    <h4>🔧 调用的工具:</h4>
                    ${tools.map(tool => `<span class="tool-item">${tool}</span>`).join('')}
                </div>
            `;
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                <strong>${type === 'user' ? '您' : 'AI 助手'}:</strong> ${content}
                ${toolsHtml}
            </div>
            <div class="message-time">${currentTime}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // 显示工具面板
    showToolsPanel(tools) {
        const toolsList = document.getElementById('toolsList');
        toolsList.innerHTML = tools.map(tool => `
            <div class="tool-item">${tool}</div>
        `).join('');
        
        document.getElementById('toolsPanel').classList.remove('hidden');
        
        // 3秒后自动隐藏
        setTimeout(() => {
            document.getElementById('toolsPanel').classList.add('hidden');
        }, 3000);
    }

    // 设置加载状态
    setLoading(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        const loadingIndicator = document.getElementById('loadingIndicator');
        
        if (loading) {
            sendBtn.disabled = true;
            sendBtn.textContent = '发送中...';
            loadingIndicator.classList.remove('hidden');
        } else {
            sendBtn.disabled = false;
            sendBtn.textContent = '发送';
            loadingIndicator.classList.add('hidden');
        }
    }

    // 加载当前数据
    async loadCurrentData() {
        await this.loadDailyTasks();
        await this.loadWeeklyTasks();
    }

    // 加载日计划
    async loadDailyTasks() {
        try {
            // 使用新的轻量级 API 获取所有数据
            const response = await fetch(`${this.apiBaseUrl}/api/data/current`);
            const data = await response.json();

            if (data.success) {
                const dailySchedules = data.data.daily_schedules || {};
                const tasks = dailySchedules[this.currentDate]?.tasks || [];
                this.renderDailyTasks(tasks);
            }
        } catch (error) {
            console.error('加载日计划失败:', error);
        }
    }

    // 渲染日计划
    renderDailyTasks(tasks) {
        const container = document.getElementById('dailyTasks');
        
        if (!tasks || tasks.length === 0) {
            container.innerHTML = `
                <div class="no-tasks">
                    <p>📝 ${this.currentDate} 没有安排任务</p>
                    <p>您可以通过 AI 对话来添加任务</p>
                </div>
            `;
            return;
        }

        // 按时间排序
        tasks.sort((a, b) => a.start_time.localeCompare(b.start_time));

        container.innerHTML = tasks.map(task => `
            <div class="task-item">
                <div class="task-header">
                    <div class="task-name">${task.task_name}</div>
                    <div class="task-time">${task.start_time} - ${task.end_time}</div>
                </div>
                <div class="task-description">${task.description}</div>
                <div class="task-meta">
                    ${task.can_reschedule ? '<span class="task-tag">🔄 可重排</span>' : ''}
                    ${task.can_compress ? '<span class="task-tag">⏰ 可压缩</span>' : ''}
                    ${task.can_parallel ? '<span class="task-tag">⚡ 可并行</span>' : ''}
                    ${task.parent_task ? `<span class="task-tag">📂 ${task.parent_task}</span>` : ''}
                </div>
            </div>
        `).join('');
    }

    // 加载周计划
    async loadWeeklyTasks() {
        try {
            // 使用新的轻量级 API 获取所有数据
            const response = await fetch(`${this.apiBaseUrl}/api/data/current`);
            const data = await response.json();

            if (data.success) {
                const weeklySchedules = data.data.weekly_schedules || {};
                const tasks = weeklySchedules[this.currentWeek]?.tasks || [];
                this.renderWeeklyTasks(tasks);
            }
        } catch (error) {
            console.error('加载周计划失败:', error);
        }
    }

    // 渲染周计划
    renderWeeklyTasks(tasks) {
        const container = document.getElementById('weeklyTasks');
        
        if (!tasks || tasks.length === 0) {
            container.innerHTML = `
                <div class="no-tasks">
                    <p>📋 第 ${this.currentWeek} 周没有安排任务</p>
                    <p>您可以通过 AI 对话来添加任务</p>
                </div>
            `;
            return;
        }

        // 按优先级排序
        const priorityOrder = { 'high': 3, 'medium': 2, 'low': 1 };
        tasks.sort((a, b) => priorityOrder[b.priority] - priorityOrder[a.priority]);

        container.innerHTML = tasks.map(task => `
            <div class="task-item">
                <div class="task-header">
                    <div class="task-name">${task.task_name}</div>
                    <div class="task-time priority-${task.priority}">
                        ${this.getPriorityText(task.priority)}
                    </div>
                </div>
                <div class="task-description">${task.description}</div>
                <div class="task-meta">
                    ${task.parent_project ? `<span class="task-tag">🏗️ ${task.parent_project}</span>` : ''}
                    <span class="task-tag priority-${task.priority}">
                        ${this.getPriorityIcon(task.priority)} ${this.getPriorityText(task.priority)}
                    </span>
                </div>
            </div>
        `).join('');
    }

    // 获取优先级文本
    getPriorityText(priority) {
        const map = {
            'high': '高优先级',
            'medium': '中优先级',
            'low': '低优先级'
        };
        return map[priority] || priority;
    }

    // 获取优先级图标
    getPriorityIcon(priority) {
        const map = {
            'high': '🔥',
            'medium': '⚡',
            'low': '📝'
        };
        return map[priority] || '📝';
    }

    // 改变日期
    changeDate(days) {
        const date = new Date(this.currentDate);
        date.setDate(date.getDate() + days);
        this.currentDate = date.toISOString().split('T')[0];
        document.getElementById('dateSelector').value = this.currentDate;
        this.loadDailyTasks();
    }

    // 改变周数
    changeWeek(weeks) {
        this.currentWeek += weeks;
        if (this.currentWeek < 1) this.currentWeek = 1;
        if (this.currentWeek > 53) this.currentWeek = 53;
        this.updateWeekDisplay();
        this.loadWeeklyTasks();
    }

    // 更新周显示
    updateWeekDisplay() {
        document.getElementById('weekRange').textContent = `第 ${this.currentWeek} 周`;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new AITimeManager();
});
