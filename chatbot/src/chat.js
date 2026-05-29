const BLOCKED_PATTERNS = [
  /should\s+i\s+(buy|sell|invest)/i,
  /\b(best|top)\s+(stock|fund|mutual fund|sip|share)/i,
  /price\s+prediction/i,
  /guaranteed\s+return/i,
  /multibagger/i,
  /which\s+(stock|fund|share)/i,
];

const TOPICS = [
  {
    keywords: ['sip', 'systematic investment plan'],
    title: 'Systematic Investment Plan',
    answer: 'A SIP is a way to invest a fixed amount at regular intervals. It can build discipline and reduce the stress of timing the market. The key ideas are consistency, suitable time horizon, and risk awareness.',
  },
  {
    keywords: ['emergency fund', 'emergency'],
    title: 'Emergency fund',
    answer: 'An emergency fund is money kept aside for unexpected needs such as job loss, medical costs, urgent travel, or repairs. Many education frameworks discuss keeping several months of essential expenses in safe and liquid instruments.',
  },
  {
    keywords: ['compounding', 'compound'],
    title: 'Compounding',
    answer: 'Compounding means earning returns on earlier returns. Time, consistency, and reinvestment are the main drivers. Small regular contributions can grow meaningfully over long periods, but returns are not guaranteed.',
  },
  {
    keywords: ['diversification', 'diversify'],
    title: 'Diversification',
    answer: 'Diversification means spreading money across assets, sectors, or instruments so one bad outcome does not dominate the entire plan. It reduces concentration risk but does not remove all risk.',
  },
  {
    keywords: ['risk tolerance', 'risk capacity', 'risk'],
    title: 'Risk capacity',
    answer: 'Risk capacity depends on income stability, dependents, debt, emergency fund, goal horizon, and ability to handle losses. It is different from risk preference, which is how comfortable someone feels with volatility.',
  },
];

export function isAdviceRequest(message) {
  return BLOCKED_PATTERNS.some((pattern) => pattern.test(message));
}

export function buildChatResponse(message) {
  const trimmed = String(message || '').trim();

  if (!trimmed) {
    return {
      blocked: false,
      source: 'validation',
      answer: 'Please ask a finance education question to get started.',
      citations: [],
    };
  }

  if (isAdviceRequest(trimmed)) {
    return {
      blocked: true,
      source: 'guardrail',
      answer: 'I cannot recommend buying, selling, timing, or choosing a specific stock, fund, or product. I can explain the concept, risks, and evaluation framework in education-only terms. For personal advice, consult a SEBI-registered investment adviser.',
      citations: [],
    };
  }

  const lower = trimmed.toLowerCase();
  const topic = TOPICS.find((item) => item.keywords.some((keyword) => lower.includes(keyword)));

  if (topic) {
    return {
      blocked: false,
      source: 'demo_knowledge_base',
      answer: topic.answer + ' This is education-only information, not investment advice.',
      citations: [{ title: topic.title, text: 'Demo knowledge base topic match' }],
    };
  }

  return {
    blocked: false,
    source: 'ai_fallback_ready',
    answer: 'I can help explain finance concepts in simple language. Try asking about SIPs, emergency funds, compounding, diversification, insurance, taxation, or risk capacity. I will keep the response educational and avoid product recommendations.',
    citations: [],
  };
}

export const suggestedQuestions = [
  'What is SIP?',
  'How does compounding work?',
  'What is an emergency fund?',
  'What is diversification?',
  'How should I understand risk capacity?',
];
