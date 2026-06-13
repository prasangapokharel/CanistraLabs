'use client';

import { motion } from 'framer-motion';
import { Header } from '@/components/landing/Header';
import { Footer } from '@/components/landing/Footer';

export default function TermsPage() {
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
              <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">Terms of Service</h1>
              <p className="text-white/60">Last updated: March 21, 2026</p>
            </div>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Acceptance</h2>
              <p>
                By accessing and using Internet Computer hosting services, you accept and agree to be bound 
                by these Terms of Service. If you do not agree to these terms, please do not use our services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Use of Service</h2>
              <p className="mb-4">
                Our platform enables you to deploy and host applications on the Internet Computer Protocol. 
                When using our services, you agree to:
              </p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Provide accurate and complete registration information</li>
                <li>Maintain the security of your account credentials</li>
                <li>Use the service in compliance with all applicable laws</li>
                <li>Respect the intellectual property rights of others</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Prohibited Conduct</h2>
              <p className="mb-4">You may not use our services to:</p>
              <ul className="list-disc list-inside space-y-2 ml-4">
                <li>Host illegal, harmful, or offensive content</li>
                <li>Violate any applicable laws or regulations</li>
                <li>Infringe upon intellectual property rights</li>
                <li>Transmit malware, viruses, or malicious code</li>
                <li>Attempt to gain unauthorized access to our systems</li>
                <li>Interfere with the normal operation of our services</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Limitation of Liability</h2>
              <p>
                To the maximum extent permitted by law, Internet Computer hosting services shall not be 
                liable for any indirect, incidental, special, consequential, or punitive damages, including 
                but not limited to loss of profits, data, or other intangible losses resulting from your 
                use of our services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Governing Law</h2>
              <p>
                These Terms of Service shall be governed by and construed in accordance with the laws of 
                the jurisdiction in which our company is incorporated, without regard to conflict of law 
                principles. Any disputes arising under these terms shall be subject to the exclusive 
                jurisdiction of the courts in that jurisdiction.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-6">Contact</h2>
              <p>
                If you have any questions about these Terms of Service, please contact us at 
                legal@internetcomputer.com or through our support channels.
              </p>
            </section>
          </motion.div>
        </div>
      </main>
      <Footer />
    </div>
  );
}