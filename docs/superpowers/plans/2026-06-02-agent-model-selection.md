# Agent 模型选择功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 支持每个 Agent 独立配置自定义模型名称，配置持久化到数据库，在聊天页面顶部显示并可编辑。

**Architecture:** 扩展现有 `agent_llm_config` 表新增 `model` 列，修改 LLM Service 构造函数支持动态模型，前端在聊天页顶部添加模型编辑器。

**Tech Stack:** Python, FastAPI, SQLite, Next.js, TypeScript, Tailwind CSS

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `agenthub/backend/services/llm_config_db.py` | 数据库操作：新增 get_model/update_model |
| `agenthub/backend/services/bailian.py` | 百炼服务：构造函数支持 model 参数 |
| `agenthub/backend/services/minimax.py` | MiniMax 服务：构造函数支持 model 参数 |
| `agenthub/backend/services/llm_router.py` | 路由：传递 model 参数给 Service |
| `agenthub/backend/services/session.py` | 会话：读取并传递 model |
| `agenthub/backend/routers/agents.py` | API：新增配置端点 |
| `agenthub/frontend/lib/api.ts` | 前端 API：新增配置调用 |
| `agenthub/frontend/lib/types.ts` | 类型：扩展 AgentConfig |
| `agenthub/frontend/app/page.tsx` | UI：新增模型编辑器 |

---

### Task 1: 扩展数据库层

**Files:**
- Modify: `agenthub/backend/services/llm_config_db.py`

- [ ] **Step 1: 添加数据库迁移方法**

在 `LLMConfigDB` 类的 `_init_db` 方法中添加列迁移逻辑：

```python
def _init_db(self) -> None:
    """初始化数据库：创建表 + 填充默认值"""
    conn = sqlite3.connect(self.db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_llm_config (
                agent_id TEXT PRIMARY KEY,
                llm_provider TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 迁移：添加 model 列（如果不存在）
        cursor = conn.execute("PRAGMA table_info(agent_llm_config)")
        columns = [row[1] for row in cursor.fetchall()]
        if "model" not in columns:
            conn.execute("ALTER TABLE agent_llm_config ADD COLUMN model TEXT")

        # 表为空时填入默认配置
        cursor = conn.execute("SELECT COUNT(*) FROM agent_llm_config")
        if cursor.fetchone()[0] == 0:
            from .session import AGENT_CONFIGS
            for agent_id, config in AGENT_CONFIGS.items():
                provider = config.get("llm_provider", "bailian")
                conn.execute(
                    "INSERT INTO agent_llm_config (agent_id, llm_provider) VALUES (?, ?)",
                    (agent_id, provider)
                )

        conn.commit()
    finally:
        conn.close()
```

- [ ] **Step 2: 添加 get_model 方法**

```python
def get_model(self, agent_id: str) -> Optional[str]:
    """获取指定 Agent 的模型配置"""
    conn = sqlite3.connect(self.db_path)
    try:
        cursor = conn.execute(
            "SELECT model FROM agent_llm_config WHERE agent_id = ?",
            (agent_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()
```

- [ ] **Step 3: 添加 update_model 方法**

```python
def update_model(self, agent_id: str, model: str) -> bool:
    """更新指定 Agent 的模型配置"""
    conn = sqlite3.connect(self.db_path)
    try:
        cursor = conn.execute(
            "UPDATE agent_llm_config SET model = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_id = ?",
            (model, agent_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
```

- [ ] **Step 4: 扩展 get_all_config 方法**

```python
def get_all_config(self) -> Dict[str, Dict[str, str]]:
    """获取所有 Agent 的 LLM 配置"""
    conn = sqlite3.connect(self.db_path)
    try:
        cursor = conn.execute("SELECT agent_id, llm_provider, model FROM agent_llm_config")
        result = {}
        for row in cursor.fetchall():
            result[row[0]] = {"llm_provider": row[1], "model": row[2]}
        return result
    finally:
        conn.close()
```

- [ ] **Step 5: 运行测试验证**

```bash
cd agenthub/backend
python -c "
from services.llm_config_db import LLMConfigDB
db = LLMConfigDB()
print('get_model:', db.get_model('pm'))
print('get_all_config:', db.get_all_config())
"
```

- [ ] **Step 6: 提交**

