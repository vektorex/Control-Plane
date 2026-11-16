// src/app/api/security/collective/[...route]/route.js
import { NextResponse } from 'next/server';
import { IntelligenceCore } from '@/lib/collective/IntelligenceCore';

/** Feature 22 — Public API, Webhooks & Event Integration */
export async function GET(request, { params }) {
  const tenantId = request.headers.get('x-tenant-id') || 'tenant-1';
  const resolvedParams = await params;
  const routeParams = resolvedParams?.route || [];
  const action = routeParams[0];

  try {
    let result = { message: `Collective API Endpoint: ${action}` };

    if (action === 'health') {
      result = { status: 'OK', services: ['IntelligenceCore', 'PrivacyEngine', 'CorrelationEngine'] };
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
  const resolvedParams = await params;
  const routeParams = resolvedParams?.route || [];
  const action = routeParams[0];

  try {
    const payload = await request.json();

    if (action === 'intelligence') {
      const core = new IntelligenceCore();
      const event = await core.ingestIntelligence(tenantId, payload);
      return NextResponse.json({ success: true, data: event }, { status: 201 });
    }

    return NextResponse.json({ success: false, message: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 400 });
  }
}
