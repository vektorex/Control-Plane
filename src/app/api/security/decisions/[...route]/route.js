// src/app/api/security/decisions/[...route]/route.js
import { NextResponse } from 'next/server';
import { SignalFabric } from '@/lib/decisions/SignalFabric';

/** Feature 21 — Universal Decision API & Event Contracts */
export async function GET(request, { params }) {
  const tenantId = request.headers.get('x-tenant-id') || 'tenant-1';
  const routeParams = params.route || [];
  const action = routeParams[0];

  try {
    let result = { message: `Decisions API Endpoint: ${action}` };

    if (action === 'health') {
      result = { status: 'OK', services: ['SignalFabric', 'ContextEngine', 'DecisionEngine'] };
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

    if (action === 'signals') {
      const fabric = new SignalFabric();
      const event = await fabric.ingestSignal(tenantId, payload.source, payload.data, payload.confidence);
      return NextResponse.json({ success: true, data: event }, { status: 201 });
    }

    return NextResponse.json({ success: false, message: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 400 });
  }
}
