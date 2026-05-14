"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Loader2,
  BookOpen,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Sparkles,
} from "lucide-react";
import { submitAnswer } from "@/lib/api";
import type { SessionState } from "@/app/page";
import type { SessionSummary, SubmitAnswerResponse } from "@/lib/api";

interface Props {
  session: SessionState;
  setSession: (s: SessionState) => void;
  onComplete: (summary: SessionSummary) => void;
}

interface ChatMessage {
  id: string;
  role: "ai" | "user";
  content: string;
  metadata?: {
    difficulty?: string;
    questionNumber?: number;
    isCorrect?: boolean;
    score?: number;
    feedback?: string;
    citation?: { source_book: string; chapter_title: string; core_concept: string };
    difficultyChange?: { from: string; to: string };
  };
}

const difficultyColors: Record<string, string> = {
  simple: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  moderate: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  complex: "text-rose-400 bg-rose-500/10 border-rose-500/20",
};

export default function InterviewChat({ session, setSession, onComplete }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "q1",
      role: "ai",
      content: session.currentQuestion,
      metadata: {
        difficulty: session.currentDifficulty,
        questionNumber: session.currentQuestionNumber,
        citation: session.sourceCitation,
      },
    },
  ]);
  const [input, setInput] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async () => {
    if (!input.trim() || submitting) return;

    const userMsg: ChatMessage = {
      id: `u${Date.now()}`,
      role: "user",
      content: input.trim(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setSubmitting(true);

    try {
      const result: SubmitAnswerResponse = await submitAnswer({
        session_id: session.sessionId,
        answer: userMsg.content,
      });

      // Add evaluation feedback
      const evalMsg: ChatMessage = {
        id: `eval${Date.now()}`,
        role: "ai",
        content: result.evaluation.feedback,
        metadata: {
          isCorrect: result.evaluation.is_correct,
          score: result.evaluation.accuracy_score,
          feedback: result.evaluation.feedback,
          citation: result.evaluation.source_citation,
          difficultyChange:
            result.difficulty_update.previous !== result.difficulty_update.current
              ? { from: result.difficulty_update.previous, to: result.difficulty_update.current }
              : undefined,
        },
      };
      setMessages((prev) => [...prev, evalMsg]);

      if (result.status === "interview_completed" && result.summary) {
        setTimeout(() => onComplete(result.summary!), 1500);
      } else if (result.next_question) {
        // Add next question after a short delay
        setTimeout(() => {
          const nextQ: ChatMessage = {
            id: `q${result.next_question!.question_number}`,
            role: "ai",
            content: result.next_question!.question,
            metadata: {
              difficulty: result.next_question!.difficulty,
              questionNumber: result.next_question!.question_number,
              citation: result.next_question!.source_citation,
            },
          };
          setMessages((prev) => [...prev, nextQ]);
          setSession({
            ...session,
            currentQuestion: result.next_question!.question,
            currentQuestionNumber: result.next_question!.question_number,
            currentDifficulty: result.next_question!.difficulty,
            sourceCitation: result.next_question!.source_citation,
          });
        }, 800);
      }
    } catch (e: unknown) {
      const errMsg: ChatMessage = {
        id: `err${Date.now()}`,
        role: "ai",
        content: e instanceof Error ? e.message : "An error occurred. Please try again.",
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const progress = (session.currentQuestionNumber / session.totalQuestions) * 100;

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-7rem)]">
      {/* Top Bar */}
      <div className="glass rounded-2xl p-4 mb-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span className="text-sm font-medium text-white/70">{session.jobRole}</span>
          </div>
          <span className={`text-xs px-2.5 py-1 rounded-full border font-medium ${difficultyColors[session.currentDifficulty] || difficultyColors.simple}`}>
            {session.currentDifficulty.toUpperCase()}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-white/30">
            Q{session.currentQuestionNumber}/{session.totalQuestions}
          </span>
          <div className="w-24 h-1.5 bg-white/5 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2 min-h-0">
        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div className={`max-w-[85%] ${msg.role === "user" ? "order-2" : ""}`}>
                {/* Question header */}
                {msg.metadata?.questionNumber && (
                  <div className="flex items-center gap-2 mb-2 text-xs text-white/30">
                    <span className="font-mono">Question {msg.metadata.questionNumber}</span>
                    <span className={`px-2 py-0.5 rounded-full border ${difficultyColors[msg.metadata.difficulty || "simple"]}`}>
                      {msg.metadata.difficulty}
                    </span>
                  </div>
                )}

                {/* Message Bubble */}
                <div
                  className={`rounded-2xl px-5 py-4 text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-gradient-to-br from-indigo-600 to-purple-600 text-white"
                      : "glass text-white/80"
                  }`}
                >
                  {/* Evaluation badge */}
                  {msg.metadata?.isCorrect !== undefined && (
                    <div className={`flex items-center gap-2 mb-3 text-xs font-medium ${msg.metadata.isCorrect ? "text-emerald-400" : "text-rose-400"}`}>
                      {msg.metadata.isCorrect ? (
                        <CheckCircle2 className="w-4 h-4" />
                      ) : (
                        <XCircle className="w-4 h-4" />
                      )}
                      {msg.metadata.isCorrect ? "Correct" : "Needs Improvement"}
                      {msg.metadata.score !== undefined && (
                        <span className="ml-auto text-white/30">
                          Score: {(msg.metadata.score * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  )}

                  <p className="whitespace-pre-wrap">{msg.content}</p>

                  {/* Difficulty change notification */}
                  {msg.metadata?.difficultyChange && (
                    <div className="mt-3 flex items-center gap-2 text-xs text-amber-400 bg-amber-500/10 rounded-lg px-3 py-2 border border-amber-500/15">
                      <TrendingUp className="w-3.5 h-3.5" />
                      Difficulty: {msg.metadata.difficultyChange.from} → {msg.metadata.difficultyChange.to}
                    </div>
                  )}
                </div>

                {/* Source citation */}
                {msg.metadata?.citation && msg.metadata.citation.source_book !== "N/A" && (
                  <div className="mt-2 flex items-center gap-1.5 text-xs text-white/20">
                    <BookOpen className="w-3 h-3" />
                    <span className="truncate">{msg.metadata.citation.source_book}</span>
                    <span>·</span>
                    <span className="truncate">{msg.metadata.citation.chapter_title}</span>
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {submitting && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="glass rounded-2xl px-5 py-4 flex items-center gap-3 text-white/40 text-sm">
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
              Evaluating your answer...
            </div>
          </motion.div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="flex-shrink-0 mt-4">
        <div className="glass rounded-2xl p-3 flex items-end gap-3">
          <textarea
            ref={inputRef}
            id="answer-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your answer..."
            rows={2}
            className="flex-1 bg-transparent text-white placeholder-white/20 resize-none focus:outline-none text-sm leading-relaxed px-3 py-2"
            disabled={submitting}
          />
          <button
            id="submit-answer"
            onClick={handleSubmit}
            disabled={!input.trim() || submitting}
            className="w-10 h-10 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 flex items-center justify-center text-white disabled:opacity-30 hover:from-indigo-500 hover:to-purple-500 transition-all flex-shrink-0"
          >
            {submitting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
        <p className="text-xs text-white/15 text-center mt-2">
          Press Enter to submit · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}
