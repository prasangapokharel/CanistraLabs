'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, ArrowRight, Github } from 'lucide-react';

export function Header() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { href: '/about', label: 'Features' },
    { href: '/about', label: 'Pricing' },
    { href: '/help', label: 'Documentation' },
    { href: '/about', label: 'Blog' },
  ];

  return (
    <>
      <motion.header
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled ? 'bg-black/50 backdrop-blur-md border-b border-white/5 py-4' : 'bg-transparent py-6'
        }`}
      >
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 md:px-6">
          <div className="flex items-center justify-between w-full">
            {/* Logo */}
            <Link href="/" className="flex items-center gap-2 group">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-tr from-purple-500 to-blue-500 p-[1px]">
                <div className="h-full w-full rounded-[7px] bg-black flex items-center justify-center group-hover:bg-black/80 transition-colors">
                  <span className="font-bold text-white text-lg">C</span>
                </div>
              </div>
              <span className="font-bold text-xl text-white tracking-tight">Canistra</span>
            </Link>

            {/* Desktop Nav */}
            <nav className="hidden md:flex items-center gap-8">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="text-sm font-medium text-white/70 hover:text-white transition-colors"
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            {/* Actions */}
            <div className="hidden md:flex items-center gap-4">
              <Link
                href="https://github.com/canistra/platform"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 text-white/50 hover:text-white transition-colors"
              >
                <Github className="w-5 h-5" />
              </Link>
              <Link
                href="/auth/login"
                className="text-sm font-medium text-white hover:text-white/80 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/auth/signup"
                className="group inline-flex h-9 items-center justify-center gap-2 rounded-full bg-white px-4 text-sm font-medium text-black transition-colors hover:bg-white/90"
              >
                Get Started
                <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
              </Link>
            </div>

            {/* Mobile Menu Toggle */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="md:hidden p-2 text-white/70 hover:text-white"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed inset-0 z-40 bg-black/95 backdrop-blur-xl pt-24 px-6 md:hidden"
          >
            <nav className="flex flex-col gap-6 text-center">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setIsMenuOpen(false)}
                  className="text-2xl font-medium text-white/80 hover:text-white"
                >
                  {link.label}
                </Link>
              ))}
              <div className="h-px w-full bg-white/10 my-4" />
              <Link
                href="/auth/login"
                onClick={() => setIsMenuOpen(false)}
                className="text-lg font-medium text-white/80 hover:text-white"
              >
                Sign In
              </Link>
              <Link
                href="/auth/signup"
                onClick={() => setIsMenuOpen(false)}
                className="inline-flex h-12 items-center justify-center gap-2 rounded-full bg-white px-8 text-lg font-medium text-black transition-colors hover:bg-white/90"
              >
                Get Started
              </Link>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
