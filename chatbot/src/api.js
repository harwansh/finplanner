import { buildChatResponse } from './chat.js';

export async function askSmartFinly(message) {
  const apiUrl = import.meta.env.VITE_CHAT_API_URL;

  if (!apiUrl) {
    return buildChatResponse(message);
  }

  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      throw new Error('Chat API request failed');
    }

    return await response.json();
  } catch (error) {
    return {
      blocked: false,
      source: 'local_fallback',
      answer: buildChatResponse(message).answer + ' The live API is unavailable, so this response came from the local demo fallback.',
      citations: [],
    };
  }
}
