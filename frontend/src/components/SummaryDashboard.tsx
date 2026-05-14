"use client";

import { motion } from "framer-motion";
import {
  Award,
  BarChart3,
  BookOpen,
  CheckCircle2,
  XCircle,
  TrendingUp,
  ArrowRight,
  RotateCcw,
  Shield,
  Eye,
  Target,
  Sparkles,
} from "lucide-react";
import type { SessionSummary } from "@/lib/api";

interface Props {
  summary: SessionSummary;
  onRestart: () => void;
}

export default function SummaryDashboard({ summary, onRestart }: Props) {
  const scoreColor =
    summary.score_percentage >= 80
      ? "text-emerald-400"
      : summary.score_percentage >= 60
      ? "text-amber-400"
      : "text-rose-400";

  const scoreGlow =
    summary.score_percentage >= 80
      ? "from-emerald-500/20 to-emerald-500/5"
      : summary.score_percentage >= 60
      ? "from-amber-500/20 to-amber-500/5"
      : "from-rose-500/20 to-rose-500/5";

  const recColor = summary.recommendation.includes("STRONG HIRE")
    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
    : summary.recommendation.includes("HIRE")
    ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
    : summary.recommendation.includes("MAYBE")
    ? "border-amber-500/20 bg-amber-500/5 text-amber-400"
    : "border-rose-500/20 bg-rose-500/5 text-rose-400";

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ type: "spring", stiffness: 200, delay: 0.1 }}
          className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-4 glow"
        >
          <Award className="w-8 h-8 text-white" />
        </motion.div>
        <h1 className="text-3xl font-bold text-white/90 mb-1">
          Interview Complete
        </h1>
        <p className="text-white/40">
          {summary.candidate_name} · {summary.job_role}
        </p>
      </div>

      {/* Score Card */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass rounded-2xl p-8 text-center"
      >
        <div className={`text-6xl font-bold ${scoreColor} mb-2`}>
          {summary.score_percentage}%
        </div>
        <p className="text-sm text-white/40 mb-4">
          {summary.correct_answers} of {summary.total_questions} correct
        </p>
        <div className={`inline-block px-5 py-2.5 rounded-xl border text-sm font-medium ${recColor}`}>
          {summary.recommendation}
        </div>
      </motion.div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        {[
          { label: "Avg Accuracy", value: `${(summary.average_accuracy * 100).toFixed(0)}%`, icon: Target },
          { label: "Final Level", value: summary.final_difficulty.charAt(0).toUpperCase() + summary.final_difficulty.slice(1), icon: TrendingUp },
          { label: "Correct", value: `${summary.correct_answers}/${summary.total_questions}`, icon: CheckCircle2 },
          { label: "RAG Score", value: `${((summary.rag_triad_averages.context_relevance + summary.rag_triad_averages.answer_faithfulness + summary.rag_triad_averages.answer_relevance) / 3 * 100).toFixed(0)}%`, icon: Sparkles },
        ].map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + i * 0.08 }}
            className="glass rounded-xl p-4 text-center"
          >
            <m.icon className="w-5 h-5 text-indigo-400 mx-auto mb-2" />
            <div className="text-lg font-semibold text-white/90">{m.value}</div>
            <div className="text-xs text-white/30 mt-1">{m.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Difficulty Distribution & RAG Triad */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Difficulty Distribution */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-sm font-medium text-white/60 mb-4 flex items-center gap-2">
            <BarChart3 className="w-4 h-4" /> Difficulty Distribution
          </h3>
          <div className="space-y-3">
            {(["simple", "moderate", "complex"] as const).map((level) => {
              const count = summary.difficulty_distribution[level] || 0;
              const pct = summary.total_questions > 0 ? (count / summary.total_questions) * 100 : 0;
              const colors: Record<string, string> = {
                simple: "bg-emerald-500",
                moderate: "bg-amber-500",
                complex: "bg-rose-500",
              };
              return (
                <div key={level}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-white/50 capitalize">{level}</span>
                    <span className="text-white/30">{count} questions</span>
                  </div>
                  <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                    <motion.div
                      className={`h-full ${colors[level]} rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ delay: 0.7, duration: 0.6 }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        {/* RAG Triad */}
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.55 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-sm font-medium text-white/60 mb-4 flex items-center gap-2">
            <Eye className="w-4 h-4" /> RAG Triad Observability
          </h3>
          <div className="space-y-3">
            {[
              { label: "Context Relevance", value: summary.rag_triad_averages.context_relevance, color: "bg-sky-500" },
              { label: "Answer Faithfulness", value: summary.rag_triad_averages.answer_faithfulness, color: "bg-violet-500" },
              { label: "Answer Relevance", value: summary.rag_triad_averages.answer_relevance, color: "bg-teal-500" },
            ].map((m) => (
              <div key={m.label}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-white/50">{m.label}</span>
                  <span className="text-white/30">{(m.value * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-2 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full ${m.color} rounded-full`}
                    initial={{ width: 0 }}
                    animate={{ width: `${m.value * 100}%` }}
                    transition={{ delay: 0.8, duration: 0.6 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Q&A Review */}
      {summary.interactions && summary.interactions.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="glass rounded-2xl p-6"
        >
          <h3 className="text-sm font-medium text-white/60 mb-4 flex items-center gap-2">
            <BookOpen className="w-4 h-4" /> Question Review
          </h3>
          <div className="space-y-4">
            {summary.interactions.map((qa, i) => (
              <div key={i} className="border border-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-mono text-white/30">Q{qa.question_number}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full border ${
                    qa.difficulty === "simple"
                      ? "text-emerald-400 border-emerald-500/20"
                      : qa.difficulty === "moderate"
                      ? "text-amber-400 border-amber-500/20"
                      : "text-rose-400 border-rose-500/20"
                  }`}>
                    {qa.difficulty}
                  </span>
                  {qa.is_correct ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 ml-auto" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 ml-auto" />
                  )}
                  <span className="text-xs text-white/20">
                    {qa.accuracy_score !== null ? `${(qa.accuracy_score * 100).toFixed(0)}%` : "N/A"}
                  </span>
                </div>
                <p className="text-sm text-white/70 mb-2">{qa.question}</p>
                {qa.answer && (
                  <p className="text-sm text-white/40 pl-3 border-l-2 border-indigo-500/30 mb-2">
                    {qa.answer}
                  </p>
                )}
                {qa.feedback && (
                  <p className="text-xs text-white/25 italic">{qa.feedback}</p>
                )}
                {qa.source_citation && qa.source_citation.source_book !== "N/A" && (
                  <div className="mt-2 text-xs text-white/15 flex items-center gap-1">
                    <BookOpen className="w-3 h-3" />
                    {qa.source_citation.source_book} · {qa.source_citation.chapter_title}
                  </div>
                )}
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Restart Button */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="text-center pb-8"
      >
        <button
          id="restart-interview"
          onClick={onRestart}
          className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium inline-flex items-center gap-2 hover:from-indigo-500 hover:to-purple-500 transition-all glow"
        >
          <RotateCcw className="w-4 h-4" /> Start New Interview
        </button>
      </motion.div>
    </div>
  );
}
