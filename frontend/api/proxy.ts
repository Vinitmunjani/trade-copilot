import { NextRequest, NextResponse } from 'next/server';

export const config = {
  runtime: 'nodejs',
};

export default async function handler(req: NextRequest) {
  const url = new URL(req.url);
  const pathname = new URL(req.url).pathname;
  
  // Extract the path after /api/proxy/
  const path = pathname.replace('/api/proxy', '') || '/health';
  const method = req.method;
  
  // Backend URL - points to localhost:443 (through Nginx)
  const backendUrl = `https://localhost:443${path}`;
  
  try {
    const headers = new Headers(req.headers);
    headers.delete('host');
    headers.delete('connection');
    
    console.log(`[PROXY] ${method} ${path} → ${backendUrl}`);
    
    const fetchOptions: RequestInit = {
      method,
      headers,
    };
    
    // Include body for POST, PUT, PATCH requests
    if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
      const body = await req.text();
      if (body) {
        fetchOptions.body = body;
      }
    }
    
    const response = await fetch(backendUrl, fetchOptions);
    
    const responseHeaders = new Headers(response.headers);
    responseHeaders.set('Access-Control-Allow-Origin', '*');
    responseHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS, PATCH');
    responseHeaders.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With');
    responseHeaders.set('Access-Control-Max-Age', '86400');
    
    const body = await response.text();
    
    console.log(`[PROXY] Response: ${response.status}`);
    
    return new NextResponse(body, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('[PROXY] Error:', error);
    return NextResponse.json(
      {
        error: 'Proxy failed',
        message: String(error),
        path,
      },
      { status: 502 }
    );
  }
}
