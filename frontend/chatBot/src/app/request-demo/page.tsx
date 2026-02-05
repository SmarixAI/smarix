"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  User,
  Building2,
  Briefcase,
  Mail,
  Phone,
  MessageSquare,
  CheckCircle2,
  Loader2,
  Send,
  Clock,
  MonitorPlay,
  Users,
  HelpCircle,
  Globe,
  Users2,
  Calendar,
  ChevronDown,
  Search,
  AlertCircle,
  Home,
} from "lucide-react";
import { Fira_Code, Victor_Mono } from "next/font/google";

const firaCode = Fira_Code({
  weight: ["400", "500", "600", "700"],
  subsets: ["latin"],
  display: "swap",
});

const victorMono = Victor_Mono({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
});

interface Country {
  name: string;
  code: string;
  flag: string;
  idd: string;
}

// GIF showcase items - replace these URLs with your actual CDN/S3 URLs
const gifShowcase = [
  {
    id: 1,
    url: "https://d285vgwdgs4ml7.cloudfront.net/GIFs/chatbot1_gif.gif",
    title: "Smarix Chatbot",
    description: "Conversational AI interface",
  },
  {
    id: 2,
    url: "https://d285vgwdgs4ml7.cloudfront.net/GIFs/onboarding3_gif.gif",
    title: "Smarix Onboarding",
    description: "Effortless employee onboarding"
  },
  {
    id: 3,
    url: "https://d285vgwdgs4ml7.cloudfront.net/GIFs/offboarding2_gif.gif", 
    title: "Smarix Offboarding",
    description: "Seamless knowledge transfer",
  },
];

