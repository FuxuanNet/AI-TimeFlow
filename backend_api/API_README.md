# AI 时间管理系统 - 后端 API 文档

## 概述

本 API 为 AI 时间管理系统提供完整的后端服务，支持与前端的完全分离，并通过 RESTful API 进行通信。

## 安装和启动

### 1. 安装依赖

```bash
# 进入后端目录
cd backend_api

# 安装 FastAPI 依赖
pip install fastapi uvicorn pydantic
```

### 2. 启动服务

```bash
# 推荐方法：使用启动脚本
python start_server.py

# 方法2：使用 uvicorn 直接启动
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 方法3：从项目根目录启动
cd ..
uvicorn backend_api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## API 端点一览

### 基础信息

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/` | API 欢迎信息 |
| GET | `/health` | 健康检查 |

### AI 聊天接口 (`/api/chat`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/chat/message` | 发送消息给 AI |
| GET | `/api/chat/history` | 获取聊天历史 |

### 任务管理接口 (`/api/tasks`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/tasks/daily` | 创建日任务 |
| GET | `/api/tasks/daily` | 获取日任务 |
| POST | `/api/tasks/weekly` | 创建周任务 |
| GET | `/api/tasks/weekly` | 获取周任务 |
| GET | `/api/tasks/statistics` | 获取统计信息 |

### 数据管理接口 (`/api/data`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/data/schedules/latest` | 获取最新时间表 |
| POST | `/api/data/export/frontend` | 导出前端数据 |
| GET | `/api/data/time-info` | 获取时间信息 |

## 详细 API 说明

### 1. AI 聊天接口

#### POST `/api/chat/message`

向 AI 发送消息并获取响应。

**请求体：**
```json
{
  "message": "请帮我安排今天的任务",
  "session_id": "user123"
}
```

**响应：**
```json
{
  "success": true,
  "message": "请帮我安排今天的任务",
  "response": "AI的回复内容",
  "tools_used": ["时间查询工具", "任务管理工具"],
  "timestamp": "2025-01-16T10:30:00",
  "session_id": "user123"
}
```

#### GET `/api/chat/history`

获取聊天历史记录。

**查询参数：**
- `session_id`: 会话ID (默认: "default")
- `limit`: 返回数量限制 (默认: 50)

**响应：**
```json
{
  "success": true,
  "history": [
    {
      "role": "user",
      "content": "用户消息",
      "timestamp": "2025-01-16T10:30:00"
    },
    {
      "role": "assistant", 
      "content": "AI回复",
      "timestamp": "2025-01-16T10:30:05"
    }
  ]
}
```

### 2. 任务管理接口

#### POST `/api/tasks/daily`

创建日任务。

**请求体：**
```json
{
  "task_name": "学习编程",
  "description": "学习 Python 基础",
  "date_str": "2025-01-16",
  "start_time": "09:00",
  "end_time": "11:00",
  "can_reschedule": true,
  "can_compress": true,
  "can_parallel": false,
  "parent_task": "编程学习计划"
}
```

**响应：**
```json
{
  "success": true,
  "message": "日任务 '学习编程' 创建成功",
  "task_data": {
    "task_name": "学习编程",
    "date_str": "2025-01-16",
    // ... 其他任务数据
  }
}
```

#### GET `/api/tasks/daily`

获取指定日期的日任务。

**查询参数：**
- `date_str`: 日期字符串 (YYYY-MM-DD) [必需]

**响应：**
```json
{
  "success": true,
  "date": "2025-01-16",
  "tasks": [
    {
      "task_name": "学习编程",
      "start_time": "09:00",
      "end_time": "11:00",
      // ... 其他任务信息
    }
  ],
  "count": 1
}
```

#### POST `/api/tasks/weekly`

创建周任务。

**请求体：**
```json
{
  "task_name": "完成项目文档",
  "description": "编写项目技术文档",
  "week_number": 3,
  "parent_project": "AI时间管理系统",
  "priority": "high"
}
```

**响应：**
```json
{
  "success": true,
  "message": "周任务 '完成项目文档' 创建成功",
  "task_data": {
    "task_name": "完成项目文档",
    "week_number": 3,
    // ... 其他任务数据
  }
}
```

#### GET `/api/tasks/weekly`

获取指定周的周任务。

