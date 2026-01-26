"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Icon-based quick access cards
 * - Chunky borders with hard shadows
 * - Vibrant accent colors
 */

import { Gift, Calendar, BookOpen, TrendingUp, Tablet, Video } from "lucide-react";
import Link from "next/link";

const quickLinks: Array<{ icon: any; label: string; color: string; link: string }> = [];

export default function QuickLinks() {
  return (
    <div className="bg-gray-50 py-8">
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {quickLinks.map((link, index) => {
            const Icon = link.icon;
            return (
              <Link
                key={index}
                href={link.link}
                className="bg-white border-2 border-gray-300 rounded-lg p-6 hover:scale-105 transition-all duration-150 flex flex-col items-center gap-3"
              >
                <div className={`${link.color} text-white p-4 rounded-lg border border-gray-300`}>
                  <Icon size={32} />
                </div>
                <span className="font-medium text-sm text-center">{link.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}