```bash
git add agenthub/backend/services/llm_config_db.py
git commit -m "feat: add model column to agent_llm_config table"
```

---

### Task 2: 修改 LLM Service 支持动态模型

**Files:**
- Modify: `agenthub/backend/services/bailian.py`
- Modify: `agenthub/backend/services/minimax.py`

- [ ] **Step 1: 修改 BailianService 构造函数**

```python
class BailianService:
    """百炼 API 服务封装 - 带重试和超时"""

    DEFAULT_MODEL = "qwen3.5-plus-2026-04-20"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model or self.DEFAULT_MODEL
        self.default_timeout = 60  # 秒

    @classmethod
    def get_default_model(cls) -> str:
        return cls.DEFAULT_MODEL
```

- [ ] **Step 2: 修改 MiniMaxService 构造函数**

```python
class MiniMaxService:
    """MiniMax API 服务封装 - 带重试和超时"""

    DEFAULT_MODEL = "MiniMax-Text-01"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("MINIMAX_API_KEY", "")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.minimax.chat/v1",
        )
        self.model = model or self.DEFAULT_MODEL
        self.default_timeout = 60  # 秒

    @classmethod
    def get_default_model(cls) -> str:
        return cls.DEFAULT_MODEL
```

- [ ] **Step 3: 验证服务初始化**

```bash
cd agenthub/backend
python -c "
from services.bailian import BailianService
from services.minimax import MiniMaxService
b = BailianService(model='qwen-turbo')
m = MiniMaxService(model='custom-model')
print('Bailian model:', b.model)
print('MiniMax model:', m.model)
"
```

- [ ] **Step 4: 提交**

```bash
git add agenthub/backend/services/bailian.py agenthub/backend/services/minimax.py
git commit -m "feat: add dynamic model support to LLM services"
```

---

### Task 3: 修改 LLM Router 传递 model 参数

**Files:**
- Modify: `agenthub/backend/services/llm_router.py`

- [ ] **Step 1: 修改 get_llm_service_for_provider**

```python
def get_llm_service_for_provider(provider: str, model: Optional[str] = None) -> Union["BailianService", "MiniMaxService"]:
    """根据 provider 名称返回对应服务实例（带缓存）

    Args:
        provider: "bailian" 或 "minimax"
        model: 可选的模型名称，None 时使用默认模型

    Returns:
        对应的 LLM 服务实例
    """
    cache_key = f"{provider}:{model or 'default'}"

    if cache_key in _llm_services:
        return _llm_services[cache_key]

    if provider == "minimax":
        from .minimax import MiniMaxService
        service = MiniMaxService(model=model)
    else:
        from .bailian import BailianService
        service = BailianService(model=model)

    _llm_services[cache_key] = service
    return service
```

- [ ] **Step 2: 更新 get_llm_service 兼容函数**

```python
def get_llm_service(model: Optional[str] = None) -> Union["BailianService", "MiniMaxService"]:
    """根据 LLM_PROVIDER 环境变量返回对应服务实例（兼容旧调用）"""
    provider = os.getenv("LLM_PROVIDER", "bailian")
    return get_llm_service_for_provider(provider, model=model)
```

- [ ] **Step 3: 验证路由功能**

```bash
cd agenthub/backend
python -c "
from services.llm_router import get_llm_service_for_provider
s = get_llm_service_for_provider('bailian', model='qwen-turbo')
print('Model:', s.model)
"
```

- [ ] **Step 4: 提交**

```bash
git add agenthub/backend/services/llm_router.py
git commit -m "feat: pass model parameter through LLM router"
```

---

### Task 4: 修改 Session 读取并传递 model

**Files:**
- Modify: `agenthub/backend/services/session.py`

- [ ] **Step 1: 修改 send_to_agent 方法**

```python
def send_to_agent(self, agent_id: str, message: str) -> str:
    """发送消息到指定Agent（按 agent 配置的 llm_provider 选择 LLM）

    优先从数据库读取 provider 和 model，回退到 AGENT_CONFIGS 默认值

    Args:
        agent_id: Agent ID
        message: 消息内容

    Returns:
        LLM 响应文本
    """
    from .llm_router import get_llm_service_for_provider
    from .llm_config_db import LLMConfigDB

    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        return f"Error: Unknown agent {agent_id}"

    system_prompt = config.get("system_prompt", "")

    # 从数据库读取 provider 和 model，回退到默认值
    db = LLMConfigDB()
    provider = db.get_provider(agent_id) or config.get("llm_provider", "bailian")
    model = db.get_model(agent_id)  # None 时使用默认模型

    session_id = f"session_{agent_id}"

    try:
        llm = get_llm_service_for_provider(provider, model=model)
        response = llm.send_message(
            session_id=session_id,
            message=message,
            system_prompt=system_prompt
        )
        return response
    except Exception as e:
        return f"Error: {str(e)}"
```

