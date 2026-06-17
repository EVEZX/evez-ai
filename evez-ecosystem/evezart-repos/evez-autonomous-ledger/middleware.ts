import { NextResponse, type NextRequest } from 'next/server';

export const config = {
  matcher: ['/api/run', '/api/resume'],
};

export default async function middleware(_req: NextRequest) {
  return NextResponse.next();
}
