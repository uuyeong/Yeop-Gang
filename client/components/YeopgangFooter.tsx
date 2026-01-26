"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Structured footer with clear sections
 * - Bold borders and organized information
 */

export default function YeopgangFooter() {
  return (
    <footer className="bg-gray-900 text-white py-8 sm:py-12 border-t border-gray-700">
      <div className="container">
        <div className="flex flex-col items-center justify-center text-center">
          <h3 className="text-xl sm:text-2xl font-bold mb-4 sm:mb-8" style={{ fontFamily: 'var(--font-display)' }}>
            옆강
          </h3>
          <p className="text-xs sm:text-sm text-gray-400 mb-2">
            Hateslop Final Project
          </p>
          <p className="text-xs text-gray-500 mt-2 sm:mt-4">
            © 2026 옆강. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}

