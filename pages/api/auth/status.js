export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ message: 'Method not allowed' })
  }

  try {
    const response = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/auth/status`, {
      method: 'GET',
      headers: {
        'Cookie': req.headers.cookie || '',
      },
    })

    const data = await response.json()
    
    res.status(response.status).json(data)
  } catch (error) {
    console.error('Auth status error:', error)
    res.status(500).json({ authenticated: false, user: null })
  }
}