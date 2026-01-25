"use client";

import { useState } from "react";
import LoginModal from "./LoginModal";
import RegisterModal from "./RegisterModal";

type ClientLayoutProps = {
  children: React.ReactNode;
};

export default function ClientLayout({ children }: ClientLayoutProps) {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showRegisterModal, setShowRegisterModal] = useState(false);

  const handleLoginSuccess = () => {
    setShowLoginModal(false);
    // 페이지 새로고침하여 인증 상태 반영
    window.location.reload();
  };

  const handleRegisterSuccess = () => {
    setShowRegisterModal(false);
    // 페이지 새로고침하여 인증 상태 반영
    window.location.reload();
  };

  return (
    <>
      {children}
      {showLoginModal && (
        <LoginModal
          onClose={() => setShowLoginModal(false)}
          onSuccess={handleLoginSuccess}
        />
      )}
      {showRegisterModal && (
        <RegisterModal
          onClose={() => setShowRegisterModal(false)}
          onSuccess={handleRegisterSuccess}
        />
      )}
    </>
  );
}
