# AgentHub

IM聊天式多Agent协作平台

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 编辑并填入 ANTHROPIC_API_KEY
python main.py
```

后端运行在 http://localhost:7005

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 http://localhost:7000

## 功能

- [x] @指令触发特定Agent
- [x] 广播消息给所有Agent
- [x] SSE实时推送
- [x] Spec文档格式输出
- [x] 人类触发终止讨论

## 技术栈

- 前端: Next.js 14 + TypeScript + TailwindCSS
- 后端: FastAPI + Python
- 通信: HTTP POST + SSE