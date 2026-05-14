"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  User,
  Briefcase,
  Zap,
  ChevronRight,
  FileText,
  CheckCircle2,
  Loader2,
  BookOpen,
  Brain,
  Target,
} from "lucide-react";
import { uploadResume, startInterview } from "@/lib/api";
import type { SessionState } from "@/app/page";

interface Props {
  onStart: (session: SessionState) => void;
}

const JOB_ROLES = [
  "Machine Learning Engineer",
  "Data Scientist",
  "AI Research Scientist",
  "NLP Engineer",
  "Computer Vision Engineer",
  "MLOps Engineer",
  "Deep Learning Engineer",
];

export default function SetupPhase({ onStart }: Props) {
  const [step, setStep] = useState<"info" | "upload" | "review">("info");
  const [candidateName, setCandidateName] = useState("");
  const [jobRole, setJobRole] = useState(JOB_ROLES[0]);
  const [totalQuestions, setTotalQuestions] = useState(5);
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [skills, setSkills] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState("");

  const handleFileUpload = useCallback(async (file: File) => {
    setResumeFile(file);
    setUploading(true);
    setError("");
    try {
      const result = await uploadResume(file);
      setResumeText(result.resume_text);
      setSkills(result.extracted.skills || []);
      if (result.extracted.candidate_name && result.extracted.candidate_name !== "Unknown Candidate") {
        setCandidateName(result.extracted.candidate_name);
      }
      setStep("review");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }, []);

  const handleStartInterview = async () => {
    if (!candidateName.trim()) {
      setError("Please enter your name");
      return;
    }
    setStarting(true);
    setError("");
    try {
      const result = await startInterview({
        candidate_name: candidateName,
        job_role: jobRole,
        resume_text: resumeText || undefined,
        skills: skills.length > 0 ? skills : undefined,
        total_questions: totalQuestions,
      });
      onStart({
        sessionId: result.session_id,
        candidateName,
        jobRole,
        skills,
        totalQuestions,
        currentQuestion: result.question,
        currentQuestionNumber: result.question_number,
        currentDifficulty: result.difficulty,
        sourceCitation: result.source_citation,
      });
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to start interview");
      setStarting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 mb-6 glow"
        >
          <Brain className="w-10 h-10 text-white" />
        </motion.div>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-4">
          <span className="gradient-text">PG-AGI</span>{" "}
          <span className="text-white/80">Screening</span>
        </h1>
        <p className="text-white/40 text-lg max-w-2xl mx-auto leading-relaxed">
          Autonomous, role-based technical interview powered by adaptive RAG
          and real-time difficulty adjustment.
        </p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {[
          { icon: BookOpen, label: "Knowledge-Backed", desc: "Questions from ML textbooks" },
          { icon: Target, label: "Adaptive Difficulty", desc: "Simple → Moderate → Complex" },
          { icon: Zap, label: "Real-time Scoring", desc: "Cosine + Term overlap metrics" },
        ].map((f, i) => (
          <motion.div
            key={f.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 + i * 0.1 }}
            className="glass rounded-xl p-5 text-center"
          >
            <f.icon className="w-6 h-6 text-indigo-400 mx-auto mb-3" />
            <div className="text-sm font-medium text-white/80">{f.label}</div>
            <div className="text-xs text-white/30 mt-1">{f.desc}</div>
          </motion.div>
        ))}
      </div>

      {/* Main Setup Card */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.5 }}
        className="glass rounded-2xl p-8 sm:p-10"
      >
        {/* Candidate Info Step */}
        {step === "info" && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold text-white/90 mb-2">
              Candidate Information
            </h2>
            <div>
              <label className="block text-sm text-white/50 mb-2">Full Name</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <input
                  id="candidate-name"
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  placeholder="Enter your full name"
                  className="w-full pl-11 pr-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-white/20 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-white/50 mb-2">Target Role</label>
              <div className="relative">
                <Briefcase className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
                <select
                  id="job-role"
                  value={jobRole}
                  onChange={(e) => setJobRole(e.target.value)}
                  className="w-full pl-11 pr-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white appearance-none focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/20 transition-all"
                >
                  {JOB_ROLES.map((r) => (
                    <option key={r} value={r} className="bg-gray-900">{r}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm text-white/50 mb-2">
                Questions: {totalQuestions}
              </label>
              <input
                id="total-questions"
                type="range"
                min={3}
                max={15}
                value={totalQuestions}
                onChange={(e) => setTotalQuestions(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
              <div className="flex justify-between text-xs text-white/20 mt-1">
                <span>3 (Quick)</span>
                <span>15 (Thorough)</span>
              </div>
            </div>
            <button
              onClick={() => setStep("upload")}
              disabled={!candidateName.trim()}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium flex items-center justify-center gap-2 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-30 disabled:cursor-not-allowed transition-all glow"
            >
              Continue <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Resume Upload Step */}
        {step === "upload" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => setStep("info")}
                className="text-white/30 hover:text-white/60 text-sm transition-colors"
              >
                ← Back
              </button>
              <h2 className="text-xl font-semibold text-white/90">
                Resume Upload
              </h2>
            </div>
            <p className="text-sm text-white/40">
              Upload your resume for AI-powered skill extraction, or skip to start with manual skills.
            </p>

            {/* Drop Zone */}
            <label
              htmlFor="resume-upload"
              className="block border-2 border-dashed border-white/10 rounded-2xl p-10 text-center cursor-pointer hover:border-indigo-500/30 hover:bg-white/[0.02] transition-all"
            >
              {uploading ? (
                <Loader2 className="w-10 h-10 text-indigo-400 mx-auto animate-spin" />
              ) : resumeFile ? (
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
              ) : (
                <Upload className="w-10 h-10 text-white/20 mx-auto" />
              )}
              <p className="text-sm text-white/40 mt-4">
                {uploading
                  ? "Analyzing resume with AI..."
                  : resumeFile
                  ? resumeFile.name
                  : "Drop PDF or click to upload"}
              </p>
              <input
                id="resume-upload"
                type="file"
                accept=".pdf,.txt"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFileUpload(f);
                }}
              />
            </label>

            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                {error}
              </div>
            )}

            <button
              onClick={handleStartInterview}
              disabled={starting}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium flex items-center justify-center gap-2 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 transition-all glow"
            >
              {starting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Zap className="w-4 h-4" /> Start Interview
                </>
              )}
            </button>

            <button
              onClick={handleStartInterview}
              disabled={starting}
              className="w-full py-3 rounded-xl border border-white/10 text-white/40 text-sm hover:text-white/60 hover:border-white/20 transition-all"
            >
              Skip resume & start with role-based questions →
            </button>
          </div>
        )}

        {/* Review Step (after resume upload) */}
        {step === "review" && (
          <div className="space-y-6">
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => setStep("upload")}
                className="text-white/30 hover:text-white/60 text-sm transition-colors"
              >
                ← Back
              </button>
              <h2 className="text-xl font-semibold text-white/90">
                Skills Detected
              </h2>
            </div>

            <div className="flex flex-wrap gap-2">
              {skills.map((skill) => (
                <span
                  key={skill}
                  className="px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-500/15 text-indigo-300 border border-indigo-500/20"
                >
                  {skill}
                </span>
              ))}
              {skills.length === 0 && (
                <p className="text-sm text-white/30">
                  No specific skills detected. Interview will use role-based questions.
                </p>
              )}
            </div>

            <div className="glass rounded-xl p-4 text-sm text-white/40">
              <div className="flex items-center gap-2 mb-2 text-white/60">
                <FileText className="w-4 h-4" /> Resume Preview
              </div>
              <p className="line-clamp-4 leading-relaxed">{resumeText.slice(0, 500)}...</p>
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl p-3">
                {error}
              </div>
            )}

            <button
              onClick={handleStartInterview}
              disabled={starting}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium flex items-center justify-center gap-2 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 transition-all glow"
            >
              {starting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <>
                  <Zap className="w-4 h-4" /> Begin Technical Screening
                </>
              )}
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
}
