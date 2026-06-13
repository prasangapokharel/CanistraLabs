import type { Metadata } from "next";
import { Syne, DM_Sans } from "next/font/google";
import "./globals.css";
import { AppProviders } from "./providers";

const syne = Syne({
  subsets: ["latin"],
  variable: "--font-syne",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ICP Hosting Platform - Canistra",
  description: "Deploy your web applications to the Internet Computer Protocol with ease",
  keywords: ["ICP", "Internet Computer", "Web3", "Hosting", "Deployment", "Blockchain"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body
        className={`${syne.variable} ${dmSans.variable} font-body antialiased bg-background text-foreground relative`}
      >
        <AppProviders>{children}</AppProviders>
      </body>
    </html>
  );
}
