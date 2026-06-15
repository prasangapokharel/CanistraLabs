'use client';

import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { ChevronDown, ArrowRight, Zap, Globe, Shield, Terminal } from 'lucide-react';
import Link from 'next/link';

export function Hero() {
  const containerRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  });

  const y = useTransform(scrollYProgress, [0, 1], ["0%", "50%"]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <section 
      ref={containerRef}
      className="relative min-h-[100dvh] flex flex-col items-center justify-center overflow-hidden bg-black text-white selection:bg-purple-500/30"
    >
      {/* Dynamic Background with Noise */}
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03] mix-blend-overlay pointer-events-none"></div>
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]"></div>
        <div className="absolute left-0 right-0 top-0 -z-10 m-auto h-[310px] w-[310px] rounded-full bg-purple-500 opacity-20 blur-[100px] animate-pulse"></div>
        <div className="absolute right-0 bottom-0 -z-10 h-[310px] w-[310px] rounded-full bg-blue-500 opacity-20 blur-[100px] animate-pulse delay-700"></div>
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-7xl flex-col items-center px-4 pt-20 text-center md:px-6">
        
        {/* Terminal Badge */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-mono text-purple-300 backdrop-blur-sm mb-8 hover:bg-white/10 transition-colors cursor-default"
        >
          <Terminal className="w-3 h-3" />
          <span>$ dfx deploy --network ic</span>
        </motion.div>

        {/* Main Headline */}
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="max-w-5xl text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-8 leading-tight"
        >
          <span className="bg-clip-text text-transparent bg-gradient-to-b from-white via-white to-white/50">
            The Cloud is Dead.
          </span>
          <br />
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-purple-500 to-indigo-500 animate-gradient-x">
            Long Live the Chain.
          </span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="max-w-2xl text-lg md:text-xl text-white/60 mb-10 leading-relaxed"
        >
          Deploy full-stack applications directly to the Internet Computer blockchain. 
          Zero AWS bills. Zero downtime. 100% on-chain.
        </motion.p>

        {/* Buttons */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row gap-4 w-full sm:w-auto"
        >
          <Link 
            href="/dashboard" 
            className="group relative inline-flex h-14 items-center justify-center gap-2 overflow-hidden rounded-full bg-white px-8 font-medium text-black transition-all hover:bg-white/90 hover:ring-2 hover:ring-white/20 hover:ring-offset-2 hover:ring-offset-black"
          >
            <span className="relative z-10 font-bold">Deploy Now</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            <div className="absolute inset-0 -z-10 bg-gradient-to-r from-blue-400/20 to-purple-400/20 opacity-0 transition-opacity group-hover:opacity-100" />
          </Link>
          
          <Link 
            href="/help" 
            className="inline-flex h-14 items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-8 font-medium text-white backdrop-blur-sm transition-all hover:bg-white/10 hover:border-white/20"
          >
            View Documentation
          </Link>
        </motion.div>

        {/* Feature Grid (Floating) */}
        <motion.div 
          style={{ y, opacity }}
          className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-5xl px-4"
        >
          {[
            { icon: Zap, title: "Edge Speed", desc: "Global caching via boundary nodes" },
            { icon: Shield, title: "Tamper Proof", desc: "Cryptographically secured assets" },
            { icon: Globe, title: "Unstoppable", desc: "Censorship-resistant hosting" },
          ].map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.5 + i * 0.1 }}
              className="group relative p-6 rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm transition-all hover:bg-white/10 hover:border-white/10 hover:-translate-y-1"
            >
              <div className="flex flex-col items-center gap-3 text-center">
                <div className="p-3 rounded-full bg-white/5 ring-1 ring-white/10 group-hover:bg-white/10 transition-colors group-hover:scale-110 duration-300">
                  <feature.icon className="w-6 h-6 text-purple-400" />
                </div>
                <h3 className="font-semibold text-white">{feature.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">{feature.desc}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

      </div>
      
      {/* Scroll Indicator */}
      <motion.div 
        animate={{ y: [0, 10, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-10 left-1/2 -translate-x-1/2 text-white/30 pointer-events-none"
      >
        <ChevronDown className="w-6 h-6" />
      </motion.div>
    </section>
  );
}
