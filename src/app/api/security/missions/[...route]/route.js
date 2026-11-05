// src/app/api/security/missions/[...route]/route.js
import { NextResponse } from 'next/server';
import { MissionControl } from '@/lib/missions/MissionControl';

/** Feature 21 — Mission Control API & Event Contracts */
export async function GET(request, { params }) {
  const tenantId = request.headers.get('x-tenant-id') || 'tenant-1';
  const routeParams = params.route || [];
  const action = routeParams[0];

  try {
    let result = { message: `Missions API Endpoint: ${action}` };

    if (action === 'health') {
      result = { status: 'OK', services: ['MissionControl', 'AgentOrchestrator', 'VerificationEngine'] };
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

    if (action === 'create') {
      const control = new MissionControl();
      const event = await control.createMission(tenantId, payload.name, payload.objectives, payload.riskTier);
      return NextResponse.json({ success: true, data: event }, { status: 201 });
    }

    return NextResponse.json({ success: false, message: 'Invalid action' }, { status: 400 });
  } catch (error) {
    return NextResponse.json({ success: false, error: error.message }, { status: 400 });
  }
}
