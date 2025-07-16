// AI 时间管理系统 - WebSocket 版本前端

// 全局错误处理
window.addEventListener('error', (e) => {
    console.error('全局 JavaScript 错误:', e.error);
    console.error('错误信息:', e.message);
    console.error('错误文件:', e.filename);
    console.error('错误行号:', e.lineno);
    console.error('错误堆栈:', e.error?.stack);
});

window.addEventListener('unhandledrejection', (e) => {
    console.error('未处理的 Promise 拒绝:', e.reason);
    console.error('Promise:', e.promise);
});

// 页面刷新检测
window.addEventListener('beforeunload', (e) => {
    console.warn('页面即将刷新/关闭！');
    console.trace('页面刷新调用栈');
});

window.addEventListener('unload', (e) => {
    console.warn('页面正在卸载！');
});

class AITimeManagerWS {
    constructor() {
        this.wsUrl = 'ws://localhost:8000/ws/chat';
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentDate = new Date().toISOString().split('T')[0];
        this.currentWeek = 1;
        this.isLoading = false;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 3000; // 3秒
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateDateDisplay();
        this.updateWeekDisplay();
        this.connectWebSocket();
        
        // 显示聊天页面
        this.showPage('chat');
    }

    // WebSocket 连接管理
    connectWebSocket() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            console.log('正在连接 WebSocket...');
            this.updateConnectionStatus('connecting');
            
            this.ws = new WebSocket(this.wsUrl);
            
