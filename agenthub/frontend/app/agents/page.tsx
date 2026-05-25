import { AgentList } from "@/components/agents/AgentList";

export default async function AgentsPage() {
  // Server Component - 数据获取在 client hydrate 后通过 store 同步
  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Agent 列表</h1>
      <AgentList agents={[]} />
    </div>
  );
}
