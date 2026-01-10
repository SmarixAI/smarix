'use client';

import React, { useEffect, useState } from 'react';
import { useParams, notFound } from 'next/navigation';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { Navbar } from '@/components/landing/Navbar';
import { Footer } from '@/components/landing/Footer';
import { Calendar, Clock, ArrowLeft, User, Tag } from 'lucide-react';
import { Space_Grotesk, Victor_Mono, Fira_Code } from 'next/font/google';
import { getPostBySlug, getAllPosts } from '@/data/blogPosts';
import ReactMarkdown from 'react-markdown';

const spaceGrotesk = Space_Grotesk({ subsets: ['latin'] });
const victorMono = Victor_Mono({ weight: ["400", "500", "700"], subsets: ['latin'] });
const firaCode = Fira_Code({ weight: ["400", "500", "600", "700"], subsets: ['latin'] });

export default function BlogPostPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [post, setPost] = useState(getPostBySlug(slug));

  useEffect(() => {
    setPost(getPostBySlug(slug));
  }, [slug]);

  if (!post) {
    notFound();
  }

  // Format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  return (
    <main className="min-h-screen bg-[#FAFAFA] text-[#0E1B2E] relative selection:bg-[#0E1B2E] selection:text-white">
      <Navbar />
      
      {/* Back Button */}
      <section className="relative pt-32 pb-8 px-6">
        <div className="max-w-4xl mx-auto">
          <Link 
            href="/blog"
            className="inline-flex items-center gap-2 text-[#0E1B2E]/60 hover:text-[#0E1B2E] transition-colors group"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className={`${victorMono.className} text-sm`}>Back to Blog</span>
          </Link>
        </div>
      </section>

      {/* Article Header */}
      <section className="relative pb-12 px-6">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#0E1B2E05_1px,transparent_1px),linear-gradient(to_bottom,#0E1B2E05_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />
        
        <div className="relative max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            {/* Category & Meta */}
            <div className="flex flex-wrap items-center gap-4 mb-6">
              <span className={`
                px-4 py-2 rounded-full text-sm font-semibold
                bg-gradient-to-r ${post.gradient} text-white
                ${firaCode.className}
              `}>
                {post.category}
              </span>
              <div className="flex items-center gap-4 text-[#0E1B2E]/60">
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" />
                  <span className={`${victorMono.className} text-sm`}>
                    {formatDate(post.date)}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4" />
                  <span className={`${victorMono.className} text-sm`}>
                    {post.readTime}
                  </span>
                </div>
              </div>
            </div>

            {/* Title */}
            <h1 className={`
              ${firaCode.className} text-4xl md:text-5xl lg:text-6xl 
              font-bold tracking-tight leading-[1.1] text-[#0E1B2E] mb-6
            `}>
              {post.title}
            </h1>

            {/* Excerpt */}
            <p className={`
              ${victorMono.className} text-xl text-[#0E1B2E]/70 mb-8 leading-relaxed
            `}>
              {post.excerpt}
            </p>

            {/* Author */}
            <div className="flex items-center gap-3 pb-8 border-b border-[#0E1B2E]/10">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center">
                <User className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className={`${firaCode.className} font-semibold text-[#0E1B2E]`}>
                  {post.author}
                </p>
                <p className={`${victorMono.className} text-sm text-[#0E1B2E]/60`}>
                  Engineering Team
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Article Content */}
      <article className="relative py-8 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="prose prose-lg max-w-none"
          >
            <div className={`
              ${victorMono.className} 
              text-base md:text-lg 
              leading-relaxed 
              text-[#0E1B2E]/90
              [&>h1]:${firaCode.className}
              [&>h1]:text-3xl
              [&>h1]:font-bold
              [&>h1]:text-[#0E1B2E]
              [&>h1]:mt-12
              [&>h1]:mb-6
              [&>h2]:${firaCode.className}
              [&>h2]:text-2xl
              [&>h2]:font-bold
              [&>h2]:text-[#0E1B2E]
              [&>h2]:mt-10
              [&>h2]:mb-4
              [&>h3]:${firaCode.className}
              [&>h3]:text-xl
              [&>h3]:font-semibold
              [&>h3]:text-[#0E1B2E]
              [&>h3]:mt-8
              [&>h3]:mb-3
              [&>p]:mb-6
              [&>p]:leading-relaxed
              [&>ul]:list-disc
              [&>ul]:ml-6
              [&>ul]:mb-6
              [&>ul>li]:mb-2
              [&>ul>li]:leading-relaxed
              [&>ol]:list-decimal
              [&>ol]:ml-6
              [&>ol]:mb-6
              [&>ol>li]:mb-2
              [&>ol>li]:leading-relaxed
              [&>strong]:font-semibold
              [&>strong]:text-[#0E1B2E]
              [&>a]:text-blue-600
              [&>a]:underline
              [&>a]:hover:text-blue-700
              [&>code]:${firaCode.className}
              [&>code]:bg-[#0E1B2E]/5
              [&>code]:px-2
              [&>code]:py-1
              [&>code]:rounded
              [&>code]:text-sm
              [&>blockquote]:border-l-4
              [&>blockquote]:border-[#0E1B2E]/20
              [&>blockquote]:pl-4
              [&>blockquote]:italic
              [&>blockquote]:text-[#0E1B2E]/70
              [&>blockquote]:my-6
            `}>
              <ReactMarkdown>{post.content}</ReactMarkdown>
            </div>
          </motion.div>

          {/* Tags */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mt-12 pt-8 border-t border-[#0E1B2E]/10"
          >
            <div className="flex flex-wrap items-center gap-3">
              <Tag className="w-5 h-5 text-[#0E1B2E]/60" />
              {post.tags.map((tag, index) => (
                <span
                  key={index}
                  className={`
                    px-3 py-1 rounded-full text-sm
                    bg-[#0E1B2E]/5 text-[#0E1B2E]/70
                    ${victorMono.className}
                  `}
                >
                  {tag}
                </span>
              ))}
            </div>
          </motion.div>
        </div>
      </article>

      <Footer />
    </main>
  );
}

