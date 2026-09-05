import express from 'express';
import path from 'path';

import { spawn } from 'child_process';
import { createServer as createViteServer } from 'vite';
import { createProxyMiddleware } from 'http-proxy-middleware';




async function startServer() {
  const app = express();
  const PORT = 3000;

  // Start FastAPI backend on port 8082
  const pythonCmd = process.env.PYTHON_EXEC || (process.cwd() + '/venv/bin/python');
  const pyBackend = spawn(pythonCmd, ['-m', 'backend.main'], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: { ...process.env, PYTHONPATH: process.cwd() }
  });

  pyBackend.on('error', (err) => {
    console.error('Failed to start FastAPI backend:', err);
  });
  
  pyBackend.on('close', (code) => {
    console.error(`FastAPI backend exited with code ${code}`);
  });

  // Proxy /api and /ws to FastAPI
  app.use('/api', createProxyMiddleware({ target: 'http://127.0.0.1:8082', changeOrigin: true, pathRewrite: {'^/api': ''} }));
  app.use('/ws', createProxyMiddleware({ target: 'http://127.0.0.1:8082', ws: true, changeOrigin: true, pathRewrite: {'^/ws': ''} }));

  // Vite middleware for development
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*all', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`Node server running on http://localhost:${PORT}`);
  });
}

startServer();
