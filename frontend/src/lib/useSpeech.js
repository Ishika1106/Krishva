import { useCallback, useEffect, useRef, useState } from 'react';
import { speakUrl } from './api.js';
import { isSpeechSupported, listVoices, pickVoice } from './voices.js';

// Chrome populates the voice list asynchronously, so poll for a few seconds.
export function useSpeech() {
  const [speaking, setSpeaking] = useState(false);
  const [note, setNote] = useState('');
  const [engine, setEngine] = useState('server');   // 'server' | 'device'
  const [preferred, setPreferred] = useState('');   // voiceURI, '' = automatic
  const [voices, setVoices] = useState([]);
  const audioRef = useRef(null);
  const objectUrlRef = useRef(null);
  const supported = isSpeechSupported();

  useEffect(() => {
    if (!supported) return undefined;
    const sync = () => setVoices(listVoices());
    sync();
    window.speechSynthesis.onvoiceschanged = sync;
    const timers = [200, 600, 1200, 2000, 3500].map((ms) => setTimeout(sync, ms));
    return () => {
      window.speechSynthesis.onvoiceschanged = null;
      timers.forEach(clearTimeout);
    };
  }, [supported]);

  useEffect(
    () => () => {
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    },
    []
  );

  const stop = useCallback(() => {
    if (supported) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setSpeaking(false);
  }, [supported]);

  // Plays a real audio file. This is the default because Chrome's
  // speechSynthesis can fire onstart/onend while producing no sound.
  const playServerAudio = useCallback(
    async (text, lang, t) => {
      setSpeaking(true);
      setNote(t('generating_voice'));
      try {
        const url = await speakUrl(text, lang);
        if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = url;
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => { setSpeaking(false); setNote(''); };
        audio.onerror = () => { setSpeaking(false); setNote(t('voice_failed')); };
        await audio.play();
        setNote('');
      } catch {
        setSpeaking(false);
        setNote(t('voice_failed'));
      }
    },
    []
  );

  const speakDevice = useCallback(
    (text, lang) => {
      const available = listVoices();
      const voice = (preferred && available.find((v) => v.voiceURI === preferred)) || pickVoice(lang, available);
      if (!voice) return false;
      const u = new SpeechSynthesisUtterance(text);
      u.lang = voice.lang || (lang === 'hi' ? 'hi-IN' : 'en-IN');
      u.voice = voice;
      u.rate = 0.95;
      u.onend = () => setSpeaking(false);
      u.onerror = () => setSpeaking(false);
      window.speechSynthesis.speak(u);
      setSpeaking(true);
      return true;
    },
    [preferred]
  );

  const speak = useCallback(
    async (text, lang, t) => {
      if (!text) return;
      stop();
      setNote('');

      if (engine === 'device' && supported) {
        if (speakDevice(text, lang)) return;
      }
      await playServerAudio(text, lang, t);
    },
    [stop, engine, supported, speakDevice, playServerAudio]
  );

  return {
    speak, stop, speaking, note, setNote, supported,
    voices, preferred, setPreferred, engine, setEngine,
  };
}
