// Tiny zero-dependency web service: keeps the daily refresh loop alive on a
// free Render web service. UptimeRobot pings GET / every 5 min to prevent sleep.
const http = require('http');

let lastRun = null;
let lastResult = null;
let running = false;

async function tick() {
  if (running) return;
  running = true;
  try {
    const { runRefresh } = await import('./refresh.mjs');
    lastResult = await runRefresh();
  } catch (e) {
    lastResult = { error: String(e && e.message || e) };
  }
  lastRun = new Date().toISOString();
  running = false;
}

const DAY = 24 * 60 * 60 * 1000;
setInterval(tick, DAY);
setTimeout(tick, 60 * 1000); // first run 1 min after boot

const port = process.env.PORT || 3000;
http.createServer((req, res) => {
  if (req.url === '/status') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ lastRun, lastResult, nextRunIn: 'within 24h' }));
  } else {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('hsn-finder updater ok\n');
  }
}).listen(port, () => console.log('updater listening on ' + port));
