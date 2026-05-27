---
phase: code-review
reviewed: 2026-05-25T00:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - agenthub/frontend/lib/sse.ts
  - agenthub/frontend/lib/stores/messageStore.ts
  - agenthub/frontend/lib/stores/agentStore.ts
  - agenthub/frontend/lib/stores/uiStore.ts
  - agenthub/frontend/lib/hooks/useChatStream.ts
  - agenthub/frontend/lib/schemas/message.ts
  - agenthub/frontend/lib/api.ts
  - agenthub/frontend/lib/types.ts
  - agenthub/frontend/app/page.tsx
  - agenthub/frontend/app/layout.tsx
  - agenthub/frontend/components/chat/MessageInput.tsx
  - agenthub/frontend/components/chat/MessageList.tsx
  - agenthub/frontend/components/chat/MessageBubble.tsx
  - agenthub/frontend/components/chat/MentionDropdown.tsx
  - agenthub/frontend/components/agents/AgentList.tsx
findings:
  critical: 5
  warning: 6
  info: 3
  total: 14
status: issues_found
---

# Phase: AgentHub Frontend Migration Code Review

**Reviewed:** 2026-05-25
**Depth:** standard
**Files Reviewed:** 15
**Status:** issues_found

## Summary

The AgentHub frontend migration from Pages Router to App Router has several critical security vulnerabilities and logic bugs that must be addressed before production deployment. Most critically, there are hardcoded API keys in both `lib/api.ts` and `lib/sse.ts` that will be exposed in client-side bundles. Additionally, the SSE implementation has blocking issues and the message stream hook has stale closure problems that can cause incorrect message routing.

## Critical Issues

### CR-01: Hardcoded API Key in SSE Transport

**File:** `agenthub/frontend/lib/sse.ts:30`
**Issue:** API key is hardcoded directly in source code. This secret will be exposed in any client-side bundle, allowing anyone to extract it and authenticate against the API.
```typescript
const API_KEY = "dev-secret-key";
```
**Fix:** Replace with environment variable lookup:
```typescript
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";
```
And ensure `NEXT_PUBLIC_API_KEY` is configured in deployment environment (not in `.env.local` for client-exposed keys, use `.env.production` with proper CDN secrecy controls, or better yet, move SSE authentication to server-side).

### CR-02: Hardcoded API Key in API Module

**File:** `agenthub/frontend/lib/api.ts:4`
**Issue:** Same hardcoded API key issue as CR-01. This key is used for all API requests and will be exposed in client bundles.
```typescript
const API_KEY = "dev-secret-key";
```
**Fix:** Use `process.env.NEXT_PUBLIC_API_KEY` and document that production deployment requires proper secret management.

### CR-03: SSE Connection Blocks Caller

**File:** `agenthub/frontend/lib/sse.ts:99`
**Issue:** The `connect()` function is called synchronously inside `createSSEConnection()`, which means the function does not return until the connection either establishes or fails retries completely. This blocks the caller and prevents the hook from returning a usable connection handle promptly.
```typescript
connect(); // Blocks until connection dies or retries exhausted
```
**Fix:** Return the connection handle immediately and let the caller manage connection lifecycle:
```typescript
// Don't call connect() here - let caller invoke it
return {
  connect: () => { /* ... */ },
  close: () => { aborted = true; }
};
```

### CR-04: SSE Retry Logic Continues After Abort

**File:** `agenthub/frontend/lib/sse.ts:94`
**Issue:** After `setTimeout(connect, retryDelay)` schedules a retry, the `aborted` flag is not checked before the next connection attempt begins. If `close()` is called during the retry delay, the retry will still occur.
```typescript
setTimeout(connect, retryDelay);
retryDelay = Math.min(retryDelay * 2, 16000);
// If aborted becomes true here, next connect() still runs
```
**Fix:** Add an early exit check at the start of `connect()`:
```typescript
const connect = async () => {
  if (aborted) return;
  try {
    // ...
```

### CR-05: XSS Vulnerability via ReactMarkdown

**File:** `agenthub/frontend/components/chat/MessageBubble.tsx:30`
**Issue:** User-controlled message content is rendered directly via `ReactMarkdown` without sanitization. A malicious agent could send a message containing `<script>` tags or event handlers (onclick, onerror, etc.) that execute in other users' browsers.
```typescript
<ReactMarkdown>{message.content}</ReactMarkdown>
```
**Fix:** Use a sanitizing markdown renderer or add sanitize-html:
```typescript
import remarkGfm from "remark-gfm";
import { createRoot } from "react-dom";

// Or configure rehype-sanitize
<ReactMarkdown rehypePlugins={[rehypeSanitize]}>
  {message.content}
</ReactMarkdown>
```

---

## Warnings

### WR-01: Stale Closure in SSE onMessage Callback

**File:** `agenthub/frontend/lib/hooks/useChatStream.ts:38-40,87-112`
**Issue:** The `addMessage` function is captured in the closure when `createSSEConnection` is called. Since `addMessage` comes from `useMessageStore`, it's stable by identity but the `messages` variable captured at line 92 is stale on every render. This can cause the wrong message to be replaced during streaming.
```typescript
const addMessage = useMessageStore((s) => s.addMessage);
// ...
connectionRef.current = createSSEConnection({
  baseUrl,
  onMessage: (data) => {
    // addMessage is stable but messages is STALE here
    const existingIndex = messages.findIndex(...)
  },
```
**Fix:** Access current messages via store getter inside callback:
```typescript
onMessage: (data) => {
  const currentMessages = useMessageStore.getState().messages;
  const existingIndex = currentMessages.findIndex(
    (m) => m.id.startsWith("temp-") && m.content === content,
  );
```

