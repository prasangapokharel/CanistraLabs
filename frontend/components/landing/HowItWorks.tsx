'use client';

import { motion } from 'framer-motion';
import { Code, Settings, Globe, BarChart } from 'lucide-react';

export function HowItWorks() {
  const steps = [
    {
      title: "Connect",
      description: "Link your GitHub repository or upload your build artifacts directly.",
      icon: Code,
      color: "text-blue-400",
      bg: "bg-blue-400/10",
      border: "border-blue-400/20"
    },
    {
      title: "Configure",
      description: "Our system auto-detects your framework and optimizes build settings.",
      icon: Settings,
      color: "text-purple-400",
      bg: "bg-purple-400/10",
      border: "border-purple-400/20"
    },
    {
      title: "Deploy",
      description: "Your site is deployed to the Internet Computer blockchain network.",
      icon: Globe,
      color: "text-pink-400",
      bg: "bg-pink-400/10",
      border: "border-pink-400/20"
    },
    {
      title: "Scale",
      description: "Serve millions of users with infinite scalability and zero config.",
      icon: BarChart,
      color: "text-orange-400",
      bg: "bg-orange-400/10",
      border: "border-orange-400/20"
    }
  ];

  return (
    <section className="py-24 md:py-32 bg-black relative overflow-hidden">
      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-3xl md:text-4xl lg:text-5xl font-bold text-white mb-6 leading-tight"
          >
            From Code to Chain in Minutes
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-lg text-white/60"
          >
            A seamless deployment pipeline designed for the modern web.
          </motion.p>
        </div>

        <div className="relative">
          {/* Connecting Line (Desktop) */}
          <div className="hidden md:block absolute top-12 left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent" />

          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2 }}
                className="relative flex flex-col items-center text-center"
              >
                {/* Step Number Badge */}
                <div className={`w-24 h-24 rounded-2xl ${step.bg} ${step.border} border flex items-center justify-center mb-6 relative z-10 backdrop-blur-sm group hover:scale-110 transition-transform duration-300`}>
                  <step.icon className={`w-10 h-10 ${step.color}`} />
                  <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white text-black font-bold flex items-center justify-center text-sm">
                    {i + 1}
                  </div>
                </div>

                <h3 className="text-xl font-bold text-white mb-3">{step.title}</h3>
                <p className="text-sm text-white/50 leading-relaxed">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
