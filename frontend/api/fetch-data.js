// Vercel serverless function for NASA API
export default async function handler(req, res) {
  const NASA_API_KEY = 'ATOOD7MgZPxGcaTmPZckylMkHC0SWfZK3HUgyK05';
  
  try {
    // Fetch from NASA DONKI API
    const response = await fetch(
      `https://api.nasa.gov/DONKI/CME?startDate=2024-01-01&endDate=2024-12-31&api_key=${NASA_API_KEY}`
    );
    
    if (!response.ok) {
      throw new Error(`NASA API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    res.status(200).json({
      success: true,
      data: data.slice(0, 10), // Return latest 10 events
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}