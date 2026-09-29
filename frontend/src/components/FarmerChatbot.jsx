import { useMemo, useState } from 'react';
import { MessageCircle, Send, Sprout, X } from 'lucide-react';
import { chatWithAgronomist } from '../api/yieldApi';

const copy = {
  en: {
    title: 'KhetiAI Farmer Assistant',
    subtitle: 'Ask common questions about your crop',
    placeholder: 'Ask: When should I irrigate?',
    welcome: 'Namaste! I can help with irrigation, fertilizer, disease risk, soil, weather, yield and MSP.',
    send: 'Send',
    suggested: ['When should I irrigate?', 'How much urea should I use?', 'Is my wheat at disease risk?', 'What does NPK mean?'],
    error: 'I could not answer that right now. Please try again.',
    disclaimer: 'General guidance only. Confirm treatment decisions with a local agronomist and product label.',
  },
  hi: {
    title: 'KhetiAI किसान सहायक',
    subtitle: 'फसल से जुड़े आम सवाल पूछें',
    placeholder: 'पूछें: सिंचाई कब करें?',
    welcome: 'नमस्ते! मैं सिंचाई, खाद, रोग, मिट्टी, मौसम, उपज और MSP पर मदद कर सकता हूँ।',
    send: 'भेजें',
    suggested: ['सिंचाई कब करें?', 'यूरिया कब दें?', 'गेहूं में रोग का खतरा है?', 'NPK क्या है?'],
    error: 'अभी उत्तर नहीं मिल पाया। कृपया फिर कोशिश करें।',
    disclaimer: 'सामान्य मार्गदर्शन है। उपचार के फैसले स्थानीय कृषि विशेषज्ञ और उत्पाद लेबल से पुष्टि करें।',
  },
  pa: {
    title: 'KhetiAI ਕਿਸਾਨ ਸਹਾਇਕ',
    subtitle: 'ਫਸਲ ਬਾਰੇ ਆਮ ਸਵਾਲ ਪੁੱਛੋ',
    placeholder: 'ਪੁੱਛੋ: ਸਿੰਚਾਈ ਕਦੋਂ ਕਰੀਏ?',
    welcome: 'ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਸਿੰਚਾਈ, ਖਾਦ, ਰੋਗ, ਮਿੱਟੀ, ਮੌਸਮ, ਉਪਜ ਅਤੇ MSP ਬਾਰੇ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ।',
    send: 'ਭੇਜੋ',
    suggested: ['ਸਿੰਚਾਈ ਕਦੋਂ ਕਰੀਏ?', 'ਯੂਰੀਆ ਕਦੋਂ ਪਾਈਏ?', 'ਗੇਹੂੰ ਵਿੱਚ ਰੋਗ ਦਾ ਖਤਰਾ ਹੈ?', 'NPK ਕੀ ਹੈ?'],
    error: 'ਹੁਣੇ ਜਵਾਬ ਨਹੀਂ ਮਿਲ ਸਕਿਆ। ਕਿਰਪਾ ਕਰਕੇ ਦੁਬਾਰਾ ਕੋਸ਼ਿਸ਼ ਕਰੋ।',
    disclaimer: 'ਇਹ ਆਮ ਮਾਰਗਦਰਸ਼ਨ ਹੈ। ਇਲਾਜ ਲਈ ਸਥਾਨਕ ਖੇਤੀ ਮਾਹਿਰ ਅਤੇ ਉਤਪਾਦ ਲੇਬਲ ਤੋਂ ਪੁਸ਼ਟੀ ਕਰੋ।',
  },
};

export default function FarmerChatbot({ crop, stage, latitude, longitude, lang = 'en' }) {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const t = copy[lang] || copy.en;
  const suggestions = useMemo(() => t.suggested, [t]);

  const sendMessage = async (question = input) => {
    const text = question.trim();
    if (!text || loading) return;
    setInput('');
    setError('');
    setMessages((prev) => [...prev, { role: 'user', text }]);
    setLoading(true);
    try {
      const result = await chatWithAgronomist({
        message: text,
        crop,
        stage,
        language: lang,
        district: '',
      });
      setMessages((prev) => [...prev, {
        role: 'assistant',
        text: result.answer,
      }]);
    } catch (err) {
      setError(t.error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {open && (
        <div className="farmer-chat-panel">
          <div className="farmer-chat-header">
            <div className="flex items-center gap-3">
              <div className="farmer-chat-avatar"><Sprout size={20} /></div>
              <div>
                <h3>{t.title}</h3>
                <p>{t.subtitle}</p>
              </div>
            </div>
            <button type="button" className="farmer-chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
              <X size={19} />
            </button>
          </div>

          <div className="farmer-chat-body">
            <div className="farmer-chat-bubble assistant">{t.welcome}</div>

            {messages.map((m, i) => (
              <div key={`${m.role}-${i}`} className={`farmer-chat-bubble ${m.role}`}>
                {m.text}
              </div>
            ))}

            {!messages.length && (
              <div className="farmer-chat-suggestions">
                {suggestions.map((q) => (
                  <button key={q} type="button" onClick={() => sendMessage(q)} disabled={loading}>
                    {q}
                  </button>
                ))}
              </div>
            )}

            {loading && <div className="farmer-chat-bubble assistant">...</div>}
            {error && <div className="farmer-chat-error">{error}</div>}
          </div>

          <div className="farmer-chat-disclaimer">{t.disclaimer}</div>

          <form className="farmer-chat-input" onSubmit={(e) => { e.preventDefault(); sendMessage(); }}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={t.placeholder}
              maxLength={500}
              aria-label={t.placeholder}
            />
            <button type="submit" disabled={!input.trim() || loading} aria-label={t.send}>
              <Send size={18} />
            </button>
          </form>
        </div>
      )}

      {!open && (
        <button type="button" className="farmer-chat-fab" onClick={() => setOpen(true)} aria-label={t.title}>
          <MessageCircle size={24} />
          <span>{t.title}</span>
        </button>
      )}
    </>
  );
}
