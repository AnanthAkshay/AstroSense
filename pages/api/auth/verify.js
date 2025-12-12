export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/auth/verify`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(req.body),
    })

    const data = await response.json()
    
    // Forward the Set-Cookie header if present
    const setCookieHeader = response.headers.get('set-cookie')
    if (setCookieHeader) {
      res.setHeader('Set-Cookie', setCookieHeader)
    }
    
    res.status(response.status).json(data)
  } catch (error) {
    console.error('Auth verify error:', error)
    res.status(500).json({ success: false, message: 'Internal server error' })
  }
}