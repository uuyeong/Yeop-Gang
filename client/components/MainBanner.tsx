"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Bold gradient backgrounds
 * - Chunky borders and hard shadows
 * - High contrast text
 */

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";
import Link from "next/link";

const banners = [
  {
    id: 1,
    title: "내 옆의 강의, 옆강",
    bgColor: "bg-blue-400",
    link: "/student/courses",
  },
  {
    id: 2,
    title: "수능 영어 준비도",
    subtitle: "옆강에서 시작!",
    bgColor: "bg-sky-400",
    link: "/student/courses",
  },
  {
    id: 3,
    title: "한국사 개념완성",
    subtitle: "기초부터 튼튼하게 개념 완성",
    bgColor: "bg-blue-500",
    link: "/student/courses",
  },
];

export default function MainBanner() {
  const [currentSlide, setCurrentSlide] = useState(0);

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % banners.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + banners.length) % banners.length);
  };

  return (
    <div className="relative bg-white py-8">
      <div className="container">
        <div className="relative overflow-hidden border-2 border-white rounded-lg">
          {/* Slides */}
          <div
            className="flex transition-transform duration-300 ease-in-out"
            style={{ transform: `translateX(-${currentSlide * 100}%)` }}
          >
            {banners.map((banner) => (
              <Link
                key={banner.id}
                href={banner.link}
                className={`min-w-full ${banner.bgColor} h-96 flex items-center justify-center text-white cursor-pointer`}
              >
                <div className="text-center">
                  <h2
                    className="text-6xl mb-4"
                    style={{ fontFamily: "var(--font-display)" }}
                  >
                    {banner.title}
                  </h2>
                  <p className="text-2xl font-medium">{banner.subtitle}</p>
                </div>
              </Link>
            ))}
          </div>

          {/* Navigation Buttons */}
          <button
            onClick={prevSlide}
            className="absolute left-4 top-1/2 -translate-y-1/2 bg-white border border-gray-400 rounded-lg p-3 hover:bg-primary hover:text-white transition-all duration-150"
            aria-label="Previous slide"
          >
            <ChevronLeft size={24} />
          </button>
          <button
            onClick={nextSlide}
            className="absolute right-4 top-1/2 -translate-y-1/2 bg-white border border-gray-400 rounded-lg p-3 hover:bg-primary hover:text-white transition-all duration-150"
            aria-label="Next slide"
          >
            <ChevronRight size={24} />
          </button>

          {/* Indicators */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
            {banners.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={`w-3 h-3 rounded-full border border-gray-400 transition-all duration-150 ${
                  index === currentSlide
                    ? "bg-white scale-125"
                    : "bg-white/50 hover:bg-white/75"
                }`}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