**查询参数：**
- `week_number`: 周数 [必需]

**响应：**
```json
{
  "success": true,
  "week_number": 3,
  "tasks": [
    {
      "task_name": "完成项目文档",
      "priority": "high",
      // ... 其他任务信息
    }
  ],
  "count": 1
}
```

#### GET `/api/tasks/statistics`

获取任务统计信息。

**响应：**
```json
{
  "success": true,
  "statistics": {
    "total_daily_tasks": 5,
    "total_weekly_tasks": 3,
    "completed_tasks": 2,
    "pending_tasks": 6
  },
  "timestamp": "2025-01-16T10:30:00"
}
```

### 3. 数据管理接口

#### GET `/api/data/schedules/latest`

获取最新的 AI 生成的时间表。

**响应：**
```json
{
  "success": true,
  "schedule": {
    "user_request": "帮我安排今天的学习计划",
    "ai_response": "AI生成的时间表内容",
    "timestamp": "2025-01-16T10:30:00",
    "metadata": {
      "total_tasks": 3,
      "time_span": "8小时"
    }
  },
  "source": "latest_schedule.json"
}
```

#### POST `/api/data/export/frontend`

为前端导出完整数据。

**响应：**
```json
{
  "success": true,
  "data": {
    "current_data": {
      "daily_schedules": {},
      "weekly_schedules": {},
      "statistics": {}
    },
    "ai_schedules": [
      {
        "timestamp": "2025-01-16T10:30:00",
        "content": "AI时间表内容"
      }
    ],
    "time_info": {
      "current_time": "2025-01-16 10:30:00",
      "week_number": 3
    }
  },
  "export_time": "2025-01-16T10:30:00"
}
```

#### GET `/api/data/time-info`

获取当前时间信息。

**响应：**
```json
{
  "success": true,
  "time_info": {
    "current_time": {
      "date": "2025-01-16",
      "time": "10:30:00",
      "weekday": "星期四"
    },
    "detailed_time": {
      "year": 2025,
      "month": 1,
      "day": 16,
      "hour": 10,
      "minute": 30
    },
    "week_progress": {
      "week_number": 3,
      "progress_percentage": 60
    },
    "timestamp": "2025-01-16T10:30:00"
  }
}
```

## 错误处理

所有 API 都使用标准的 HTTP 状态码：

- `200`: 成功
- `400`: 请求错误
- `404`: 资源未找到  
- `500`: 服务器内部错误

**错误响应格式：**
```json
{
  "detail": "错误描述信息"
}
```

## CORS 支持

API 已配置 CORS 中间件，支持跨域请求：
- 允许所有来源 (`*`)
- 支持所有 HTTP 方法
- 支持所有请求头

## 使用示例

### 使用 curl 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 发送聊天消息
curl -X POST "http://localhost:8000/api/chat/message" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好，请帮我安排今天的任务"}'

# 获取今天的任务
curl "http://localhost:8000/api/tasks/daily?date_str=2025-01-16"

# 创建日任务
curl -X POST "http://localhost:8000/api/tasks/daily" \
  -H "Content-Type: application/json" \
  -d '{
    "task_name": "学习编程",
    "description": "学习 Python",
    "date_str": "2025-01-16", 
    "start_time": "09:00",
    "end_time": "11:00"
  }'
```

### 使用 JavaScript 前端

```javascript
// 发送聊天消息
async function sendMessage(message) {
  const response = await fetch('http://localhost:8000/api/chat/message', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });
  
  const data = await response.json();
  return data;
}

// 获取任务列表
async function getDailyTasks(date) {
  const response = await fetch(`http://localhost:8000/api/tasks/daily?date_str=${date}`);
  const data = await response.json();
  return data.tasks;
}
```

## 注意事项

1. **数据持久化**: 所有数据存储在 JSON 文件中，重启服务不会丢失数据
2. **AI 集成**: API 完全集成现有的 AI Agent，保持功能一致性
3. **实时性**: 支持实时的 AI 对话和任务管理
4. **扩展性**: 模块化设计，易于添加新功能
5. **兼容性**: 保持与现有终端版本的完全兼容

## 开发和调试

- 使用 `--reload` 参数启动开发模式
- 访问 `/docs` 进行在线 API 测试
- 检查控制台日志了解详细信息
- 使用 `/health` 端点监控服务状态
