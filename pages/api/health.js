// Next.js API route for health check
export default function handler(req, res) {
  res.status(200).json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'AstroSense API',
    version: '1.0.0'
  });
}