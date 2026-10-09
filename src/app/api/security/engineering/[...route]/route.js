// src/app/api/security/engineering/[...route]/route.js
import { NextResponse } from 'next/server';
import { Watcher } from '@/lib/engineering/Watcher';

/** Feature 21 — Engineering API & Event Contracts */
export async function GET(request, { params }) {
  const tenantId = request.headers.get('x-tenant-id') || 'tenant-1';
  const routeParams = params.route || [];
  const action = routeParams[0];

  try {
    let result = { message: `Engineering API Endpoint: ${action}` };

    if (action === 'health') {
      result = { status: 'OK', services: ['Watcher', 'PatchEngine', 'VerificationPipeline', 'Operations'] };
    }

    return NextResponse.json({
      success: true,
      data: result,
      correlationId: crypto.randomUUID()
    });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 500 });
  }
}

export async function POST(request, { params }) {
  const tenantId = request.headers.get('x-tenant-id') || 'tenant-1';
  const routeParams = params.route || [];
  const action = routeParams[0];

  try {
    const payload = await request.json();

    if (action === 'watcher') {
      const watcher = new Watcher();
      const event = await watcher.logEvent(tenantId, payload.source, payload.repo, payload.findings, payload.severity);
      return NextResponse.json({ success: true, data: event }, { status: 201 });
    }

    return NextResponse.json({ success: false, message: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 400 });
  }
}
