# AgentHub — 五行神兽议事堂

> 一行 code 写不出来，五个神兽围炉议事。

## 五行流转

```
苍龙(谋·定策) → 炎翎(严·试火) → 瑞麟(调·调度) → 啸风(快·锻冶) → 玄冥(稳·筑基) → 苍龙
```

每一步是上一段的果，是下一段的因。

**真实示例：**

```
@瑞麟 加个深色模式
  → 瑞麟拆解任务
  → @苍龙 厘清需求
  → @啸风 实现
  → @炎翎 试火
  → @玄冥 复查架构
  → 完事
```

## 5 神兽

| 兽 | 昵称 | 五行 | 方位 | 季节 | 性格动词 | 职能 | 口头禅 |
|----|------|------|------|------|----------|------|--------|
| 青龙 | 苍龙 | 木 | 东 | 春 | **谋** | 定策 | 且慢，先理清需求再动手 |
| 玄武 | 玄冥 | 水 | 北 | 冬 | **稳** | 筑基 | 根基不稳，地动山摇 |
| 白虎 | 啸风 | 金 | 西 | 秋 | **快** | 锻冶 | 说干就干，废话少说 |
| 朱雀 | 炎翎 | 火 | 南 | 夏 | **严** | 试火 | 这点小把戏，还想瞒过我？ |
| 麒麟 | 瑞麟 | 土 | 中 | 季 | **调** | 调律 | 诸位稍安，容我梳理一番 |

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入 ANTHROPIC_API_KEY 或 DASHSCOPE_API_KEY
python main.py
```

后端运行在 http://localhost:7010

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:7000，从 Landing 进 /forum，挑一只神兽开聊。

## 怎么调度

- `@苍龙 <需求>` — 让 PM 分析需求
- `@啸风 <任务>` — 让开发者实现
- `@炎翎 <代码>` — 让 QA 审查
- `@瑞麟 <目标>` — 让协调器按五行流转拆解 + 调度
- `@玄冥 <方案>` — 让架构师评审架构

无 @ 指令的消息会发给当前会话的默认 Agent（首次进入会话会引导选择）。

## 怎么加你的神兽

扩 3 个文件即可，5 分钟内完成：

1. `backend/services/agent_identity.py` 的 `AGENT_IDENTITIES` 加一项（含 beast/nickname/element/personality/catchphrase/strengths/caution/system_prompt_suffix）
2. `backend/services/session.py` 的 `AGENT_CONFIGS` 加一项（含 name/role/llm_provider/system_prompt）
3. `frontend/lib/wuxing.ts` 的 `WUXING_BEASTS` 加一项（含 beast/nickname/element/direction/season/verb/role/color/svgPath/personality/catchphrase/strengths/caution）

如需新羁绊，再扩 `BOND_MAP`（同文件）。

## 路线图

- **阶段 1（现在）**: 五行神兽立庙 — 真头像 + Landing + README
- **阶段 2**: 声与形 — 神兽声线 + 水墨主题精调
- **阶段 3**: 飞升 — 飞书/钉钉跨平台
- **阶段 4**: 副业 — 神兽策略卡 / 共创世界

## 不做的清单

- 不做 AI 陪伴和虚拟人格
- 不做演示视频
- 不立 CVO 之类的神秘化角色
- 不模仿其他项目的章节骨架
- 不堆砌东方装饰（印章/卷轴/砚台图标等）

## License

MIT
