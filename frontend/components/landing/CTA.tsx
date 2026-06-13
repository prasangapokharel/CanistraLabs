'use client';

import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';
import Link from 'next/link';

export function CTA() {
  return (
    <section className="py-24 md:py-32 bg-black relative overflow-hidden">
      <div className="absolute inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-radial from-purple-500/20 via-transparent to-transparent opacity-50" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 text-center md:px-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto space-y-8 p-12 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-md shadow-2xl shadow-purple-500/10"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-purple-300 backdrop-blur-sm mb-4">
            <Sparkles className="w-4 h-4" />
            <span>Start your Web3 journey today</span>
          </div>

          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-white tracking-tight">
            Ready to <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">Launch?</span>
          </h2>
          
          <p className="text-lg text-white/60 max-w-2xl mx-auto leading-relaxed">
            Join thousands of developers building the next generation of decentralized applications. 
            Deploy your first canister in minutes.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-8">
            <Link 
              href="/signup" 
              className="group inline-flex h-14 items-center justify-center gap-2 rounded-full bg-white px-8 text-lg font-medium text-black transition-all hover:bg-white/90 hover:scale-105"
            >
              Get Started Free
              <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            </Link>
            
            <Link 
              href="/contact" 
              className="inline-flex h-14 items-center justify-center gap-2 rounded-full border border-white/10 bg-white/5 px-8 text-lg font-medium text-white transition-all hover:bg-white/10 hover:border-white/20"
            >
              Contact Sales
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
