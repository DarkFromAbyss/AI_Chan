/**
 * Response Parser Utilities
 * 
 * Handles extraction of XML tags from LLM backend responses.
 * Supports dual-track output: display (chat) and voice (TTS).
 * 
 * Process:
 * 1. Extract XML tag content using regex patterns
 * 2. Sanitize extracted text
 * 3. Return structured response object
 * 4. Provide fallbacks for missing tags
 */

/**
 * Extract content between XML tags using regex
 * Pattern: <tagName>content</tagName>
 * Case-insensitive with support for whitespace
 */
function extractXmlTagContent(xml: string, tagName: string): string | null {
  try {
    const pattern = new RegExp(
      `<${tagName}\\s*>([\\s\\S]*?)<\\/${tagName}\\s*>`,
      "i"
    );
    const match = xml.match(pattern);
    return match ? match[1].trim() : null;
  } catch {
    return null;
  }
}

/**
 * Extract voice tag content from backend response
 * Used for status indicator and TTS rendering
 */
export function extractVoiceTag(responseText: string): string | null {
  return extractXmlTagContent(responseText, "voice");
}

/**
 * Extract display tag content from backend response
 * Used for chat history rendering
 */
export function extractDisplayTag(responseText: string): string | null {
  return extractXmlTagContent(responseText, "display");
}

/**
 * Extract display2d tag content from backend response
 * Used for 3D WebGL text rendering
 */
export function extractDisplay2dTag(responseText: string): string | null {
  return extractXmlTagContent(responseText, "display2d");
}

/**
 * Check if response contains voice tag
 * Useful for conditional rendering
 */
export function hasVoiceTag(responseText: string): boolean {
  return extractVoiceTag(responseText) !== null;
}

/**
 * Sanitize extracted voice text for display
 * Remove extra whitespace, normalize line breaks
 */
export function sanitizeVoiceText(voiceText: string): string {
  return voiceText
    .replace(/\s+/g, " ") // Collapse multiple whitespace
    .trim();
}

/**
 * Process backend response and extract all components
 * Returns structured object with extracted tags and fallbacks
 */
export interface ParsedResponse {
  display: string;
  voice: string | null;
  display2d: string | null;
  hasVoice: boolean;
}

export function parseBackendResponse(
  responseText: string,
  defaultDisplay: string = "No response"
): ParsedResponse {
  const voice = extractVoiceTag(responseText);
  const display = extractDisplayTag(responseText) || defaultDisplay;
  const display2d = extractDisplay2dTag(responseText);

  return {
    display,
    voice: voice ? sanitizeVoiceText(voice) : null,
    display2d,
    hasVoice: voice !== null,
  };
}
