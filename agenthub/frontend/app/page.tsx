import { BeastRoster } from "@/components/landing/BeastRoster";
import { ForumEntry } from "@/components/landing/ForumEntry";
import { HeroSection } from "@/components/landing/HeroSection";
import { WuxingFlow } from "@/components/landing/WuxingFlow";

export default function LandingPage() {
  return (
    <main className="min-h-screen bg-paper">
      <HeroSection />
      <WuxingFlow />
      <BeastRoster />
      <ForumEntry />
    </main>
  );
}
