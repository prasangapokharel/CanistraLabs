'use client';

import { motion, useInView } from 'framer-motion';
import { useRef, useEffect } from 'react';

function Counter({ from, to, suffix = '', prefix = '' }: { from: number; to: number; suffix?: string; prefix?: string }) {
  const nodeRef = useRef<HTMLSpanElement>(null);
  const isInView = useInView(nodeRef, { once: true, margin: "-100px" });
  
  useEffect(() => {
    if (!isInView) return;
    
    const node = nodeRef.current;
    if (!node) return;

    const controls = {
      value: from,
      stop: false
    };

    const duration = 2000; // 2s
    const startTime = performance.now();

    const update = (currentTime: number) => {
      if (controls.stop) return;
      
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Ease out quart
      const ease = 1 - Math.pow(1 - progress, 4);
      
      const current = from + (to - from) * ease;
      
      // Format number
      if (to % 1 !== 0) {
        node.textContent = prefix + current.toFixed(1) + suffix;
      } else {
        node.textContent = prefix + Math.floor(current).toLocaleString() + suffix;
      }

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    };

    requestAnimationFrame(update);

    return () => { controls.stop = true; };
  }, [from, to, suffix, prefix, isInView]);

  return <span ref={nodeRef} className="tabular-nums">{prefix}{from}{suffix}</span>;
}

export function Stats() {
  const stats = [
    { value: 5, label: "Storage Cost / GB / Year", prefix: "$" },
    { value: 100, label: "On-Chain Speed (ms)", suffix: "ms" },
    { value: 0, label: "Gas Fees for Users", prefix: "$" },
    { value: 100, label: "Uptime Guarantee", suffix: "%" },
  ];

  return (
    <section className="py-24 border-y border-white/10 bg-black relative overflow-hidden">
      <div className="absolute inset-0 bg-grid-white/[0.02] bg-[size:32px_32px]" />
      
      {/* Glow effect */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[100px] bg-purple-500/20 blur-[100px] rounded-full pointer-events-none" />

      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 md:px-6">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 md:gap-12">
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.1 }}
              className="text-center group"
            >
              <div className="text-4xl md:text-5xl font-mono font-bold text-white mb-2 tracking-tighter group-hover:text-purple-300 transition-colors">
                <Counter from={0} to={stat.value} suffix={stat.suffix} prefix={stat.prefix} />
              </div>
              <div className="text-xs md:text-sm font-medium text-white/40 uppercase tracking-widest group-hover:text-white/70 transition-colors">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
