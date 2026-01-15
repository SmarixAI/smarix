"use client";

import React, { useState } from "react";
import { Mail, Send, Plus, Minus, Copy, Check, ArrowRight } from "lucide-react";
import { Space_Grotesk, Victor_Mono, Fira_Code } from "next/font/google";

const spaceGrotesk = Space_Grotesk({ subsets: ["latin"] });
const victorMono = Victor_Mono({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
});
const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "demo",
    message: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<
    "idle" | "success" | "error"
  >("idle");
  const [openFaq, setOpenFaq] = useState<number | null>(0);
  const [copied, setCopied] = useState(false);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitStatus("success");
      setFormData({ name: "", email: "", subject: "demo", message: "" });
      setTimeout(() => setSubmitStatus("idle"), 5000);
    }, 1500);
  };

  const copyEmail = () => {
    navigator.clipboard.writeText("hello@smarix.ai");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const faqs = [
    {
      q: "How fast is the integration?",
      a: "Integration typically takes less than 15 minutes. Just connect your repo and define your scope.",
    },
    {
      q: "Is my codebase secure?",
      a: "Yes. We process data in ephemeral environments. Your code never persists on our training servers.",
    },
    {
      q: "What languages are supported?",
      a: "We support all major programming languages including Python, JavaScript, Java, C#, Ruby, and more.",
    },
  ];

  return (
    <main
      className={`min-h-screen bg-[#F8FAFC] text-[#0E1B2E] selection:bg-[#3B82F6] selection:text-white pt-50 pb-12 px-4 md:px-6 lg:px-8`}
    >
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none -z-10" />
      <div className="fixed inset-0 bg-gradient-to-tr from-blue-50/50 via-transparent to-indigo-50/50 pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto h-full">
        <div className="grid lg:grid-cols-12 gap-6 h-full items-start">
          <div className="lg:col-span-5 flex flex-col gap-6 sticky top-24">
            <div className="space-y-3">
              <h1
                className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-[#0E1B2E] leading-[0.9]`}
              >
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600">
                  Contact Us
                </span>
              </h1>
              <p
                className={`${spaceGrotesk.className} text-lg text-[#0E1B2E]/70 max-w-md leading-relaxed font-medium`}
              >
                Transform your workflow with Smarix. Technical questions or
                partnership inquiries? We are ready.
              </p>
            </div>

            <div className="group relative overflow-hidden bg-[#0E1B2E] text-white rounded-xl p-6 transition-all duration-300 shadow-xl shadow-blue-900/10 border border-[#0E1B2E]">
              <div className="absolute top-0 right-0 w-64 h-64 bg-blue-600/20 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
              <div className="absolute bottom-0 left-0 w-32 h-32 bg-indigo-500/20 rounded-full blur-2xl translate-y-1/2 -translate-x-1/2" />

              <div className="relative z-10">
                <div className="flex items-center justify-between mb-6">
                  <div className="p-2 bg-white/10 rounded-lg backdrop-blur-sm">
                    <Mail className="w-5 h-5 text-blue-200" />
                  </div>
                </div>

                <div className="space-y-1">
                  <p
                    className={`${victorMono.className} text-xs text-blue-200/60`}
                  >
                    Email ID
                  </p>
                  <div className="flex items-center justify-between gap-4">
                    <a
                      href="mailto:contact@smarix.net"
                      className={`${firaCode.className} text-xl md:text-2xl font-bold hover:text-blue-300 transition-colors tracking-tight`}
                    >
                      contact@smarix.net
                    </a>
                    <button
                      onClick={copyEmail}
                      className="p-2 rounded-lg bg-white/10 hover:bg-white/20 hover:text-blue-300 transition-all active:scale-95 border border-white/5"
                    >
                      {copied ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-white/60 backdrop-blur-sm rounded-xl border border-blue-100 overflow-hidden shadow-sm">
              <div
                className={`px-5 py-3 border-b border-blue-100 bg-blue-50/50 ${victorMono.className} text-xs font-bold uppercase tracking-wider text-blue-900/70 flex items-center gap-2`}
              >
                <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
                Frequently Asked Questions
              </div>
              <div>
                {faqs.map((item, i) => (
                  <div
                    key={i}
                    className="border-b border-blue-50 last:border-0"
                  >
                    <button
                      onClick={() => setOpenFaq(openFaq === i ? null : i)}
                      className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white transition-colors group"
                    >
                      <span
                        className={`${firaCode.className} font-medium text-[#0E1B2E] text-xs md:text-sm group-hover:text-blue-700 transition-colors`}
                      >
                        {item.q}
                      </span>
                      {openFaq === i ? (
                        <Minus className="w-3.5 h-3.5 text-blue-500" />
                      ) : (
                        <Plus className="w-3.5 h-3.5 text-gray-400 group-hover:text-blue-500 transition-colors" />
                      )}
                    </button>
                    <div
                      className={`overflow-hidden transition-all duration-300 ease-in-out ${
                        openFaq === i
                          ? "max-h-24 opacity-100"
                          : "max-h-0 opacity-0"
                      }`}
                    >
                      <p
                        className={`px-5 pb-5 pt-0 ${victorMono.className} text-xs text-[#0E1B2E]/60 leading-relaxed`}
                      >
                        {item.a}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="lg:col-span-7">
            <div className="h-full bg-white rounded-xl border border-blue-100 p-6 md:p-8 shadow-xl shadow-blue-900/5 relative overflow-hidden">
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-cyan-500" />

              <div className="mb-6 flex items-end justify-between border-b border-slate-100 pb-6">
                <div>
                  <h3
                    className={`${firaCode.className} text-xl font-bold text-[#0E1B2E] mb-1 flex items-center gap-2`}
                  >
                    Fill out this form to get in touch
                    <span className="w-2 h-2 rounded-full bg-green-500" />
                  </h3>
                  <p
                    className={`${victorMono.className} text-xs text-[#0E1B2E]/50`}
                  >
                    Our team will be in touch. 
                  </p>
                </div>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label
                      htmlFor="name"
                      className={`${victorMono.className} text-[10px] font-bold uppercase tracking-wider text-blue-900/60`}
                    >
                      Name *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      required
                      value={formData.name}
                      onChange={handleInputChange}
                      className={`w-full bg-[#F8FAFC] border border-slate-200 rounded-lg px-3 py-2.5 text-[#0E1B2E] focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all ${firaCode.className} text-sm font-medium placeholder:text-slate-400`}
                      placeholder="John Doe"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label
                      htmlFor="email"
                      className={`${victorMono.className} text-[10px] font-bold uppercase tracking-wider text-blue-900/60`}
                    >
                      Email ID *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      required
                      value={formData.email}
                      onChange={handleInputChange}
                      className={`w-full bg-[#F8FAFC] border border-slate-200 rounded-lg px-3 py-2.5 text-[#0E1B2E] focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all ${firaCode.className} text-sm font-medium placeholder:text-slate-400`}
                      placeholder="john@company.com"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label
                      htmlFor="subject"
                      className={`${victorMono.className} text-[10px] font-bold uppercase tracking-wider text-blue-900/60`}
                    >
                      Reason for Contact *
                    </label>
                  <div className="relative">
                    <select
                      id="subject"
                      name="subject"
                      value={formData.subject}
                      onChange={handleInputChange}
                      className={`w-full bg-[#F8FAFC] border border-slate-200 rounded-lg px-3 py-2.5 text-[#0E1B2E] focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 appearance-none transition-all ${firaCode.className} text-sm font-medium`}
                    >
                      <option value="demo">Request System Demo</option>
                      <option value="pricing">Enterprise Pricing</option>
                      <option value="support">Technical Support</option>
                    </select>
                    <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400">
                      <div className="grid grid-cols-2 gap-0.5">
                        <div className="w-1 h-1 bg-slate-400 rounded-full" />
                        <div className="w-1 h-1 bg-slate-400 rounded-full" />
                        <div className="w-1 h-1 bg-slate-400 rounded-full" />
                        <div className="w-1 h-1 bg-slate-400 rounded-full" />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label
                    htmlFor="message"
                    className={`${victorMono.className} text-[10px] font-bold uppercase tracking-wider text-blue-900/60`}
                  >
                    Comments *
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    required
                    rows={5}
                    value={formData.message}
                    onChange={handleInputChange}
                    className={`w-full bg-[#F8FAFC] border border-slate-200 rounded-lg px-3 py-2.5 text-[#0E1B2E] focus:outline-none focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-500/10 transition-all resize-none ${firaCode.className} text-sm font-medium placeholder:text-slate-400`}
                    placeholder="Enter comments here..."
                  />
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting || submitStatus === "success"}
                    className={`
                      w-full group relative px-6 py-3.5 
                      bg-gradient-to-r from-[#0E1B2E] via-[#1e3a8a] to-[#0E1B2E] bg-[length:200%_auto]
                      hover:bg-[position:right_center]
                      text-white rounded-lg overflow-hidden
                      transition-all duration-500 shadow-lg shadow-blue-900/20
                      disabled:opacity-70 disabled:cursor-not-allowed
                    `}
                  >
                    <div className="relative z-10 flex items-center justify-center gap-3">
                      <span
                        className={`${firaCode.className} font-semibold tracking-wide`}
                      >
                        {isSubmitting
                          ? "Subkitting form..."
                          : submitStatus === "success"
                          ? "Form has been submitted!"
                          : "SUBMIT"}
                      </span>
                      {isSubmitting ? (
                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      ) : submitStatus === "success" ? (
                        <Check className="w-4 h-4 text-green-400" />
                      ) : (
                        <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1 text-blue-200" />
                      )}
                    </div>
                  </button>
                  <div className="mt-3 text-center">
                    <p
                      className={`${victorMono.className} text-[10px] text-[#0E1B2E]/40`}
                    >
                      Encrypted End-to-End
                    </p>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}