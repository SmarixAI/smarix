'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import Link from 'next/link';
import { Calendar, Clock, ArrowRight, Tag, User, Search, BookOpen } from 'lucide-react';
import { Space_Grotesk, Victor_Mono, Fira_Code } from 'next/font/google';
import { getAllPosts } from '@/data/blogPosts';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const victorMono = Victor_Mono({ weight: ["400", "500", "700"], subsets: ['latin'] });
const firaCode = Fira_Code({ weight: ["400", "500", "600", "700"], subsets: ['latin'] });

const categories = ['All', 'Engineering', 'AI', 'Documentation', 'Culture', 'Management'];

export default function BlogPage() {
  const blogPosts = getAllPosts();
  const [selectedCategory, setSelectedCategory] = React.useState('All');
  const [searchQuery, setSearchQuery] = React.useState('');

  const filteredPosts = blogPosts.filter(post => {
    const matchesCategory = selectedCategory === 'All' || post.category === selectedCategory;
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         post.excerpt.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const featuredPosts = filteredPosts.filter(post => post.featured);
  const regularPosts = filteredPosts.filter(post => !post.featured);

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      {/* Hero Section */}
      <section className="relative w-full pt-32 pb-16 px-6 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-12"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#0E1B2E]/5 border border-[#0E1B2E]/10 mb-6"
            >
              <BookOpen className="w-4 h-4 text-[#0E1B2E]/60" />
              <span className={`${victorMono.className} text-xs text-[#0E1B2E]/70`}>
                Insights & Stories
              </span>
            </motion.div>
            
            <h1 className={`${firaCode.className} text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6`}>
              Smarix Blog
            </h1>
            
            <p className={`${victorMono.className} text-xl text-[#0E1B2E]/70 max-w-2xl mx-auto leading-relaxed`}>
              Explore insights on engineering knowledge management, AI-powered solutions, and best practices.
            </p>
          </motion.div>

          {/* Search Bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="max-w-2xl mx-auto mb-8"
          >
            <div className="relative">
              <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-[#0E1B2E]/40" />
              <input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className={`
                  w-full pl-12 pr-4 py-3 rounded-full border-2 border-[#0E1B2E]/10
                  bg-white/60 backdrop-blur-sm
                  ${firaCode.className} text-sm
                  focus:outline-none focus:border-[#0E1B2E]/30
                  transition-all duration-200
                `}
              />
            </div>
          </motion.div>

          {/* Category Filter */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-wrap justify-center gap-3 mb-12"
          >
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`
                  px-4 py-2 rounded-full text-sm font-medium transition-all duration-200
                  ${selectedCategory === category
                    ? 'bg-[#0E1B2E] text-white shadow-lg'
                    : 'bg-white/60 text-[#0E1B2E]/70 hover:bg-white/80 border border-[#0E1B2E]/10'
                  }
                  ${firaCode.className}
                `}
              >
                {category}
              </button>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Featured Posts */}
      {featuredPosts.length > 0 && (
        <section className="relative py-12 px-6">
          <div className="max-w-7xl mx-auto">
            <h2 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-8`}>
              Featured Articles
            </h2>
            <div className="grid md:grid-cols-2 gap-8 mb-16">
              {featuredPosts.map((post, index) => (
                <motion.article
                  key={post.id}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: 0.1 * index }}
                  className="group relative"
                >
                  <Link href={`/blog/${post.slug}`} className="block">
                    <div className={`
                    relative h-full rounded-2xl border-2 border-[#0E1B2E]/10 bg-white
                    p-8 transition-all duration-300
                    hover:shadow-xl hover:shadow-black/10 hover:-translate-y-1
                    overflow-hidden
                  `}>
                    <div className={`
                      absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${post.gradient}
                      opacity-5 rounded-bl-full transform translate-x-8 -translate-y-8
                      group-hover:opacity-10 transition-opacity duration-300
                    `} />
                    
                    <div className="relative z-10">
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`
                          px-3 py-1 rounded-full text-xs font-semibold
                          bg-[#0E1B2E]/5 text-[#0E1B2E]
                          ${firaCode.className}
                        `}>
                          {post.category}
                        </span>
                        <span className={`${victorMono.className} text-xs text-[#0E1B2E]/40`}>
                          {post.readTime}
                        </span>
                      </div>
                      
                      <h3 className={`
                        ${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-3
                        group-hover:text-blue-600 transition-colors
                      `}>
                        {post.title}
                      </h3>
                      
                      <p className={`${victorMono.className} text-base text-[#0E1B2E]/70 mb-6 leading-relaxed`}>
                        {post.excerpt}
                      </p>
                      
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <User className="w-4 h-4 text-[#0E1B2E]/40" />
                          <span className={`${victorMono.className} text-sm text-[#0E1B2E]/60`}>
                            {post.author}
                          </span>
                        </div>
                        <ArrowRight className="w-5 h-5 text-[#0E1B2E]/40 group-hover:text-[#0E1B2E] group-hover:translate-x-1 transition-all" />
                      </div>
                    </div>
                  </div>
                  </Link>
                </motion.article>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Regular Posts Grid */}
      <section className="relative py-12 px-6">
        <div className="max-w-7xl mx-auto">
          <h2 className={`${firaCode.className} text-2xl font-bold text-[#0E1B2E] mb-8`}>
            All Articles
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {regularPosts.map((post, index) => (
              <motion.article
                key={post.id}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: 0.1 * index }}
                className="group relative"
              >
                <Link href={`/blog/${post.slug}`} className="block">
                  <div className={`
                  relative h-full rounded-xl border border-[#0E1B2E]/10 bg-white
                  p-6 transition-all duration-300
                  hover:shadow-lg hover:shadow-black/5 hover:-translate-y-1
                  overflow-hidden
                `}>
                  <div className={`
                    absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${post.gradient}
                    opacity-5 rounded-bl-full
                    group-hover:opacity-10 transition-opacity duration-300
                  `} />
                  
                  <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`
                        px-2 py-1 rounded text-xs font-semibold
                        bg-[#0E1B2E]/5 text-[#0E1B2E]
                        ${firaCode.className}
                      `}>
                        {post.category}
                      </span>
                    </div>
                    
                    <h3 className={`
                      ${firaCode.className} text-lg font-bold text-[#0E1B2E] mb-2
                      group-hover:text-blue-600 transition-colors line-clamp-2
                    `}>
                      {post.title}
                    </h3>
                    
                    <p className={`${victorMono.className} text-sm text-[#0E1B2E]/70 mb-4 leading-relaxed line-clamp-2`}>
                      {post.excerpt}
                    </p>
                    
                    <div className="flex items-center justify-between text-xs text-[#0E1B2E]/40">
                      <span className={`${victorMono.className}`}>{post.readTime}</span>
                      <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    </div>
                  </div>
                </div>
                </Link>
              </motion.article>
            ))}
          </div>

          {filteredPosts.length === 0 && (
            <div className="text-center py-16">
              <p className={`${victorMono.className} text-lg text-[#0E1B2E]/50`}>
                No articles found. Try a different search or category.
              </p>
            </div>
          )}
        </div>
      </section>

      <Footer />
    </main>
  );
}

