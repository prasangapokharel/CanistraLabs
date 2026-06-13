'use client';

import Link from 'next/link';
import { Twitter, Github, Linkedin } from 'lucide-react';

export function Footer() {
  const currentYear = new Date().getFullYear();

  const footerLinks = [
    {
      title: "Product",
      links: [
        { label: "Features", href: "/features" },
        { label: "Pricing", href: "/pricing" },
        { label: "Documentation", href: "/docs" },
        { label: "Changelog", href: "/changelog" },
      ]
    },
    {
      title: "Resources",
      links: [
        { label: "Blog", href: "/blog" },
        { label: "Community", href: "/community" },
        { label: "Help Center", href: "/help" },
        { label: "Status", href: "/status" },
      ]
    },
    {
      title: "Legal",
      links: [
        { label: "Privacy Policy", href: "/privacy" },
        { label: "Terms of Service", href: "/terms" },
        { label: "Cookie Policy", href: "/cookies" },
      ]
    }
  ];

  return (
    <footer className="bg-black text-white/60 border-t border-white/10">
      <div className="mx-auto w-full max-w-7xl px-4 py-16 md:px-6 md:py-24">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          {/* Brand Column */}
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 mb-6">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-purple-500 to-blue-500 p-[1px]">
                <div className="h-full w-full rounded-[7px] bg-black flex items-center justify-center">
                  <span className="font-bold text-white text-lg">C</span>
                </div>
              </div>
              <span className="font-bold text-xl text-white tracking-tight">Canistra</span>
            </Link>
            <p className="text-sm leading-relaxed mb-6 max-w-xs">
              The decentralized hosting platform for the modern web. Deploy to the Internet Computer with zero configuration.
            </p>
            <div className="flex gap-4">
              <Link href="#" className="text-white/40 hover:text-white transition-colors">
                <Twitter className="w-5 h-5" />
              </Link>
              <Link href="#" className="text-white/40 hover:text-white transition-colors">
                <Github className="w-5 h-5" />
              </Link>
              <Link href="#" className="text-white/40 hover:text-white transition-colors">
                <Linkedin className="w-5 h-5" />
              </Link>
            </div>
          </div>

          {/* Links Columns */}
          {footerLinks.map((column, i) => (
            <div key={i} className="col-span-1">
              <h4 className="font-bold text-white mb-6">{column.title}</h4>
              <ul className="space-y-4">
                {column.links.map((link, j) => (
                  <li key={j}>
                    <Link 
                      href={link.href}
                      className="text-sm hover:text-purple-400 transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-4 text-sm">
          <p>© {currentYear} Canistra Labs. All rights reserved.</p>
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
            System Operational
          </div>
        </div>
      </div>
    </footer>
  );
}
