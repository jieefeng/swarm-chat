import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor, fireEvent, act } from "@testing-library/react";
import { ThreadList } from "../ThreadList";
import { useThreadStore } from "@/lib/stores/threadStore";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  api: {
    getThreads: vi.fn(),
    createThread: vi.fn(),
    deleteThread: vi.fn(),
    deleteAllThreads: vi.fn(),
    getThreadMessages: vi.fn(),
  },
}));

const mockedApi = vi.mocked(api);

const baseThread = {
  id: "thread_a",
  title: "会话 A",
  created_at: 1,
  updated_at: 1,
  is_pinned: false,
  is_archived: false,
  message_count: 0,
};

beforeEach(() => {
  vi.clearAllMocks();
  useThreadStore.setState({
    threads: [],
    currentThreadId: null,
    isLoading: false,
  });
});

describe("ThreadList 删除会话 - 删除后必须 refetch 服务端列表", () => {
  it("点击单条删除并确认后,store 必须用服务端 refetch 结果替换(而不是仅本地 filter)", async () => {
    // Arrange: 首次加载返回 [A, B]
    mockedApi.getThreads.mockResolvedValueOnce({
      threads: [baseThread, { ...baseThread, id: "thread_b", title: "会话 B" }],
    });
    mockedApi.deleteThread.mockResolvedValue({ success: true });
    // 关键: refetch 后服务端只返回 [B] (A 已被删)
    mockedApi.getThreads.mockResolvedValueOnce({
      threads: [{ ...baseThread, id: "thread_b", title: "会话 B" }],
    });

    const onThreadSelect = vi.fn();
    render(<ThreadList onThreadSelect={onThreadSelect} />);

    await waitFor(() => {
      expect(screen.getByText("会话 A")).toBeInTheDocument();
      expect(screen.getByText("会话 B")).toBeInTheDocument();
    });

    // 选 A
    fireEvent.click(screen.getByText("会话 A").closest('[role="button"]')!);

    // 触发 A 行的删除按钮
    const threadARow = screen.getByText("会话 A").closest('[role="button"]')!;
    const deleteBtn = threadARow.querySelector("button")!;
    fireEvent.click(deleteBtn);

    // 确认弹窗的"删除"按钮
    const confirmBtn = await screen.findByText("删除");
    fireEvent.click(confirmBtn);

    // 1) deleteThread 用了正确的 A.id
    await waitFor(() => {
      expect(mockedApi.deleteThread).toHaveBeenCalledWith("thread_a");
    });

    // 2) 修复: 必须在 delete 之后再调一次 getThreads (refetch)
    await waitFor(() => {
      expect(mockedApi.getThreads).toHaveBeenCalledTimes(2);
    });

    // 3) store 必须用 refetch 的结果(只剩 B),而不是仅本地 filter
    await waitFor(() => {
      const state = useThreadStore.getState();
      expect(state.threads.map((t) => t.id)).toEqual(["thread_b"]);
      expect(screen.queryByText("会话 A")).not.toBeInTheDocument();
      expect(screen.getByText("会话 B")).toBeInTheDocument();
    });
  });

  it("如果服务端 refetch 返回意外结果(比如会话被其他人删了),store 必须跟着服务端", async () => {
    // 场景: 本地有 [A, B, C], 删 B 后服务端只返回 [C] (A 也被外部删除)
    // 必须保证 store 与服务端一致,不能停留在本地 filter
    mockedApi.getThreads.mockResolvedValueOnce({
      threads: [
        baseThread,
        { ...baseThread, id: "thread_b", title: "会话 B" },
        { ...baseThread, id: "thread_c", title: "会话 C" },
      ],
    });
    mockedApi.deleteThread.mockResolvedValue({ success: true });
    // 服务端此时只剩 C (A 和 B 都已被外部清掉)
    mockedApi.getThreads.mockResolvedValueOnce({
      threads: [{ ...baseThread, id: "thread_c", title: "会话 C" }],
    });

    const onThreadSelect = vi.fn();
    render(<ThreadList onThreadSelect={onThreadSelect} />);

    await waitFor(() => {
      expect(screen.getByText("会话 B")).toBeInTheDocument();
    });

    // 触发 B 的删除
    const threadBRow = screen.getByText("会话 B").closest('[role="button"]')!;
    fireEvent.click(threadBRow.querySelector("button")!);

    const confirmBtn = await screen.findByText("删除");
    fireEvent.click(confirmBtn);

    // store 必须等于服务端 (只有 C)
    await waitFor(() => {
      const state = useThreadStore.getState();
      expect(state.threads.map((t) => t.id)).toEqual(["thread_c"]);
      expect(screen.queryByText("会话 A")).not.toBeInTheDocument();
      expect(screen.queryByText("会话 B")).not.toBeInTheDocument();
      expect(screen.getByText("会话 C")).toBeInTheDocument();
    });
  });
});

