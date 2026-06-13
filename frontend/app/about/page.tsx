'use client';

import { motion } from 'framer-motion';
import { Header } from '@/components/landing/Header';
import { Footer } from '@/components/landing/Footer';

export default function AboutPage() {
  const teamMembers = [
    {
      name: "Sarah Chen",
      role: "Founder & CEO",
      description: "Former blockchain architect at DFINITY. Passionate about making decentralized computing accessible to everyone."
    },
    {
      name: "Marcus Rodriguez", 
      role: "CTO",
      description: "Full-stack engineer with 10+ years experience. Led engineering teams at successful Web3 startups."
    },
    {
      name: "Elena Volkov",
      role: "Head of Product",
      description: "Product strategist focused on developer experience. Previously at GitHub and Vercel building developer tools."
    }
  ];

  return (
    <div className="bg-landing-bg">
      <Header />
      <main className="pt-20">
        {/* Hero Section */}
        <section className="px-6 md:px-12 lg:px-20 py-24">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center"
            >
              <h1 className="font-heading font-bold text-4xl md:text-5xl lg:text-6xl text-white mb-6">
                Building the Decentralized Future
              </h1>
              <p className="text-white/70 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
                We&apos;re making it easy for developers to harness the power of the Internet Computer Protocol 
                and build applications that are truly unstoppable.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Mission Section */}
        <section className="px-6 md:px-12 lg:px-20 py-16">
          <div className="max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="space-y-12"
            >
              {/* Company Story */}
              <div>
                <h2 className="font-heading text-3xl font-bold text-white mb-6">Our Story</h2>
                <div className="text-white/70 text-lg leading-relaxed space-y-6">
                  <p>
                    The idea for Internet Computer hosting came from witnessing the limitations of traditional 
                    web infrastructure first-hand. Centralized hosting providers create single points of failure, 
                    impose censorship risks, and charge ever-increasing costs for basic reliability.
                  </p>
                  <p>
                    We saw the Internet Computer Protocol&apos;s revolutionary approach to decentralized computing 
                    and knew this was the foundation for a better web. A web where applications run forever, 
                    scale infinitely, and resist any form of interference.
                  </p>
                </div>
              </div>

              {/* Mission */}
              <div>
                <h2 className="font-heading text-3xl font-bold text-white mb-6">Our Mission</h2>
                <div className="text-white/70 text-lg leading-relaxed space-y-6">
                  <p>
                    To democratize access to unstoppable web hosting by making the Internet Computer Protocol 
                    as easy to use as traditional cloud platforms, but with the added benefits of 
                    decentralization, immutability, and infinite scalability.
                  </p>
                  <p>
                    We believe every developer should have access to infrastructure that can never be shut down, 
                    censored, or compromised by any single entity.
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Team Section */}
        <section className="px-6 md:px-12 lg:px-20 py-16">
          <div className="max-w-6xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
            >
              <h2 className="font-heading text-3xl font-bold text-white mb-12 text-center">Our Team</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {teamMembers.map((member, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.8, delay: 0.6 + index * 0.1 }}
                    className="rounded-3xl bg-white/5 border border-white/10 p-8 backdrop-blur text-center"
                  >
                    {/* Avatar placeholder */}
                    <div className="w-20 h-20 rounded-full bg-landing-accent/20 border border-landing-accent/30 mx-auto mb-6 flex items-center justify-center">
                      <span className="text-landing-accent font-bold text-lg">
                        {member.name.split(' ').map(n => n[0]).join('')}
                      </span>
                    </div>
                    
                    <h3 className="font-heading text-xl font-bold text-white mb-2">
                      {member.name}
                    </h3>
                    
                    <p className="text-landing-accent text-sm font-semibold mb-4">
                      {member.role}
                    </p>
                    
                    <p className="text-white/70 text-sm leading-relaxed">
                      {member.description}
                    </p>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}