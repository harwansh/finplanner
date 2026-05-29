import React, { useState } from 'react';
import { askSmartFinly } from './api.js';
import { suggestedQuestions } from './chat.js';

function Message({ message }) {
  return React.createElement(
    'div',
    { className: 'message ' + message.role },
    React.createElement('div', { className: 'bubble' }, message.content),
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi, I am SmartFinly. Ask me finance education questions. I do not provide buy, sell, or product recommendations.',
    },
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  async function send(text) {
    const content = String(text || input).trim();
    if (!content || isLoading) return;

    setInput('');
    setIsLoading(true);
    setMessages((current) => [...current, { role: 'user', content }]);

    const response = await askSmartFinly(content);
    setMessages((current) => [...current, { role: 'assistant', content: response.answer }]);
    setIsLoading(false);
  }

  function onSubmit(event) {
    event.preventDefault();
    send(input);
  }

  return React.createElement(
    'main',
    { className: 'page' },
    React.createElement(
      'section',
      { className: 'hero' },
      React.createElement('p', { className: 'eyebrow' }, 'SmartFinly'),
      React.createElement('h1', null, 'Finance education chatbot'),
      React.createElement(
        'p',
        { className: 'subtitle' },
        'Learn concepts like SIPs, emergency funds, diversification, compounding, taxation, insurance, and risk capacity in simple language.',
      ),
    ),
    React.createElement(
      'section',
      { className: 'chatShell', 'aria-label': 'SmartFinly chatbot' },
      React.createElement(
        'div',
        { className: 'chatHeader' },
        React.createElement('div', null, React.createElement('strong', null, 'SmartFinly Chat'), React.createElement('span', null, 'Education only')),
      ),
      React.createElement(
        'div',
        { className: 'messages' },
        messages.map((message, index) => React.createElement(Message, { key: index, message })),
        isLoading ? React.createElement(Message, { message: { role: 'assistant', content: 'Thinking...' } }) : null,
      ),
      React.createElement(
        'div',
        { className: 'suggestions' },
        suggestedQuestions.map((question) => React.createElement('button', { key: question, type: 'button', onClick: () => send(question), disabled: isLoading }, question)),
      ),
      React.createElement(
        'form',
        { className: 'composer', onSubmit },
        React.createElement('input', {
          value: input,
          onChange: (event) => setInput(event.target.value),
          placeholder: 'Ask a finance concept question...',
          'aria-label': 'Message',
          disabled: isLoading,
        }),
        React.createElement('button', { type: 'submit', disabled: isLoading }, isLoading ? 'Sending' : 'Send'),
      ),
    ),
    React.createElement(
      'footer',
      { className: 'disclaimer' },
      'SmartFinly is for education only. It is not a SEBI-registered investment adviser and does not provide investment, tax, legal, or insurance advice.',
    ),
  );
}
