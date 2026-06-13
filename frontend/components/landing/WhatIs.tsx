'use client';

import { motion } from 'framer-motion';
import { Network, ShieldCheck, Zap, Database } from 'lucide-react';

export function WhatIs() {
  const features = [
    {
      icon: Zap,
      title: "Web Speed",
      description: "Smart contracts that run at web speed, serving HTTP requests directly to users."
    },
    {
      icon: Database,
      title: "On-Chain Storage",
      description: "Store gigabytes of data on-chain for a fraction of the cost of traditional blockchains."
    },
    {
      icon: Network,
      title: "Reverse Gas Model",
      description: "Users don't pay gas fees. Developers pre-pay computation costs for a seamless UX."
    },
    {
      icon: ShieldCheck,
      title: "Identity Built-in",
      description: "Secure, passwordless authentication using cryptographic passkeys and biometrics."
    }
  ];

  return (
    <section className="py-24 bg-black relative overflow-hidden">
      {/* Abstract Background */}
      <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 bg-purple-500/10 rounded-full blur-[100px]" />
      <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-96 h-96 bg-blue-500/10 rounded-full blur-[100px]" />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 md:px-6">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          
          {/* Content Side */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            className="space-y-8"
          >
            <h2 className="text-3xl md:text-4xl lg:text-5xl font-bold text-white leading-tight">
              The World Computer <br />
              <span className="text-white/60">Reimagined.</span>
            </h2>
            
            <p className="text-lg text-white/60 leading-relaxed">
              The Internet Computer (ICP) is the first true world computer blockchain that can run social networks, 
              enterprise systems, and web services entirely on-chain.
            </p>
            
            <div className="grid sm:grid-cols-2 gap-6 mt-8">
              {features.map((feature, i) => (
                <div key={i} className="space-y-2">
                  <div className="flex items-center gap-2 text-white font-semibold">
                    <feature.icon className="w-5 h-5 text-purple-400" />
                    {feature.title}
                  </div>
                  <p className="text-sm text-white/50">{feature.description}</p>
                </div>
              ))}
            </div>
          </motion.div>

          {/* Visual Side - 3D Cube Representation */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="relative aspect-square flex items-center justify-center"
          >
            {/* Concentric Circles Animation */}
            {[1, 2, 3].map((i) => (
              <motion.div
                key={i}
                animate={{ 
                  scale: [1, 1.2, 1],
                  opacity: [0.3, 0.1, 0.3],
                  borderWidth: ["1px", "2px", "1px"]
                }}
                transition={{ 
                  duration: 3 + i,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: i * 0.5
                }}
                className="absolute inset-0 m-auto rounded-full border border-purple-500/30"
                style={{ width: `${i * 30}%`, height: `${i * 30}%` }}
              />
            ))}
            
            {/* Central Node */}
            <div className="relative w-32 h-32 bg-gradient-to-br from-purple-600 to-blue-600 rounded-2xl flex items-center justify-center shadow-[0_0_50px_rgba(124,58,237,0.5)] z-10 rotate-12 group hover:rotate-0 transition-transform duration-500">
              <span className="text-4xl font-bold text-white">ICP</span>
              
              {/* Orbiting Elements */}
              <motion.div 
                animate={{ rotate: 360 }}
                transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                className="absolute inset-0 w-48 h-48 -m-8 border border-white/10 rounded-full"
              >
                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1.5 w-3 h-3 bg-white rounded-full shadow-[0_0_10px_white]" />
              </motion.div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  );
}