- [ ] **Step 2: 修改 send_to_agent_stream 方法**

```python
def send_to_agent_stream(self, agent_id: str, message: str) -> Iterator[str]:
    """流式发送消息到指定Agent，逐个 yield 文本片段

    优先从数据库读取 provider 和 model，回退到 AGENT_CONFIGS 默认值

    Args:
        agent_id: Agent ID
        message: 消息内容

    Yields:
        LLM 响应的文本片段
    """
    from .llm_router import get_llm_service_for_provider
    from .llm_config_db import LLMConfigDB

    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        yield f"Error: Unknown agent {agent_id}"
        return

    system_prompt = config.get("system_prompt", "")

    # 从数据库读取 provider 和 model，回退到默认值
    db = LLMConfigDB()
    provider = db.get_provider(agent_id) or config.get("llm_provider", "bailian")
    model = db.get_model(agent_id)  # None 时使用默认模型

    session_id = f"session_{agent_id}"

    try:
        llm = get_llm_service_for_provider(provider, model=model)
        yield from llm.send_message_stream(
            session_id=session_id,
            message=message,
            system_prompt=system_prompt
        )
    except Exception as e:
        yield f"Error: {str(e)}"
```

- [ ] **Step 3: 提交**

```bash
git add agenthub/backend/services/session.py
git commit -m "feat: read and pass model config in session"
```

---

### Task 5: 新增后端 API 端点

**Files:**
- Modify: `agenthub/backend/routers/agents.py`

- [ ] **Step 1: 添加请求模型**

```python
class LLMConfigUpdate(BaseModel):
    """LLM 配置更新请求"""
    llm_provider: Optional[str] = None
    model: Optional[str] = None

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("bailian", "minimax"):
            raise ValueError("llm_provider must be 'bailian' or 'minimax'")
        return v
```

- [ ] **Step 2: 添加 GET 端点**

```python
@router.get("/{agent_id}/config")
async def get_agent_config(agent_id: str):
    """获取指定 Agent 的 LLM 配置"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB
    from agenthub.backend.services.session import AGENT_CONFIGS

    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    db = LLMConfigDB()
    provider = db.get_provider(agent_id)
    model = db.get_model(agent_id)

    return {
        "agent_id": agent_id,
        "llm_provider": provider,
        "model": model
    }
```

- [ ] **Step 3: 添加 PUT 端点**

```python
@router.put("/{agent_id}/config")
async def update_agent_config(agent_id: str, body: LLMConfigUpdate):
    """更新指定 Agent 的 LLM 配置"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB
    from agenthub.backend.services.session import AGENT_CONFIGS

    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    db = LLMConfigDB()

    if body.llm_provider is not None:
        db.update_provider(agent_id, body.llm_provider)

    if body.model is not None:
        db.update_model(agent_id, body.model)

    # 返回更新后的配置
    provider = db.get_provider(agent_id)
    model = db.get_model(agent_id)

    return {
        "agent_id": agent_id,
        "llm_provider": provider,
        "model": model
    }
```

- [ ] **Step 4: 测试 API**

```bash
cd agenthub/backend
# 启动服务后测试
curl http://localhost:7010/api/agents/pm/config
curl -X PUT http://localhost:7010/api/agents/pm/config \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen-turbo"}'
```

- [ ] **Step 5: 提交**

```bash
git add agenthub/backend/routers/agents.py
git commit -m "feat: add agent config API endpoints"
```

---

### Task 6: 扩展前端 API 和类型

**Files:**
- Modify: `agenthub/frontend/lib/types.ts`
- Modify: `agenthub/frontend/lib/api.ts`

- [ ] **Step 1: 添加 AgentConfig 类型**

```typescript
export interface AgentConfig {
  agent_id: string;
  llm_provider: string;
  model: string | null;
}
```

