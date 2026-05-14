"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import SetupPhase from "@/components/SetupPhase";
import InterviewChat from "@/components/InterviewChat";
import SummaryDashboard from "@/components/SummaryDashboard";
import type { SessionSummary, SubmitAnswerResponse } from "@/lib/api";

export type AppPhase = "setup" | "interview" | "summary";

export interface SessionState {
  sessionId: string;
  candidateName: string;
  jobRole: string;
  skills: string[];
  totalQuestions: number;
  currentQuestion: string;
  currentQuestionNumber: number;
  currentDifficulty: string;
  sourceCitation: { source_book: string; chapter_title: string; core_concept: string };
}

export default function Home() {
  const [phase, setPhase] = useState<AppPhase>("setup");
  const [session, setSession] = useState<SessionState | null>(null);
  const [summary, setSummary] = useState<SessionSummary | null>(null);

  const handleInterviewStarted = (s: SessionState) => {
    setSession(s);
    setPhase("interview");
  };

  const handleInterviewComplete = (sum: SessionSummary) => {
    setSummary(sum);
    setPhase("summary");
  };

  const handleRestart = () => {
    setPhase("setup");
    setSession(null);
    setSummary(null);
  };

  return (
    <div className="relative z-10 min-h-screen">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass-strong border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm">
              P
            </div>
            <span className="text-lg font-semibold tracking-tight text-white/90">
              PG-AGI
            </span>
            <span className="hidden sm:inline text-xs text-white/30 ml-2 px-2 py-0.5 rounded-full border border-white/10">
              Technical Screening
            </span>
          </div>
          {session && phase === "interview" && (
            <div className="flex items-center gap-4 text-sm">
              <span className="text-white/40">Session</span>
              <span className="font-mono text-indigo-400 text-xs">
                {session.sessionId.slice(0, 8)}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-20 pb-8 px-4 sm:px-6">
        <AnimatePresence mode="wait">
          {phase === "setup" && (
            <motion.div
              key="setup"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              <SetupPhase onStart={handleInterviewStarted} />
            </motion.div>
          )}
          {phase === "interview" && session && (
            <motion.div
              key="interview"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              <InterviewChat
                session={session}
                setSession={setSession}
                onComplete={handleInterviewComplete}
              />
            </motion.div>
          )}
          {phase === "summary" && summary && (
            <motion.div
              key="summary"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.4, ease: "easeOut" }}
            >
              <SummaryDashboard summary={summary} onRestart={handleRestart} />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