            this.ws.onopen = (event) => {
                console.log('WebSocket 连接已建立');
                this.updateConnectionStatus('online');
                this.reconnectAttempts = 0;
            };
            
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('解析 WebSocket 消息失败:', error);
                }
            };
            
            this.ws.onclose = (event) => {
                console.log('WebSocket 连接已关闭', event);
                this.updateConnectionStatus('offline');
                
                // 尝试重连
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    console.log(`尝试重连 (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    setTimeout(() => this.connectWebSocket(), this.reconnectInterval);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error('WebSocket 错误:', error);
                this.updateConnectionStatus('error');
            };
            
        } catch (error) {
            console.error('创建 WebSocket 连接失败:', error);
            this.updateConnectionStatus('error');
        }
    }

    // 处理 WebSocket 消息
    handleWebSocketMessage(data) {
        console.log('收到 WebSocket 消息:', data);
        
        switch (data.type) {
            case 'system':
                this.addMessage(data.message, 'system');
                break;
                
            case 'user_message':
                // 用户消息确认，不需要再次显示
                break;
                
            case 'processing':
                this.setLoading(true);
                this.addMessage(data.message, 'system');
                break;
                
            case 'ai_response':
                this.setLoading(false);
                this.addMessage(data.message, 'bot', data.tools_used);
                
                // 如果使用了工具，显示工具面板
                if (data.tools_used && data.tools_used.length > 0) {
                    this.showToolsPanel(data.tools_used);
                }
                
                // 刷新数据
                this.loadCurrentData();
                break;
                
            case 'error':
                this.setLoading(false);
                this.addMessage(data.message, 'error');
                break;
                
            default:
                console.log('未知消息类型:', data.type);
        }
    }

    // 更新连接状态
    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connectionStatus');
        const statusElement2 = document.getElementById('connectionStatus2');
        
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
            
            switch (status) {
                case 'online':
                    statusElement.textContent = '在线';
                    break;
                case 'offline':
                    statusElement.textContent = '离线';
                    break;
                case 'connecting':
                    statusElement.textContent = '连接中';
                    break;
                case 'error':
                    statusElement.textContent = '错误';
                    break;
            }
        }
        
        if (statusElement2) {
            statusElement2.className = `connection-status ${status}`;
            
            switch (status) {
                case 'online':
                    statusElement2.textContent = 'WebSocket: 在线';
                    break;
                case 'offline':
                    statusElement2.textContent = 'WebSocket: 离线';
                    break;
                case 'connecting':
                    statusElement2.textContent = 'WebSocket: 连接中';
                    break;
                case 'error':
                    statusElement2.textContent = 'WebSocket: 错误';
                    break;
            }
        }
    }

    setupEventListeners() {
        // 导航按钮
        document.getElementById('chatBtn').addEventListener('click', () => this.showPage('chat'));
        document.getElementById('dailyBtn').addEventListener('click', () => this.showPage('daily'));
        document.getElementById('weeklyBtn').addEventListener('click', () => this.showPage('weekly'));

        // 聊天功能
        document.getElementById('sendBtn').addEventListener('click', (e) => {
            console.log('发送按钮被点击');
            e.preventDefault();
            e.stopPropagation();
            this.sendMessage();
        });
        
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                console.log('Enter 键被按下');
                e.preventDefault();
                e.stopPropagation();
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
            this.updateDateDisplay();
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

    // 发送 WebSocket 消息
    sendMessage() {
        try {
            console.log('sendMessage 函数被调用');
            
            const input = document.getElementById('chatInput');
            const message = input.value.trim();
            
            console.log('输入消息:', message);
            
            if (!message || this.isLoading) {
                console.log('消息为空或正在加载中，返回');
                return;
            }

            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.addMessage('WebSocket 连接未建立，正在尝试重连...', 'error');
                this.connectWebSocket();
                return;
            }

            // 清空输入框
            input.value = '';
            
            // 显示用户消息
            console.log('添加用户消息到界面');
            this.addMessage(message, 'user');
            
            // 通过 WebSocket 发送消息
            const messageData = {
                type: 'chat',
                message: message,
                session_id: 'default',
                timestamp: new Date().toISOString()
            };
            
            try {
                this.ws.send(JSON.stringify(messageData));
                console.log('消息已通过 WebSocket 发送');
            } catch (wsError) {
                console.error('发送 WebSocket 消息失败:', wsError);
                this.addMessage('发送消息失败，请重试', 'error');
            }
            
        } catch (error) {
            console.error('sendMessage 函数执行出错:', error);
            console.error('错误堆栈:', error.stack);
            this.addMessage('发送消息时出现错误: ' + error.message, 'error');
        }
    }

    // 添加消息到聊天界面
    addMessage(content, type, tools = []) {
        console.log('addMessage 被调用:', { content, type, tools });
        
        const messagesContainer = document.getElementById('chatMessages');
        console.log('消息容器:', messagesContainer);
        console.log('消息容器是否存在:', !!messagesContainer);
        console.log('消息容器内容长度:', messagesContainer ? messagesContainer.children.length : 'N/A');
        
        if (!messagesContainer) {
            console.error('找不到消息容器 #chatMessages');
            return;
        }
        
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

        let displayName;
        switch (type) {
            case 'user':
                displayName = '您';
                break;
            case 'bot':
                displayName = 'AI 助手';
                break;
            case 'system':
                displayName = '系统';
                break;
            case 'error':
                displayName = '错误';
                break;
            default:
                displayName = type;
        }

        messageDiv.innerHTML = `
            <div class="message-content">
                <strong>${displayName}:</strong> ${content.replace(/\n/g, '<br>')}
                ${toolsHtml}
            </div>
            <div class="message-time">${currentTime}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // 设置加载状态
    setLoading(loading) {
        this.isLoading = loading;
        const sendBtn = document.getElementById('sendBtn');
        const chatInput = document.getElementById('chatInput');
        
        if (loading) {
            sendBtn.textContent = '发送中...';
            sendBtn.disabled = true;
            chatInput.disabled = true;
        } else {
            sendBtn.textContent = '发送';
            sendBtn.disabled = false;
            chatInput.disabled = false;
        }
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

    // 显示工具面板
    showToolsPanel(tools) {
        const toolsPanel = document.getElementById('toolsPanel');
        const toolsList = document.getElementById('toolsList');
        
        toolsList.innerHTML = tools.map(tool => `
            <div class="tool-item">
                <h4>${tool}</h4>
                <p>工具已执行完成</p>
            </div>
        `).join('');
        
        toolsPanel.classList.remove('hidden');
    }

    // 日期相关方法
    updateDateDisplay() {
        document.getElementById('dateSelector').value = this.currentDate;
    }

    changeDate(days) {
        const date = new Date(this.currentDate);
        date.setDate(date.getDate() + days);
        this.currentDate = date.toISOString().split('T')[0];
        this.updateDateDisplay();
        this.loadDailyTasks();
    }

    // 周相关方法
    getCurrentWeek() {
        const now = new Date();
        const start = new Date(now.getFullYear(), 0, 1);
        return Math.ceil(((now - start) / 86400000 + start.getDay() + 1) / 7);
    }

    updateWeekDisplay() {
        document.getElementById('weekSelector').textContent = `第 ${this.currentWeek} 周`;
    }

    changeWeek(weeks) {
        this.currentWeek = Math.max(1, this.currentWeek + weeks);
        this.updateWeekDisplay();
        this.loadWeeklyTasks();
    }

    // 数据加载方法（使用 HTTP API）
    async loadCurrentData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/data/current`);
            const data = await response.json();
            
            if (data.success) {
                // 可以根据需要处理数据
                console.log('当前数据已更新:', data);
            }
        } catch (error) {
            console.error('加载当前数据失败:', error);
        }
    }

    async loadDailyTasks() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/tasks/daily?date=${this.currentDate}`);
            const data = await response.json();
            
            const container = document.getElementById('dailyTasks');
            if (data.success && data.tasks && data.tasks.length > 0) {
                container.innerHTML = data.tasks.map(task => `
                    <div class="task-item">
                        <h4>${task.task_name}</h4>
                        <p>⏰ ${task.start_time} - ${task.end_time}</p>
                        <p>${task.description || '暂无描述'}</p>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="no-tasks">
                        <p>📝 当前日期没有安排任务</p>
                        <p>您可以通过 AI 对话来添加任务</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载日任务失败:', error);
        }
    }

    async loadWeeklyTasks() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/tasks/weekly?week=${this.currentWeek}`);
            const data = await response.json();
            
            const container = document.getElementById('weeklyTasks');
            if (data.success && data.tasks && data.tasks.length > 0) {
                container.innerHTML = data.tasks.map(task => `
                    <div class="task-item">
                        <h4>${task.task_name}</h4>
                        <p>📅 第 ${task.week_number} 周</p>
                        <p>${task.description || '暂无描述'}</p>
                    </div>
                `).join('');
            } else {
                container.innerHTML = `
                    <div class="no-tasks">
                        <p>📝 当前周没有安排任务</p>
                        <p>您可以通过 AI 对话来添加任务</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('加载周任务失败:', error);
        }
    }
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    console.log('页面加载完成，初始化 WebSocket 版本的 AI 时间管理系统');
    console.log('检查 DOM 元素:');
    console.log('- chatMessages:', document.getElementById('chatMessages'));
    console.log('- sendBtn:', document.getElementById('sendBtn'));
    console.log('- chatInput:', document.getElementById('chatInput'));
    
    window.aiManager = new AITimeManagerWS();
});