- [ ] **Step 2: 添加 API 方法**

```typescript
async getAgentConfig(agentId: string): Promise<AgentConfig> {
  const res = await fetch(`${API_BASE}/api/agents/${agentId}/config`, { headers });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
},

async updateAgentConfig(
  agentId: string,
  config: { llm_provider?: string; model?: string }
): Promise<AgentConfig> {
  const res = await fetch(`${API_BASE}/api/agents/${agentId}/config`, {
    method: "PUT",
    headers,
    body: JSON.stringify(config),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
},
```

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/types.ts agenthub/frontend/lib/api.ts
git commit -m "feat: add agent config API and types"
```

---

### Task 7: 添加前端模型编辑器组件

**Files:**
- Create: `agenthub/frontend/components/chat/ModelEditor.tsx`

- [ ] **Step 1: 创建 ModelEditor 组件**

```tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";

interface ModelEditorProps {
  agentId: string;
  agentName: string;
}

export function ModelEditor({ agentId, agentName }: ModelEditorProps) {
  const [model, setModel] = useState<string>("");
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loadConfig = async () => {
      try {
        const config = await api.getAgentConfig(agentId);
        setModel(config.model || "");
      } catch (err) {
        console.error("Failed to load agent config:", err);
      }
    };
    loadConfig();
  }, [agentId]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(false);

    try {
      await api.updateAgentConfig(agentId, { model: model || undefined });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSave();
      setIsEditing(false);
    } else if (e.key === "Escape") {
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <div className="flex items-center gap-2">
        <input
          ref={inputRef}
          type="text"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          onBlur={() => {
            handleSave();
            setIsEditing(false);
          }}
          onKeyDown={handleKeyDown}
          placeholder="输入模型名称"
          className="px-2 py-1 text-sm border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        />
        {isLoading && <span className="text-xs text-gray-500">保存中...</span>}
        {error && <span className="text-xs text-red-500">{error}</span>}
      </div>
    );
  }

  return (
    <button
      onClick={() => setIsEditing(true)}
      className="text-sm text-gray-500 hover:text-gray-700 hover:bg-gray-100 px-2 py-1 rounded transition-colors"
      title="点击编辑模型"
    >
      {model || "默认模型"}
      {success && <span className="ml-2 text-green-500">✓</span>}
    </button>
  );
}
```

- [ ] **Step 2: 提交**

```bash
git add agenthub/frontend/components/chat/ModelEditor.tsx
git commit -m "feat: add ModelEditor component"
```

---

### Task 8: 集成模型编辑器到聊天页面

**Files:**
- Modify: `agenthub/frontend/app/page.tsx`

- [ ] **Step 1: 导入 ModelEditor**

```tsx
import { ModelEditor } from "@/components/chat/ModelEditor";
```

- [ ] **Step 2: 在 Header 中添加 ModelEditor**

```tsx
{/* Header */}
<div className="flex justify-between items-center px-6 py-4 border-b border-gray-200 bg-white">
  <div className="flex items-center gap-4">
    <h1 className="text-xl font-semibold">🐉 AgentHub · 五行神兽</h1>
    {/* 当有选中 Agent 时显示模型编辑器 */}
    {agents.length > 0 && (
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-400">|</span>
        <span className="text-gray-500">当前模型:</span>
        <ModelEditor agentId={agents[0].id} agentName={agents[0].name} />
      </div>
    )}
  </div>
  <div className="text-sm text-gray-500">
    {connectionState === "connected"
      ? "🟢 已连接"
      : connectionState === "connecting"
        ? "🟡 连接中..."
        : "⚪ 空闲"}
  </div>
</div>
```

- [ ] **Step 3: 验证 UI**

```bash
cd agenthub/frontend
npm run dev
# 访问 http://localhost:3000，检查 Header 中的模型编辑器
```

- [ ] **Step 4: 提交**

```bash
git add agenthub/frontend/app/page.tsx
git commit -m "feat: integrate ModelEditor into chat page"
```

---

## 验收标准

- [ ] Agent 可以配置任意模型名称
- [ ] 模型配置持久化，重启后保留
- [ ] 聊天页面顶部显示当前模型
- [ ] 点击模型名称可编辑并保存
- [ ] 保存成功/失败有明确反馈
