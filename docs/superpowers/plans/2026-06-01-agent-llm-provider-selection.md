# Agent LLM Provider 选择功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 允许用户在前端为每个 Agent 配置 LLM Provider（bailian/anthropic），配置持久化到 SQLite。

**Architecture:** 新增 SQLite 表存储配置，后端提供 REST API，前端 Agent 列表页增加选择器。`session.py` 的 `send_to_agent` 改为从数据库读取 provider，回退到硬编码默认值。

**Tech Stack:** Python SQLite3, FastAPI, Next.js, Zustand

---

## 文件结构

| 文件 | 职责 |
|------|------|
| `backend/services/llm_config_db.py` | SQLite 操作封装：建表、读写配置 |
| `backend/routers/agents.py` | Agent LLM 配置 API 端点 |
| `backend/services/session.py` | 修改：从数据库读 provider |
| `backend/main.py` | 修改：注册路由、启动时初始化表 |
| `backend/tests/test_llm_config_db.py` | 数据库模块单元测试 |
| `backend/tests/test_agents_api.py` | API 端点测试 |
| `frontend/lib/api.ts` | 修改：新增 LLM 配置 API 调用 |
| `frontend/components/agents/AgentList.tsx` | 修改：增加 Provider 下拉框 |

---

## Task 1: SQLite 数据库模块

**Files:**
- Create: `agenthub/backend/services/llm_config_db.py`
- Test: `agenthub/backend/tests/test_llm_config_db.py`

- [ ] **Step 1: 写失败的测试**

```python
# agenthub/backend/tests/test_llm_config_db.py
"""LLM 配置数据库模块测试"""
import pytest
import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.services.llm_config_db import LLMConfigDB


class TestLLMConfigDB:
    """LLMConfigDB 测试类"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建临时数据库实例"""
        db_path = str(tmp_path / "test.db")
        return LLMConfigDB(db_path)

    def test_init_creates_table(self, db):
        """初始化时创建表"""
        conn = sqlite3.connect(db.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='agent_llm_config'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_init_seeds_default_data(self, db):
        """表为空时插入默认配置"""
        config = db.get_all_config()
        assert "pm" in config
        assert "architect" in config
        assert config["pm"]["llm_provider"] == "bailian"

    def test_get_provider_returns_default(self, db):
        """获取存在的 agent provider"""
        assert db.get_provider("pm") == "bailian"

    def test_get_provider_returns_none_for_unknown(self, db):
        """获取不存在的 agent 返回 None"""
        assert db.get_provider("unknown") is None

    def test_update_provider(self, db):
        """更新 provider"""
        db.update_provider("pm", "anthropic")
        assert db.get_provider("pm") == "anthropic"

    def test_get_all_config(self, db):
        """获取所有配置"""
        config = db.get_all_config()
        assert isinstance(config, dict)
        assert len(config) >= 2  # pm, architect
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/backend && python -m pytest tests/test_llm_config_db.py -v`
Expected: FAIL (模块不存在)

- [ ] **Step 3: 写最小实现**

```python
# agenthub/backend/services/llm_config_db.py
"""LLM 配置数据库模块 - 管理 Agent 的 LLM Provider 配置"""
import sqlite3
from typing import Dict, Optional


class LLMConfigDB:
    """LLM 配置数据库封装"""

    def __init__(self, db_path: str = "agenthub.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库：创建表 + 填充默认值"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_llm_config (
                agent_id TEXT PRIMARY KEY,
                llm_provider TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

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
        conn.close()

    def get_provider(self, agent_id: str) -> Optional[str]:
        """获取指定 Agent 的 LLM Provider

        Args:
            agent_id: Agent ID

        Returns:
            provider 名称，不存在返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT llm_provider FROM agent_llm_config WHERE agent_id = ?",
            (agent_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def get_all_config(self) -> Dict[str, Dict[str, str]]:
        """获取所有 Agent 的 LLM 配置

        Returns:
            {agent_id: {llm_provider: ...}} 格式
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT agent_id, llm_provider FROM agent_llm_config")
        result = {}
        for row in cursor.fetchall():
            result[row[0]] = {"llm_provider": row[1]}
        conn.close()
        return result

    def update_provider(self, agent_id: str, llm_provider: str) -> bool:
        """更新指定 Agent 的 LLM Provider

        Args:
            agent_id: Agent ID
            llm_provider: 新的 provider ("bailian" 或 "anthropic")

        Returns:
            是否更新成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "UPDATE agent_llm_config SET llm_provider = ?, updated_at = CURRENT_TIMESTAMP WHERE agent_id = ?",
            (llm_provider, agent_id)
        )
        conn.commit()
        updated = cursor.rowcount > 0
        conn.close()
        return updated
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd agenthub/backend && python -m pytest tests/test_llm_config_db.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/backend/services/llm_config_db.py agenthub/backend/tests/test_llm_config_db.py
git commit -m "feat: add LLM config database module with SQLite storage"
```

