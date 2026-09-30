import { useCallback, useEffect, useRef, useState } from 'react';
import { speakUrl } from './api.js';

// The server returns a real audio file, so it always plays; speechSynthesis was dropped because Chrome runs it silently.
export function useSpeech() {
  const [speaking, setSpeaking] = useState(false);
  const [note, setNote] = useState('');
  const audioRef = useRef(null);
  const objectUrlRef = useRef(null);

  useEffect(
    () => () => {
      if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
    },
    []
  );

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setSpeaking(false);
  }, []);

  const speak = useCallback(async (text, lang, t) => {
    if (!text) return;
    stop();
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
  }, [stop]);

  return { speak, stop, speaking, note, setNote };
}
