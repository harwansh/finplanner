import { describe, expect, it } from 'vitest';
import { buildChatResponse, isAdviceRequest } from './chat.js';

describe('chat logic', () => {
  it('blocks investment advice', () => {
    expect(isAdviceRequest('Should I buy this fund?')).toBe(true);
    expect(buildChatResponse('Best stock to buy').blocked).toBe(true);
  });

  it('answers demo knowledge-base topics', () => {
    const response = buildChatResponse('Explain emergency fund');
    expect(response.blocked).toBe(false);
    expect(response.source).toBe('demo_knowledge_base');
  });

  it('handles unknown education questions safely', () => {
    const response = buildChatResponse('Explain term insurance');
    expect(response.blocked).toBe(false);
    expect(response.source).toBe('ai_fallback_ready');
  });
});