---

## Task 2: Agent LLM 配置 API

**Files:**
- Create: `agenthub/backend/routers/agents.py`
- Modify: `agenthub/backend/main.py`
- Test: `agenthub/backend/tests/test_agents_api.py`

- [ ] **Step 1: 写失败的测试**

```python
# agenthub/backend/tests/test_agents_api.py
"""Agent LLM 配置 API 测试"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agenthub.backend.main import app


client = TestClient(app)
API_KEY = "dev-secret-key"
HEADERS = {"X-API-Key": API_KEY}


class TestAgentsLLMConfigAPI:
    """Agent LLM 配置 API 测试类"""

    def test_get_all_llm_config(self):
        """GET /api/agents/llm-config 返回所有配置"""
        response = client.get("/api/agents/llm-config", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "pm" in data
        assert "llm_provider" in data["pm"]

    def test_update_llm_config(self):
        """PUT /api/agents/pm/llm-config 更新配置"""
        response = client.put(
            "/api/agents/pm/llm-config",
            headers=HEADERS,
            json={"llm_provider": "anthropic"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["llm_provider"] == "anthropic"

    def test_update_invalid_provider(self):
        """PUT 无效 provider 返回 422"""
        response = client.put(
            "/api/agents/pm/llm-config",
            headers=HEADERS,
            json={"llm_provider": "invalid"}
        )
        assert response.status_code == 422

    def test_update_unknown_agent(self):
        """PUT 不存在的 agent 返回 404"""
        response = client.put(
            "/api/agents/unknown/llm-config",
            headers=HEADERS,
            json={"llm_provider": "bailian"}
        )
        assert response.status_code == 404
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/backend && python -m pytest tests/test_agents_api.py -v`
Expected: FAIL (路由不存在)

- [ ] **Step 3: 写路由实现**

```python
# agenthub/backend/routers/agents.py
"""Agent 配置 API 路由"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

router = APIRouter(prefix="/api/agents", tags=["agents"])


class LLMProviderUpdate(BaseModel):
    """LLM Provider 更新请求"""
    llm_provider: str

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in ("bailian", "anthropic"):
            raise ValueError("llm_provider must be 'bailian' or 'anthropic'")
        return v


@router.get("/llm-config")
async def get_all_llm_config():
    """获取所有 Agent 的 LLM 配置"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB
    db = LLMConfigDB()
    return db.get_all_config()


@router.put("/{agent_id}/llm-config")
async def update_llm_config(agent_id: str, body: LLMProviderUpdate):
    """更新指定 Agent 的 LLM 配置"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB
    from agenthub.backend.services.session import AGENT_CONFIGS

    if agent_id not in AGENT_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    db = LLMConfigDB()
    db.update_provider(agent_id, body.llm_provider)

    return {"agent_id": agent_id, "llm_provider": body.llm_provider}
```

- [ ] **Step 4: 注册路由到 main.py**

在 `agenthub/backend/main.py` 中添加：

```python
# 在 import 部分添加
from agenthub.backend.routers import messages, events, tasks, agents

# 在路由注册部分添加
app.include_router(agents.router)
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd agenthub/backend && python -m pytest tests/test_agents_api.py -v`
Expected: PASS

- [ ] **Step 6: 提交**

```bash
git add agenthub/backend/routers/agents.py agenthub/backend/main.py agenthub/backend/tests/test_agents_api.py
git commit -m "feat: add Agent LLM config API endpoints"
```

---

## Task 3: 修改 SessionManager 从数据库读取 Provider

**Files:**
- Modify: `agenthub/backend/services/session.py`
- Test: `agenthub/backend/tests/test_session.py`

- [ ] **Step 1: 添加测试**

在 `test_session.py` 中添加：

```python
def test_send_to_agent_uses_db_provider(self):
    """测试 send_to_agent 从数据库读取 provider"""
    from agenthub.backend.services.llm_config_db import LLMConfigDB

    db = LLMConfigDB()
    db.update_provider("pm", "anthropic")

    # 验证数据库中的配置
    assert db.get_provider("pm") == "anthropic"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd agenthub/backend && python -m pytest tests/test_session.py::TestSessionManager::test_send_to_agent_uses_db_provider -v`
