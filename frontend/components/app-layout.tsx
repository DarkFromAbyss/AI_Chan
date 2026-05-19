"use client";

import { Sidebar } from "@/components/sidebar";
import { CharacterShowcase } from "@/components/character-showcase";
import { ChatPanel } from "@/components/chat-panel";
import { useState } from "react";

/**
 * AppLayout Component
 * 
 * Root layout orchestrating the three main sections:
 * - Sidebar: Navigation and UI controls
 * - CharacterShowcase: 3D VRM model with WebGL text rendering
 * - ChatPanel: Chat interface with multi-modal response handling
 * 
 * State Management:
 * - displayContent: Text content from chat responses to render in 3D space
 * - statusVoiceText: Voice/spoken text to display in status indicator
 * - Passed from ChatPanel → AppLayout → CharacterShowcase → Status Badge
 * 
 * Multi-modal Response Flow:
 * 1. ChatPanel receives API response with display, voice, display2d
 * 2. Calls setDisplayContent with display2d content
 * 3. Calls setStatusVoiceText with voice content
 * 4. CharacterShowcase receives both props
 * 5. Voice text displayed in status badge, display2d in 3D scene
 * 6. Voice audio synthesized via TTS service
 */
export function AppLayout() {
  const [displayContent, setDisplayContent] = useState<string | null>(null);
  const [statusVoiceText, setStatusVoiceText] = useState<string | null>(null);

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background">
      {/* Left Sidebar - Navigation */}
      <Sidebar />

      {/* Center - Character Showcase with 3D text rendering */}
      <CharacterShowcase 
        displayContent={displayContent}
        statusVoiceText={statusVoiceText}
      />

      {/* Right - Chat Panel with multi-modal response handling */}
      <ChatPanel 
        setDisplayContent={setDisplayContent}
        setStatusVoiceText={setStatusVoiceText}
      />
    </div>
  );
}