export default function ContactPage() {
  const router = useRouter();
  const [countries, setCountries] = useState<Country[]>([]);
  const [filteredCountries, setFilteredCountries] = useState<Country[]>([]);
  const [selectedCountry, setSelectedCountry] = useState<Country>({
    name: "United States",
    code: "US",
    flag: "🇺🇸",
    idd: "+1",
  });
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [countrySearch, setCountrySearch] = useState("");
  const [activeGifIndex, setActiveGifIndex] = useState(0);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    company: "",
    jobTitle: "",
    companySize: "",
    country: "",
    contactReason: "",
    preferredDate: "",
    message: "",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState("");

  // Auto-rotate GIFs every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveGifIndex((prev) => (prev + 1) % gifShowcase.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchCountries = async () => {
      try {
        const response = await fetch(
          "https://restcountries.com/v3.1/all?fields=name,flags,idd,cca2",
        );
        const data = await response.json();
        const formatted: Country[] = data
          .map((c: any) => ({
            name: c.name.common,
            code: c.cca2,
            flag: c.flags.svg,
            idd: c.idd.root ? `${c.idd.root}${c.idd.suffixes?.[0] || ""}` : "",
          }))
          .filter((c: Country) => c.idd)
          .sort((a: Country, b: Country) => a.name.localeCompare(b.name));

        setCountries(formatted);
        setFilteredCountries(formatted);
      } catch (e) {
        console.error(e);
      }
    };
    fetchCountries();
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowCountryDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const filtered = countries.filter(
      (c) =>
        c.name.toLowerCase().includes(countrySearch.toLowerCase()) ||
        c.idd.includes(countrySearch),
    );
    setFilteredCountries(filtered);
  }, [countrySearch, countries]);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError("");
  };

  const validateForm = () => {
    if (
      !formData.firstName ||
      !formData.lastName ||
      !formData.email ||
      !formData.phone ||
      !formData.message
    )
      return false;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(formData.email)) {
      setError("Please enter a valid email address.");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) return;

    const submittedEmails = JSON.parse(
      localStorage.getItem("smarix_submissions") || "[]",
    );
    if (submittedEmails.includes(formData.email)) {
      setError("A request with this email has already been submitted.");
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch("/api/request-demo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...formData,
          fullPhone: `${selectedCountry.idd} ${formData.phone}`,
        }),
      });

      if (!response.ok) throw new Error("Failed to send message");

      const newSubmissions = [...submittedEmails, formData.email];
      localStorage.setItem(
        "smarix_submissions",
        JSON.stringify(newSubmissions),
      );

      setIsSubmitted(true);
    } catch (err) {
      setError("Something went wrong. Please try again later.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="h-screen bg-white text-[#0E1B2E] selection:bg-[#0E1B2E] selection:text-white overflow-hidden relative font-sans">
      <div className="flex flex-col lg:flex-row h-screen">
        <div className="w-full lg:w-1/2 flex flex-col relative z-10 h-screen">
          <div className="h-screen overflow-y-auto no-scrollbar">
            <div className="p-6 lg:p-12 xl:px-20 xl:py-12 flex flex-col justify-start min-h-full">
              <AnimatePresence mode="wait">
                {!isSubmitted ? (
                  <motion.div
                    key="form"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.5 }}
                    className="max-w-2xl mx-auto w-full pb-10"
                  >
                    <div className="mb-8">
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className="flex items-center gap-2 mb-0"
                      >
                        <span
                          className={`${firaCode.className} text-[#0E1B2E] font-semibold tracking-wider text-sm`}
                        >
                          GET IN TOUCH
                        </span>
                      </motion.div>
                      <h1
                        className={`${firaCode.className} text-3xl md:text-4xl font-bold text-[#0E1B2E] mb-3`}
                      >
                        Let's Build the Future.
                      </h1>
                      <p
                        className={`${victorMono.className} text-[#0E1B2E]/60 text-sm md:text-base mb-6`}
                      >
                        Ready to streamline your enterprise knowledge? Fill in
                        the details below.
                      </p>

                      <div className="flex flex-wrap gap-3 mb-4">
                        {[
                          { icon: Clock, text: "24hr Response" },
                          { icon: MonitorPlay, text: "30-min Demo" },
                          { icon: Users, text: "Expert Q&A" },
                        ].map((item, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 bg-[#FAFAFA] border border-[#0E1B2E]/10 px-3 py-2 rounded-lg"
                          >
                            <item.icon className="w-4 h-4 text-[#0E1B2E]" />
                            <span
                              className={`${victorMono.className} text-xs font-bold text-[#0E1B2E]/80`}
                            >
                              {item.text}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <form onSubmit={handleSubmit} className="space-y-4 mb-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            First Name
                          </label>
                          <div className="relative group">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="text"
                              name="firstName"
                              required
                              value={formData.firstName}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                              placeholder="Jane"
                            />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Last Name
                          </label>
                          <div className="relative group">
                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="text"
                              name="lastName"
                              required
                              value={formData.lastName}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                              placeholder="Doe"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Job Title
                          </label>
                          <div className="relative group">
                            <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="text"
                              name="jobTitle"
                              required
                              value={formData.jobTitle}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                              placeholder="Product Manager"
                            />
                          </div>
                        </div>
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Company Name
                          </label>
                          <div className="relative group">
                            <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="text"
                              name="company"
                              required
                              value={formData.company}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                              placeholder="Acme Inc."
                            />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Company Size
                          </label>
                          <div className="relative group">
                            <Users2 className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <select
                              name="companySize"
                              required
                              value={formData.companySize}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all appearance-none text-[#0E1B2E]`}
                            >
                              <option value="" disabled>
                                Select Size
                              </option>
                              <option value="1-10">1 - 10 employees</option>
                              <option value="11-50">11 - 50 employees</option>
                              <option value="51-200">51 - 200 employees</option>
                              <option value="201-500">
                                201 - 500 employees
                              </option>
                              <option value="500+">500+ employees</option>
                            </select>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Country
                          </label>
                          <div className="relative group">
                            <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="text"
                              name="country"
                              required
                              value={formData.country}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                              placeholder="United States"
                            />
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Email Address
                          </label>
                          <div className="relative group">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="email"
                              name="email"
                              required
                              value={formData.email}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                              placeholder="name@work.com"
                            />
                          </div>
                        </div>
                        <div className="space-y-1 relative" ref={dropdownRef}>
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Phone Number
                          </label>
                          <div className="flex gap-2">
                            <div className="relative w-1/3 min-w-[130px]">
                              <button
                                type="button"
                                onClick={() =>
                                  setShowCountryDropdown(!showCountryDropdown)
                                }
                                className="w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 px-3 text-sm flex items-center justify-between gap-2 hover:bg-[#F0F0F0] transition-colors h-full"
                              >
                                <div className="flex items-center gap-2 overflow-hidden">
                                  <img
                                    src={selectedCountry.flag}
                                    alt=""
                                    className="w-5 h-auto object-cover"
                                  />
                                  <span
                                    className={`${victorMono.className} truncate`}
                                  >
                                    {selectedCountry.idd}
                                  </span>
                                </div>
                                <ChevronDown className="w-3 h-3 opacity-50 flex-shrink-0" />
                              </button>

                              {showCountryDropdown && (
                                <div className="absolute top-full left-0 w-[300px] mt-1 bg-white border border-[#0E1B2E]/10 rounded-lg shadow-xl z-50 max-h-[300px] flex flex-col">
                                  <div className="p-2 border-b border-[#0E1B2E]/5 sticky top-0 bg-white rounded-t-lg">
                                    <div className="relative">
                                      <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3 h-3 text-[#0E1B2E]/40" />
                                      <input
                                        type="text"
                                        value={countrySearch}
                                        onChange={(e) =>
                                          setCountrySearch(e.target.value)
                                        }
                                        className={`${victorMono.className} w-full bg-[#FAFAFA] pl-7 pr-2 py-2 text-xs rounded border border-[#0E1B2E]/5 focus:outline-none`}
                                        placeholder="Search country..."
                                        autoFocus
                                      />
                                    </div>
                                  </div>
                                  <div className="overflow-y-auto flex-1">
                                    {filteredCountries.map((c) => (
                                      <button
                                        key={c.code}
                                        type="button"
                                        onClick={() => {
                                          setSelectedCountry(c);
                                          setShowCountryDropdown(false);
                                          setCountrySearch("");
                                        }}
                                        className="w-full px-3 py-2 text-left hover:bg-[#FAFAFA] flex items-center gap-3 transition-colors border-b border-[#0E1B2E]/5 last:border-0"
                                      >
                                        <img
                                          src={c.flag}
                                          alt=""
                                          className="w-5 h-auto"
                                        />
                                        <span
                                          className={`${victorMono.className} text-xs flex-1 truncate`}
                                        >
                                          {c.name}
                                        </span>
                                        <span
                                          className={`${firaCode.className} text-[10px] text-[#0E1B2E]/50`}
                                        >
                                          {c.idd}
                                        </span>
                                      </button>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                            <div className="relative group flex-1">
                              <input
                                type="tel"
                                name="phone"
                                required
                                value={formData.phone}
                                onChange={handleInputChange}
                                className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 px-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all`}
                                placeholder="000-0000"
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Reason to Contact
                          </label>
                          <div className="relative group">
                            <HelpCircle className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <select
                              name="contactReason"
                              required
                              value={formData.contactReason}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all appearance-none text-[#0E1B2E]`}
                            >
                              <option value="" disabled>
                                Select Reason
                              </option>
                              <option value="sales">Sales Inquiry</option>
                              <option value="demo">Request a Demo</option>
                              <option value="support">Technical Support</option>
                              <option value="partnership">
                                Partnership Opportunity
                              </option>
                              <option value="other">Other</option>
                            </select>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <label
                            className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                          >
                            Preferred Date
                          </label>
                          <div className="relative group">
                            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                            <input
                              type="date"
                              name="preferredDate"
                              value={formData.preferredDate}
                              onChange={handleInputChange}
                              className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all text-[#0E1B2E]`}
                            />
                          </div>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <label
                          className={`${firaCode.className} text-[10px] font-bold text-[#0E1B2E]/50 uppercase tracking-wide`}
                        >
                          Message
                        </label>
                        <div className="relative group">
                          <MessageSquare className="absolute left-3 top-3 w-4 h-4 text-[#0E1B2E]/30 group-focus-within:text-[#0E1B2E] transition-colors" />
                          <textarea
                            name="message"
                            required
                            rows={3}
                            value={formData.message}
                            onChange={handleInputChange}
                            className={`${victorMono.className} w-full bg-[#FAFAFA] border border-[#0E1B2E]/10 rounded-lg py-3 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-[#0E1B2E]/10 focus:border-[#0E1B2E] transition-all resize-none`}
                            placeholder="Tell us about your requirements..."
                          />
                        </div>
                      </div>

                      {error && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          className="flex items-center gap-2 text-red-500 bg-red-50 p-2 rounded text-xs"
                        >
                          <AlertCircle className="w-3 h-3" />
                          <span className={victorMono.className}>{error}</span>
                        </motion.div>
                      )}

                      <motion.button
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.99 }}
                        disabled={isSubmitting}
                        className={`
                                ${firaCode.className} w-full py-4 bg-[#0E1B2E] text-white rounded-lg
                                font-semibold text-base flex items-center justify-center gap-2
                                shadow-lg shadow-[#0E1B2E]/20 hover:shadow-xl hover:shadow-[#0E1B2E]/30
                                transition-all duration-300 disabled:opacity-70 disabled:cursor-not-allowed
                            `}
                      >
                        {isSubmitting ? (
                          <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                          <>
                            Submit Inquiry <Send className="w-4 h-4" />
                          </>
                        )}
                      </motion.button>
                    </form>

                    <div className="bg-[#FAFAFA] border border-[#0E1B2E]/5 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-white rounded-lg border border-[#0E1B2E]/10">
                          <HelpCircle className="w-5 h-5 text-[#0E1B2E]" />
                        </div>
                        <div>
                          <h4
                            className={`${firaCode.className} text-sm font-bold text-[#0E1B2E]`}
                          >
                            Need Immediate Help?
                          </h4>
                          <p
                            className={`${victorMono.className} text-xs text-[#0E1B2E]/60`}
                          >
                            Direct line to our team.
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-1">
                        <a
                          href="mailto:contact@smarix.net"
                          className={`${victorMono.className} text-xs font-bold text-[#0E1B2E] hover:underline flex items-center gap-2`}
                        >
                          <Mail className="w-3 h-3" /> contact@smarix.net
                        </a>
                        <a
                          href="tel:+917607066219"
                          className={`${victorMono.className} text-xs font-bold text-[#0E1B2E] hover:underline flex items-center gap-2`}
                        >
                          <Phone className="w-3 h-3" /> +91 76070 66219
                        </a>
                      </div>
                    </div>
                  </motion.div>
                ) : (
                  <motion.div
                    key="success"
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.5, type: "spring" }}
                    className="max-w-xl mx-auto w-full bg-[#FAFAFA] border border-[#0E1B2E]/5 p-12 rounded-3xl text-center shadow-2xl shadow-[#0E1B2E]/5 mt-10"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{
                        delay: 0.2,
                        type: "spring",
                        stiffness: 200,
                      }}
                      className="w-24 h-24 bg-[#0E1B2E] rounded-full flex items-center justify-center mx-auto mb-8 shadow-xl shadow-[#0E1B2E]/20"
                    >
                      <CheckCircle2 className="w-10 h-10 text-white" />
                    </motion.div>

                    <h2
                      className={`${firaCode.className} text-3xl font-bold text-[#0E1B2E] mb-4`}
                    >
                      Request Received!
                    </h2>

                    <p
                      className={`${victorMono.className} text-[#0E1B2E]/70 text-lg mb-8 leading-relaxed`}
                    >
                      Thank you for your interest in Smarix. Your inquiry has
                      been securely registered in our system. A senior executive
                      will review your requirements and reach out to you
                      shortly.
                    </p>

                    <div className="p-4 bg-white border border-[#0E1B2E]/10 rounded-xl inline-block mb-10">
                      <p
                        className={`${firaCode.className} text-xs text-[#0E1B2E]/50 font-bold uppercase tracking-wider`}
                      >
                        Reference ID
                      </p>
                      <p
                        className={`${victorMono.className} text-[#0E1B2E] font-bold mt-1`}
                      >
                        SMX-{Math.floor(Math.random() * 100000)}
                      </p>
                    </div>

                    <motion.button
                      onClick={() => router.push("/landing")}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className={`
                            ${firaCode.className} w-full py-4 bg-[#0E1B2E] text-white rounded-xl
                            font-semibold text-base flex items-center justify-center gap-2
                            shadow-lg shadow-[#0E1B2E]/10 hover:shadow-xl hover:shadow-[#0E1B2E]/20
                            transition-all duration-300
                            `}
                    >
                      <Home className="w-5 h-5" />
                      Back to Home
                    </motion.button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>

        {/* RIGHT PANEL - GIF SHOWCASE */}
        <div className="hidden lg:flex w-1/2 bg-[#0E1B2E] relative overflow-hidden items-center justify-center fixed right-0 h-screen">
          {/* Background Grid */}
          <div className="absolute inset-0 opacity-10">
            <div className="absolute top-0 left-0 w-full h-full bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:50px_50px]" />
          </div>

          {/* Gradient Orbs */}
          <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[120px]" />
          <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-500/10 rounded-full blur-[120px]" />

          {/* Main Content Container */}
          <div className="relative z-10 w-full h-full flex flex-col items-center justify-center px-12 py-16">
            {/* Main GIF Display */}
            <div className="relative w-full max-w-2xl">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeGifIndex}
                  initial={{ opacity: 0, scale: 0.9, y: 20 }}
                  animate={{ opacity: 1, scale: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.9, y: -20 }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                  className="relative"
                >
                  {/* GIF Container with Glass Effect */}
                  <div className="relative bg-white/5 backdrop-blur-xl border border-white/10 rounded-3xl p-4 shadow-2xl">
                    <div className="aspect-video rounded-2xl overflow-hidden bg-[#0E1B2E]/50 relative">
                      <img
                        src={gifShowcase[activeGifIndex].url}
                        alt={gifShowcase[activeGifIndex].title}
                        className="w-full h-full object-cover"
                      />
                      {/* Overlay gradient for better text visibility */}
                      <div className="absolute inset-0 bg-gradient-to-t from-[#0E1B2E]/80 via-transparent to-transparent" />
                    </div>

                    {/* Info Badge */}
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.3 }}
                      className="absolute bottom-8 left-8 right-8"
                    >
                      <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-4">
                        <h3
                          className={`${firaCode.className} text-white text-lg font-bold mb-1`}
                        >
                          {gifShowcase[activeGifIndex].title}
                        </h3>
                        <p
                          className={`${victorMono.className} text-white/70 text-sm`}
                        >
                          {gifShowcase[activeGifIndex].description}
                        </p>
                      </div>
                    </motion.div>
                  </div>

                  {/* Decorative Elements */}
                  <motion.div
                    animate={{
                      rotate: [0, 360],
                      scale: [1, 1.1, 1],
                    }}
                    transition={{
                      duration: 20,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="absolute -top-6 -right-6 w-32 h-32 border border-white/10 rounded-full"
                  />
                  <motion.div
                    animate={{
                      rotate: [360, 0],
                      scale: [1, 1.05, 1],
                    }}
                    transition={{
                      duration: 15,
                      repeat: Infinity,
                      ease: "linear",
                    }}
                    className="absolute -bottom-8 -left-8 w-40 h-40 border border-white/5 rounded-full"
                  />
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Navigation Dots */}
            <div className="flex gap-3 mt-12">
              {gifShowcase.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setActiveGifIndex(index)}
                  className="group relative"
                >
                  <div
                    className={`
                    w-3 h-3 rounded-full transition-all duration-300
                    ${
                      index === activeGifIndex
                        ? "bg-white w-8"
                        : "bg-white/30 hover:bg-white/50"
                    }
                  `}
                  />
                  {index === activeGifIndex && (
                    <motion.div
                      layoutId="activeIndicator"
                      className="absolute inset-0 rounded-full bg-white/20 blur-md"
                    />
                  )}
                </button>
              ))}
            </div>

            {/* Feature Tags */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              className="flex flex-wrap gap-3 mt-10 justify-center"
            >
              {["Chatbot", "Onboarding", "Offboarding"].map(
                (tag, i) => (
                  <div
                    key={i}
                    className="px-4 py-2 bg-white/5 backdrop-blur-sm border border-white/10 rounded-full"
                  >
                    <span
                      className={`${victorMono.className} text-white/80 text-xs font-bold`}
                    >
                      {tag}
                    </span>
                  </div>
                ),
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </main>
  );
}