describe("ThreadList 清理其他按钮 - always-visible 两态渲染", () => {
  const threadB = { ...baseThread, id: "thread_b", title: "会话 B" };

  it("A1: 仅 1 个会话时,按钮存在但 disabled 且 tooltip 为「当前没有其他会话可清理」", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /当前没有其他会话可清理/ });
    expect(btn).toBeDisabled();
  });

  it("A2: 2+ 会话时,按钮 enabled 且带文字「清理其他」,点击打开 cleanup modal", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    expect(btn).not.toBeDisabled();
    expect(btn).toHaveTextContent("清理其他");

    fireEvent.click(btn);

    const dialog = await screen.findByRole("dialog", { name: "清理其他会话" });
    expect(dialog).toBeInTheDocument();
    expect(dialog).toHaveTextContent("1");
    expect(dialog).toHaveTextContent("会话 A");
  });
});

describe("ThreadList 清理成功 toast - 显示/消失/store 同步", () => {
  const threadB = { ...baseThread, id: "thread_b", title: "会话 B" };

  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("B1: 清理成功后,屏幕出现「已清理 1 个会话」toast", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockResolvedValue({ success: true, deleted_count: 1 });
    // refetch 后服务端只剩 A
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);

    const confirmBtn = await screen.findByRole("button", { name: "确定清理" });
    fireEvent.click(confirmBtn);

    const toast = await screen.findByRole("status");
    expect(toast).toHaveTextContent("已清理 1 个会话");
  });

  it("B2: 2 秒后 toast 从 DOM 消失", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockResolvedValue({ success: true, deleted_count: 1 });
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);
    fireEvent.click(await screen.findByRole("button", { name: "确定清理" }));

    await screen.findByRole("status");

    act(() => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  it("B3: cleanup 后 store 必须与 refetch 后的服务端列表一致(只剩 keepThread)", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockResolvedValue({ success: true, deleted_count: 1 });
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread] });

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);
    fireEvent.click(await screen.findByRole("button", { name: "确定清理" }));

    await waitFor(() => {
      const state = useThreadStore.getState();
      expect(state.threads.map((t) => t.id)).toEqual(["thread_a"]);
    });
  });
});

describe("ThreadList 清理失败 - modal 错误显示 + 不弹 toast", () => {
  const threadB = { ...baseThread, id: "thread_b", title: "会话 B" };

  it("C1: deleteAllThreads 抛错时,modal 显示错误条,且 toast 不出现", async () => {
    mockedApi.getThreads.mockResolvedValueOnce({ threads: [baseThread, threadB] });
    mockedApi.deleteAllThreads.mockRejectedValue(new Error("网络异常,请重试"));

    render(<ThreadList onThreadSelect={vi.fn()} />);

    const btn = await screen.findByRole("button", { name: /^清理其他会话$/ });
    fireEvent.click(btn);
    fireEvent.click(await screen.findByRole("button", { name: "确定清理" }));

    // 错误条出现 (ConfirmDialog 内部用 role="alert" 渲染错误)
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("网络异常,请重试");

    // toast 不应出现
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });
});