### WR-02: Direct Store Mutation

**File:** `agenthub/frontend/lib/hooks/useChatStream.ts:97-98`
**Issue:** The code directly mutates the store's messages array instead of using the proper `set` operation. This bypasses Zustand's reactivity system and can cause inconsistent UI state.
```typescript
useMessageStore.getState().messages[existingIndex] = data as Message;
```
**Fix:** Use a proper store action or `set` function:
```typescript
useMessageStore.setState((s) => ({
  messages: s.messages.map((m, i) =>
    i === existingIndex ? (data as Message) : m
  ),
}));
```

### WR-03: useCallback Missing Dependencies

**File:** `agenthub/frontend/lib/hooks/useChatStream.ts:119`
**Issue:** The `useCallback` dependency array includes `messages`, but `messages` is derived from `useMessageStore((s) => s.messages)`. Including it causes the callback to be recreated on every message change, which defeats the purpose of memoization and can cause subtle bugs.
```typescript
}, [agentId, baseUrl, addMessage, setStreaming, disconnect, messages]);
```
**Fix:** Remove `messages` from dependency array and access it via store getter when needed (see WR-01 fix).

### WR-04: SSE onMessage Callback Uses Stale Sender

**File:** `agenthub/frontend/lib/hooks/useChatStream.ts:91-94`
**Issue:** The logic for finding existing temp message uses `content` comparison, but `content` is captured from the outer scope at the time `sendMessage` was called. If the user sends a message while a previous stream is in progress, content matching may fail.
```typescript
const existingIndex = messages.findIndex(
  (m) => m.id.startsWith("temp-") && m.content === content,
);
```
**Fix:** Use the `tempId` that was generated and stored, or use a more stable identifier.

### WR-05: API Response Not Checked

**File:** `agenthub/frontend/lib/api.ts:22`
**Issue:** `api.sendMessage` returns `res.json()` without checking if the response was successful. If the server returns an error status (4xx/5xx), the JSON parse will likely fail or return unexpected structure.
```typescript
return res.json();
```
**Fix:** Check response status first:
```typescript
if (!res.ok) {
  const error = await res.json().catch(() => ({}));
  throw new Error(error.message || `HTTP ${res.status}`);
}
return res.json();
```

### WR-06: Missing AbortSignal for SSE Fetch

**File:** `agenthub/frontend/lib/sse.ts:34-41`
**Issue:** The fetch request does not use an AbortSignal tied to the connection's lifecycle. If `close()` is called, the in-flight fetch request continues until the server responds.
```typescript
const response = await fetch(`${options.baseUrl}/api/events`, {
  headers: { ... },
  cache: "no-store",
  credentials: "include",
});
```
**Fix:** Create an AbortController and pass its signal to fetch, calling `abortController.abort()` in the `close()` function.

---

## Info

### IN-01: 'use client' Placement in page.tsx

**File:** `agenthub/frontend/app/page.tsx:1`
**Issue:** Per project spec, `'use client'` must be the FIRST line of any client component file. The file appears to have it as the first non-comment line at line 1, which is correct. However, verify no whitespace or BOM precedes it.

### IN-02: Store Cross-Import Compliance

**File:** `agenthub/frontend/lib/stores/*.ts`
**Issue:** Verified that none of the stores import other stores. Each store is independent: `messageStore`, `agentStore`, and `uiStore` do not cross-import. This complies with the spec requirement.

### IN-03: connectionState Correctly Local

**File:** `agenthub/frontend/lib/hooks/useChatStream.ts:30-32`
**Issue:** Verified that `connectionState` is hook-local `useState`, not stored in any global store. This complies with the spec requirement that connection status is hook-local.

---

## Structural Findings (fallow)

_None provided by workflow._

## Narrative Findings (AI reviewer)

1. **Security First**: The hardcoded `API_KEY = "dev-secret-key"` appears in TWO files (`lib/sse.ts:30` and `lib/api.ts:4`). This is the most urgent issue - these secrets WILL be exposed in the client-side JavaScript bundle. Anyone can open DevTools and find them.

2. **SSE Architecture Concerns**: The SSE implementation has a fundamental issue where `connect()` is called synchronously and blocks. The retry logic is also not properly abortable. For a production chat application, connection stability is critical.

3. **React Patterns**: The stale closure issue in `useChatStream` is a classic React bug. The callback passed to `createSSEConnection` captures `messages` at the time of creation, not when messages arrive. This can cause streaming messages to be handled incorrectly.

4. **Type Safety**: The codebase uses TypeScript with `strict` mode (based on tsconfig), but there are places where `as Message` casts bypass type checking. These should be validated against the Zod schema.

5. **Missing Input Validation on API Responses**: The SSE messages and API responses are used directly without schema validation. The `sendMessageSchema` exists but isn't used to validate server responses.

---

_Reviewed: 2026-05-25_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_