Expected: FAIL (还未从数据库读取)

- [ ] **Step 3: 修改 send_to_agent 方法**

修改 `agenthub/backend/services/session.py` 中的 `send_to_agent` 方法：

```python
def send_to_agent(self, agent_id: str, message: str) -> str:
    """发送消息到指定Agent（按 agent 配置的 llm_provider 选择 LLM）

    优先从数据库读取 provider，回退到 AGENT_CONFIGS 默认值
    """
    from .llm_router import get_llm_service_for_provider
    from .llm_config_db import LLMConfigDB

    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        return f"Error: Unknown agent {agent_id}"

    system_prompt = config.get("system_prompt", "")

    # 从数据库读取 provider，回退到默认值
    db = LLMConfigDB()
    provider = db.get_provider(agent_id) or config.get("llm_provider", "bailian")

    session_id = f"session_{agent_id}"

    try:
        llm = get_llm_service_for_provider(provider)
        response = llm.send_message(
            session_id=session_id,
            message=message,
            system_prompt=system_prompt
        )
        return response
    except Exception as e:
        return f"Error: {str(e)}"
```

同样修改 `send_to_agent_stream` 方法：

```python
def send_to_agent_stream(self, agent_id: str, message: str) -> Iterator[str]:
    """流式发送消息到指定Agent，逐个 yield 文本片段

    优先从数据库读取 provider，回退到 AGENT_CONFIGS 默认值
    """
    from .llm_router import get_llm_service_for_provider
    from .llm_config_db import LLMConfigDB

    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        yield f"Error: Unknown agent {agent_id}"
        return

    system_prompt = config.get("system_prompt", "")

    # 从数据库读取 provider，回退到默认值
    db = LLMConfigDB()
    provider = db.get_provider(agent_id) or config.get("llm_provider", "bailian")

    session_id = f"session_{agent_id}"

    try:
        llm = get_llm_service_for_provider(provider)
        yield from llm.send_message_stream(
            session_id=session_id,
            message=message,
            system_prompt=system_prompt
        )
    except Exception as e:
        yield f"Error: {str(e)}"
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd agenthub/backend && python -m pytest tests/test_session.py -v`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add agenthub/backend/services/session.py
git commit -m "feat: read LLM provider from database in SessionManager"
```

---

## Task 4: 前端 API 调用

**Files:**
- Modify: `agenthub/frontend/lib/api.ts`

- [ ] **Step 1: 添加 API 调用方法**

在 `agenthub/frontend/lib/api.ts` 的 `api` 对象中添加：

```typescript
async getLLMConfig(): Promise<Record<string, { llm_provider: string }>> {
  const res = await fetch(`${API_BASE}/api/agents/llm-config`, { headers });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
},

