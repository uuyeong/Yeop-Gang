"use client";

/**
 * Design Philosophy: Neo-Brutalism Meets Korean EdTech
 * - Bold gradient backgrounds
 * - Chunky borders and hard shadows
 * - High contrast text
 */

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState, useEffect } from "react";
import Link from "next/link";

type Banner = {
  id: number;
  title: string;
  subtitle?: string;
  bgColor: string;
  link: string;
  imageUrl?: string;
};

const banners: Banner[] = [
  {
    id: 1,
    title: "내 옆의 강의, 옆강",
    bgColor: "bg-blue-400",
    link: "/student/courses",
    imageUrl: "/image/banner1.png",
  },
  {
    id: 2,
    title: "수능 영어 준비도",
    subtitle: "옆강에서 시작!",
    bgColor: "bg-sky-400",
    link: "/student/courses",
    imageUrl: "/image/banner2.png",
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

  // 자동 슬라이드 (5초마다)
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % banners.length);
    }, 5000); // 5초마다 자동으로 다음 슬라이드로 이동

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="relative bg-white pt-12 sm:pt-16 md:pt-24 pb-8 sm:pb-12 md:pb-16 mb-8 sm:mb-12 md:mb-16">
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
                href={banner.link as any}
                className={`min-w-full ${banner.bgColor} aspect-[21/9] sm:aspect-[21/9] flex items-center justify-center text-white cursor-pointer relative overflow-hidden`}
              >
                {banner.imageUrl ? (
                  <>
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={banner.imageUrl}
                      alt={banner.title}
                      className="absolute inset-0 w-full h-full object-cover"
                    />
                  </>
                ) : (
                  <div className="text-center px-4">
                    <h2
                      className="text-2xl sm:text-4xl md:text-6xl mb-2 sm:mb-4"
                      style={{ fontFamily: "var(--font-display)" }}
                    >
                      {banner.title}
                    </h2>
                    <p className="text-sm sm:text-lg md:text-2xl font-medium">{banner.subtitle}</p>
                  </div>
                )}
              </Link>
            ))}
          </div>

          {/* Navigation Buttons */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              prevSlide();
            }}
            className="absolute left-2 sm:left-4 top-1/2 -translate-y-1/2 bg-white rounded-full p-1.5 sm:p-2 hover:bg-primary hover:text-white transition-all duration-150 z-10"
            aria-label="Previous slide"
          >
            <ChevronLeft size={16} className="sm:w-[18px] sm:h-[18px]" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation();
              nextSlide();
            }}
            className="absolute right-2 sm:right-4 top-1/2 -translate-y-1/2 bg-white rounded-full p-1.5 sm:p-2 hover:bg-primary hover:text-white transition-all duration-150 z-10"
            aria-label="Next slide"
          >
            <ChevronRight size={16} className="sm:w-[18px] sm:h-[18px]" />
          </button>

          {/* Indicators */}
          <div className="absolute bottom-2 sm:bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5 sm:gap-2 z-10">
            {banners.map((_, index) => (
              <button
                key={index}
                onClick={(e) => {
                  e.stopPropagation();
                  setCurrentSlide(index);
                }}
                className={`w-2 h-2 sm:w-3 sm:h-3 rounded-full transition-all duration-150 ${
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

