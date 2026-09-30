import { useCallback, useEffect, useRef, useState } from 'react';
import { speakUrl } from './api.js';

// Chrome fills the voice list asynchronously, so poll instead of reading once.
function pickVoice(lang) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return null;
  const voices = window.speechSynthesis.getVoices() || [];
  const tag = lang === 'hi' ? 'hi' : 'en';
  return (
    voices.find((v) => (v.lang || '').toLowerCase() === `${tag}-in`) ||
    voices.find((v) => (v.lang || '').toLowerCase().startsWith(tag)) ||
    null
  );
}

export function useSpeech() {
  const [speaking, setSpeaking] = useState(false);
  const [note, setNote] = useState('');
  const audioRef = useRef(null);
  const objectUrlRef = useRef(null);

  const supported = typeof window !== 'undefined' && !!window.speechSynthesis;

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setSpeaking(false);
  }, [supported]);

  const speak = useCallback(
    async (text, lang, t) => {
      if (!text) return;
      stop();
      setNote('');

      const voice = pickVoice(lang);
      if (voice) {
        try {
          const u = new SpeechSynthesisUtterance(text);
          u.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
          u.voice = voice;
          u.rate = 0.95;
          u.onend = () => setSpeaking(false);
          u.onerror = () => setSpeaking(false);
          window.speechSynthesis.speak(u);
          setSpeaking(true);
          return;
        } catch {
          // fall through to the server
        }
      }

      setSpeaking(true);
      setNote(t('generating_voice'));
      try {
        const url = await speakUrl(text, lang);
        if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = url;
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => setSpeaking(false);
        audio.onerror = () => setSpeaking(false);
        await audio.play();
      } catch {
        setSpeaking(false);
        setNote(t('voice_failed'));
      }
    },
    [stop, supported]
  );

  useEffect(() => () => {
    if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
  }, []);

  return { speak, stop, speaking, note, setNote, supported };
}
