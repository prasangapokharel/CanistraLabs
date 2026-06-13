'use client';

import { motion } from 'framer-motion';
import { Check, Cpu, Globe, Lock, Rocket, Server, Zap, Database } from 'lucide-react';

export function Features() {
  const features = [
    {
      title: "Edge Deployment",
      description: "Deploy instantly to a global network of canister smart contracts. Your app runs on the blockchain, not a server.",
      icon: Rocket,
      gradient: "from-purple-500 to-indigo-500",
      span: "md:col-span-2"
    },
    {
      title: "Infinite Scalability",
      description: "Auto-scaling is built-in. Handle millions of users without provisioning load balancers or configuring Kubernetes.",
      icon: Zap,
      gradient: "from-yellow-400 to-orange-500",
      span: "md:col-span-1"
    },
    {
      title: "Zero Downtime",
      description: "The Internet Computer protocol ensures your dApp is always online, censorship-resistant, and unstoppable.",
      icon: Server,
      gradient: "from-green-400 to-emerald-500",
      span: "md:col-span-1"
    },
    {
      title: "Tamper-proof Storage",
      description: "Content addressed storage guarantees data integrity. Serve assets directly from the chain with cryptographic verification.",
      icon: Lock,
      gradient: "from-red-400 to-pink-500",
      span: "md:col-span-2"
    },
    {
      title: "Global CDN",
      description: "Static assets are cached at the edge in boundary nodes worldwide for sub-millisecond latency.",
      icon: Globe,
      gradient: "from-blue-400 to-cyan-500",
      span: "md:col-span-1"
    },
    {
      title: "Web3 Native",
      description: "Integrate with Internet Identity, ledgers, and other canisters seamlessly. Build truly decentralized apps.",
      icon: Cpu,
      gradient: "from-indigo-400 to-purple-500",
      span: "md:col-span-1"
    },
    {
      title: "On-Chain Database",
      description: "Persist complex data structures directly in smart contract memory. No SQL, no NoSQL, just persistent objects.",
      icon: Database,
      gradient: "from-pink-400 to-rose-500",
      span: "md:col-span-1"
    },
  ];

  return (
    <section className="relative py-24 md:py-32 bg-black overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:48px_48px] mask-image-gradient-to-b from-black via-transparent to-transparent opacity-20 pointer-events-none" />
      
      <div className="relative z-10 mx-auto w-full max-w-7xl px-4 md:px-6">
        <div className="text-center max-w-3xl mx-auto mb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="inline-block px-3 py-1 rounded-full bg-purple-500/10 border border-purple-500/20 text-purple-400 text-sm font-medium mb-6"
          >
            Capabilities
          </motion.div>
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1 }}
            className="text-3xl md:text-4xl lg:text-5xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60 mb-6 leading-tight"
          >
            The Future of Web Hosting
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-white/60"
          >
            Canistra abstracts away the complexity of the Internet Computer, giving you a familiar Web2 developer experience with Web3 superpowers.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 auto-rows-[minmax(200px,auto)]">
          {features.map((feature, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ scale: 1.02 }}
              className={`group relative p-8 rounded-3xl bg-white/5 border border-white/10 hover:border-white/20 hover:bg-white/10 transition-all duration-300 ${feature.span}`}
            >
              <div className={`absolute inset-0 rounded-3xl bg-gradient-to-br ${feature.gradient} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />
              
              <div className="relative z-10 h-full flex flex-col">
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${feature.gradient} p-[1px] mb-6 shadow-lg shadow-purple-500/10`}>
                  <div className="w-full h-full rounded-2xl bg-black flex items-center justify-center">
                    <feature.icon className="w-6 h-6 text-white" />
                  </div>
                </div>

                <h3 className="text-xl font-semibold text-white mb-3 group-hover:text-purple-300 transition-colors">
                  {feature.title}
                </h3>
                
                <p className="text-white/50 leading-relaxed mt-auto">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Integration Badges */}
        <motion.div 
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="mt-20 flex flex-wrap justify-center gap-4 opacity-50 grayscale hover:grayscale-0 transition-all duration-500"
        >
          {["Next.js", "React", "Vue", "Svelte", "Angular", "Astro", "Rust", "Motoko"].map((tech) => (
            <div key={tech} className="px-4 py-2 rounded-full border border-white/10 bg-white/5 text-sm font-medium text-white/60 flex items-center gap-2 hover:bg-white/10 hover:text-white transition-colors cursor-default">
              <Check className="w-3 h-3 text-green-500" />
              {tech} Ready
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
