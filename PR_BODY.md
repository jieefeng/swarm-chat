## Summary
- 实现 SQLite 持久化存储，聊天记录重启后不丢失
- 添加历史会话列表 UI，支持多会话切换
- 实现会话管理 API（创建、查询、删除、更新）

## Changes

### 后端
- 新增 `sqlite_manager.py` - SQLite 存储管理器
- 新增 `threads.py` - 会话 API 端点
- 修改 `memory_manager.py` - 集成 SQLite 支持
- 修改 `messages.py` - 消息持久化到 SQLite

### 前端
- 新增 `threadStore.ts` - 会话状态管理
- 新增 `ThreadList.tsx`, `ThreadItem.tsx`, `NewThreadButton.tsx` - 会话列表组件
- 修改 `page.tsx` - 集成会话列表侧边栏
- 修改 `api.ts` - 添加会话 API 调用

### 测试
- 新增 `test_sqlite_manager.py` - 16 个测试
- 新增 `test_threads_api.py` - 12 个测试

## Test Plan
- [x] SQLite 管理器单元测试通过
- [x] 会话 API 集成测试通过
- [x] TypeScript 类型检查通过
- [ ] 手动测试会话创建、切换、删除功能
- [ ] 手动测试消息持久化功能