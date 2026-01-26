"use client";

import MainBanner from "@/components/MainBanner";
import CourseSection from "@/components/CourseSection";

export default function Home() {
  return (
    <>
      <MainBanner />
      <div className="container">
        <div className="border-t border-gray-400 mt-0 mb-8 sm:mb-12 md:mb-16"></div>
      </div>
      <CourseSection />
    </>
  );
}