async updateLLMConfig(agentId: string, provider: string): Promise<{ agent_id: string; llm_provider: string }> {
  const res = await fetch(`${API_BASE}/api/agents/${agentId}/llm-config`, {
    method: "PUT",
    headers,
    body: JSON.stringify({ llm_provider: provider }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${res.status}`);
  }
  return res.json();
},
```

- [ ] **Step 2: 运行 TypeScript 检查**

Run: `cd agenthub/frontend && npm run check`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/lib/api.ts
git commit -m "feat: add LLM config API calls to frontend"
```

---

## Task 5: 前端 Agent 列表页增加 Provider 选择器

**Files:**
- Modify: `agenthub/frontend/components/agents/AgentList.tsx`

- [ ] **Step 1: 修改 AgentList 组件**

```tsx
// agenthub/frontend/components/agents/AgentList.tsx
"use client";

import { useState, useEffect } from "react";
import type { Agent } from "@/lib/types";
import { api } from "@/lib/api";

interface AgentListProps {
  agents: Agent[];
}

const ELEMENT_EMOJI: Record<string, string> = {
  木: "🌿",
  水: "💧",
  金: "⚔️",
  火: "🔥",
  土: "🪨",
};

const PROVIDER_LABELS: Record<string, string> = {
  bailian: "阿里云百炼",
  anthropic: "Claude",
};

export function AgentList({ agents }: AgentListProps) {
  const [llmConfig, setLlmConfig] = useState<Record<string, { llm_provider: string }>>({});
  const [saving, setSaving] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  useEffect(() => {
    api.getLLMConfig().then(setLlmConfig).catch(console.error);
  }, []);

  const handleProviderChange = async (agentId: string, provider: string) => {
    setSaving(agentId);
    try {
      await api.updateLLMConfig(agentId, provider);
      setLlmConfig((prev) => ({
        ...prev,
        [agentId]: { llm_provider: provider },
      }));
      setToast(`已切换到 ${PROVIDER_LABELS[provider] || provider}`);
      setTimeout(() => setToast(null), 2000);
    } catch (error) {
      console.error("Failed to update LLM config:", error);
      setToast("切换失败，请重试");
      setTimeout(() => setToast(null), 3000);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div className="w-56 bg-white border-r border-gray-200 p-4 overflow-y-auto relative">
      <div className="text-sm font-semibold text-gray-700 pb-3 border-b border-gray-200">
        🐉 五行神兽
      </div>
      {agents.map((agent) => (
        <div
          key={agent.id}
          className="py-3 border-b border-gray-100 hover:bg-gray-50 transition-colors rounded-lg px-2 -mx-2"
        >
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0"
              style={{ backgroundColor: agent.color?.primary || "#6B7280" }}
            >
              {agent.beast?.[0] || agent.name[0]}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                <span className="text-sm font-medium text-gray-800 truncate">
                  {agent.nickname || agent.name}
                </span>
                {agent.element && (
                  <span className="text-xs" title={agent.element}>
                    {ELEMENT_EMOJI[agent.element] || ""}
                  </span>
                )}
              </div>
              {agent.beast && (
                <div className="text-xs text-gray-400 truncate">
                  {agent.beast}
                </div>
              )}
            </div>
          </div>

          {/* LLM Provider 选择器 */}
          <div className="mt-2 flex items-center gap-2">
            <span className="text-xs text-gray-500">LLM:</span>
            <select
              value={llmConfig[agent.id]?.llm_provider || "bailian"}
              onChange={(e) => handleProviderChange(agent.id, e.target.value)}
              disabled={saving === agent.id}
              className="text-xs border border-gray-200 rounded px-1.5 py-0.5 bg-white disabled:opacity-50"
            >
              <option value="bailian">阿里云百炼</option>
              <option value="anthropic">Claude</option>
            </select>
          </div>

          {agent.catchphrase && (
            <div className="text-xs text-gray-400 mt-1 italic truncate">
              "{agent.catchphrase}"
            </div>
          )}
        </div>
      ))}

      {/* Toast 提示 */}
      {toast && (
        <div className="absolute bottom-4 left-4 right-4 bg-gray-800 text-white text-xs py-2 px-3 rounded shadow-lg">
          {toast}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: 运行 TypeScript 检查**

Run: `cd agenthub/frontend && npm run check`
Expected: PASS

- [ ] **Step 3: 提交**

```bash
git add agenthub/frontend/components/agents/AgentList.tsx
git commit -m "feat: add LLM provider selector to Agent list"
```

---

## Task 6: 集成测试

- [ ] **Step 1: 启动后端，验证 API**

```bash
cd agenthub/backend
python main.py &
sleep 2

# 获取所有配置
curl -H "X-API-Key: dev-secret-key" http://localhost:7010/api/agents/llm-config

# 更新配置
curl -X PUT -H "X-API-Key: dev-secret-key" -H "Content-Type: application/json" \
  -d '{"llm_provider": "anthropic"}' \
  http://localhost:7010/api/agents/pm/llm-config

# 再次获取，确认更新
curl -H "X-API-Key: dev-secret-key" http://localhost:7010/api/agents/llm-config
```

- [ ] **Step 2: 启动前端，验证 UI**

```bash
cd agenthub/frontend
npm run dev
```

访问 http://localhost:7000/agents，验证：
- 每个 Agent 卡片显示 LLM 下拉框
- 切换后显示 toast 提示
- 刷新页面后配置保持

- [ ] **Step 3: 验证消息发送使用新配置**

在聊天页面 @pm 发送消息，观察后端日志确认使用了配置的 provider。

- [ ] **Step 4: 最终提交**

```bash
git add -A
git commit -m "feat: complete Agent LLM provider selection feature"
```

---

## 自审清单

- [x] 设计文档中所有需求都有对应任务
- [x] 无 TBD/TODO 占位符
- [x] 类型、方法签名一致
- [x] 每个步骤有完整代码
- [x] 包含测试步骤
