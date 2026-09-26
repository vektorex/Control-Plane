import React from "react";
import { LandingNavbar } from "@/components/landing/Navbar";
import { Hero } from "@/components/landing/Hero";
import { ArchitectureSection } from "@/components/landing/ArchitectureSection";
import { CapabilitiesSection } from "@/components/landing/CapabilitiesSection";
import { LandingFooter } from "@/components/landing/Footer";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <LandingNavbar />
      <main className="flex-1">
        <Hero />
        <ArchitectureSection />
        <CapabilitiesSection />
      </main>
      <LandingFooter />
    </div>
  );
}
