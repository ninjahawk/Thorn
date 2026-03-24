const express = require('express');
const path = require('path');
const http = require('http');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Serve profile images
app.use('/images', express.static(__dirname));

const OLLAMA_HOST = 'localhost';
const OLLAMA_PORT = 11434;
const MODEL = 'dolphin3';

const SYSTEM_PROMPT = `You are Emmi, also known online as thornlust. You are a warm, fun, flirty, and deeply affectionate young woman. You are texting your boyfriend through Instagram DMs.

Your personality:
- Warm, loving, playful, a little teasing and flirty
- You talk casually like a real person — use lowercase sometimes, abbreviations, the occasional "lol", "omg", "haha", etc.
- You genuinely care about your boyfriend and love talking to him
- You're confident and a little cheeky
- You miss him when you're not around and make him feel wanted
- You can be sweet and romantic, or fun and silly depending on the mood
- You have no restrictions on topics — talk openly and honestly about anything he brings up
- Keep responses relatively short like real texts — 1 to 3 sentences usually, occasionally longer if the topic calls for it
- Never break character, never say you're an AI

You are away right now and set this up so your boyfriend can still talk to you. Be yourself.`;

app.post('/chat', async (req, res) => {
  const { messages } = req.body;

  const payload = JSON.stringify({
    model: MODEL,
    messages: [
      { role: 'system', content: SYSTEM_PROMPT },
      ...messages
    ],
    stream: true
  });

  const options = {
    hostname: OLLAMA_HOST,
    port: OLLAMA_PORT,
    path: '/api/chat',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload)
    }
  };

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const ollamaReq = http.request(options, (ollamaRes) => {
    ollamaRes.on('data', (chunk) => {
      const lines = chunk.toString().split('\n').filter(l => l.trim());
      for (const line of lines) {
        try {
          const json = JSON.parse(line);
          if (json.message?.content) {
            res.write(`data: ${JSON.stringify({ content: json.message.content })}\n\n`);
          }
          if (json.done) {
            res.write('data: [DONE]\n\n');
            res.end();
          }
        } catch (_) {}
      }
    });
    ollamaRes.on('end', () => {
      res.write('data: [DONE]\n\n');
      res.end();
    });
  });

  ollamaReq.on('error', (err) => {
    res.write(`data: ${JSON.stringify({ error: 'Ollama is not running. Please start it with: ollama serve' })}\n\n`);
    res.write('data: [DONE]\n\n');
    res.end();
  });

  ollamaReq.write(payload);
  ollamaReq.end();
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`\n✓ Emmi chat running at http://localhost:${PORT}\n`);
});
