import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AgentHub",
  description: "多Agent协作聊天平台",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN">
      <body className="font-body antialiased text-ink">{children}</body>
    </html>
  );
}
