// Simple NASA API route for Vercel
export default function handler(req, res) {
  const NASA_API_KEY = 'ATOOD7MgZPxGcaTmPZckylMkHC0SWfZK3HUgyK05';
  
  // Simple fetch without async/await to avoid Babel issues
  fetch(`https://api.nasa.gov/DONKI/CME?startDate=2024-01-01&endDate=2024-12-31&api_key=${NASA_API_KEY}`)
    .then(response => {
      if (!response.ok) {
        throw new Error(`NASA API error: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      res.status(200).json({
        success: true,
        data: data.slice(0, 10),
        timestamp: new Date().toISOString()
      });
    })
    .catch(error => {
      res.status(500).json({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      });
    });
}