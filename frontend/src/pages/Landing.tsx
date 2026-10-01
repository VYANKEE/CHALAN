import { useLenis } from "../lib/useLenis";
import { Nav } from "../components/landing/Nav";
import { Hero } from "../components/landing/Hero";
import { ProblemSection } from "../components/landing/ProblemSection";
import { PipelineSection } from "../components/landing/PipelineSection";
import { ResultsSection } from "../components/landing/ResultsSection";
import { ConfidenceSection } from "../components/landing/ConfidenceSection";
import { ReviewSection } from "../components/landing/ReviewSection";
import { UseCasesSection } from "../components/landing/UseCasesSection";
import { CTASection } from "../components/landing/CTASection";
import { Footer } from "../components/landing/Footer";

export function Landing() {
  useLenis();

  return (
    <div className="bg-[var(--color-ink-950)]">
      <Nav />
      <Hero />
      <ProblemSection />
      <PipelineSection />
      <ResultsSection />
      <ConfidenceSection />
      <ReviewSection />
      <UseCasesSection />
      <CTASection />
      <Footer />
    </div>
  );
}
