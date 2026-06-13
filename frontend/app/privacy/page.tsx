'use client';

import { motion } from 'framer-motion';
import { Header } from '@/components/landing/Header';
import { Footer } from '@/components/landing/Footer';

export default function PrivacyPage() {
  return (
    <div className="bg-landing-bg">
      <Header />
      <main className="pt-20">
        <div className="max-w-3xl mx-auto py-24 px-6 md:px-12 lg:px-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-white/70 leading-relaxed space-y-12"
          >
            <div className="text-center mb-16">
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">Privacy Policy</h1>
              <p className="text-white/60">Last updated: March 21, 2026</p>
            </div>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Data Collection</h2>
              <p className="mb-4">
                We collect information you provide directly to us, such as when you create an account, 
                deploy applications, or contact us for support. This includes:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Account information (email address, username)</li>
                <li>Project and deployment data</li>
                <li>Payment information (processed securely through third-party providers)</li>
                <li>Communications with our support team</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Usage</h2>
              <p className="mb-4">
                We use the information we collect to provide, maintain, and improve our services, including:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Processing deployments and managing your applications</li>
                <li>Providing customer support and responding to your requests</li>
                <li>Monitoring usage and performance to improve our platform</li>
                <li>Communicating with you about service updates and important notices</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Cookies</h2>
              <p>
                We use cookies and similar technologies to enhance your experience, analyze usage patterns, 
                and personalize content. You can control cookie settings through your browser preferences. 
                Essential cookies required for basic functionality cannot be disabled.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Third Parties</h2>
              <p className="mb-4">
                We may share information with third-party service providers who assist us in operating our 
                platform, including:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Cloud infrastructure providers</li>
                <li>Payment processing services</li>
                <li>Analytics and monitoring tools</li>
                <li>Customer support platforms</li>
              </ul>
              <p className="mt-4">
                These providers are bound by confidentiality agreements and may only use your information 
                to provide services on our behalf.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Contact</h2>
              <p>
                If you have any questions about this Privacy Policy or our data practices, please contact 
                us at privacy@internetcomputer.com or through our support channels.
              </p>
            </section>
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
}