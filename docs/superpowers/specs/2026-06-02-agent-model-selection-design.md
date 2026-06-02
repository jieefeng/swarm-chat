# Agent 模型选择功能设计

## 背景

当前系统只能选择 LLM Provider（平台），无法选择具体模型。每个 Provider 内的模型是硬编码的（如 `qwen3.5-plus-2026-04-20`），用户无法自定义。

## 目标

- 支持用户自定义输入任意模型名称
- 每个 Agent 独立配置模型
- 在聊天页面顶部显示并可切换当前 Agent 的模型
- 配置持久化到数据库

## 技术方案

### 1. 数据库层

#### 扩展 `agent_llm_config` 表

```sql
ALTER TABLE agent_llm_config ADD COLUMN model TEXT;
```

- `model` 列允许为 NULL（表示使用 Provider 默认模型）
- 为每个 Agent 预填充默认模型值

#### `llm_config_db.py` 新增方法

| 方法 | 说明 |
|------|------|
| `get_model(agent_id) -> Optional[str]` | 获取 Agent 的模型配置 |
| `update_model(agent_id, model) -> bool` | 更新 Agent 的模型 |
| `get_all_config() -> Dict` | 扩展返回 model 字段 |

### 2. 后端层

#### 修改 LLM Service

**`bailian.py` 和 `minimax.py`：**

- 构造函数接受可选 `model` 参数
- 提供 `get_default_model()` 类方法返回默认模型
- `send_message` 等方法使用实例的 `model` 属性

**`llm_router.py`：**

```python
def get_llm_service_for_provider(provider: str, model: Optional[str] = None):
    # 传入 model 参数给 Service 构造函数
```

**`session.py` 的 `send_to_agent`：**

```python
# 读取 model 配置
model = db.get_model(agent_id)

# 传给 LLM service
llm = get_llm_service_for_provider(provider, model=model)
```

### 3. 前端层

#### 聊天页面顶部新增模型显示/编辑

- 在 Agent 名称旁显示当前模型名称
- 点击模型名称变为可编辑输入框
- 失焦或回车时保存到后端
- 显示保存状态（loading / 成功 / 失败）

#### 新增 API 端点

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/agents/{id}/config` | 获取 Agent 的 LLM 配置（provider + model） |
| PUT | `/api/agents/{id}/config` | 更新 Agent 的 LLM 配置 |

## 改动范围

| 文件 | 改动类型 |
|------|----------|
| `agenthub/backend/services/llm_config_db.py` | 新增方法 |
| `agenthub/backend/services/bailian.py` | 修改构造函数 |
| `agenthub/backend/services/minimax.py` | 修改构造函数 |
| `agenthub/backend/services/llm_router.py` | 修改函数签名 |
| `agenthub/backend/services/session.py` | 读取并传递 model |
| `agenthub/backend/routers/agents.py` | 新增配置端点 |
| `agenthub/frontend/components/chat/MessageList.tsx` | 新增模型显示/编辑 |

## 验收标准

- [ ] Agent 可以配置任意模型名称
- [ ] 模型配置持久化，重启后保留
- [ ] 聊天页面顶部显示当前模型
- [ ] 点击模型名称可编辑并保存
- [ ] 保存成功/失败有明确反馈
