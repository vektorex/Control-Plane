"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function CapacityIndexPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/app/capacity/forecast");
  }, [router]);

  return (
    <div className="p-8 text-center text-muted-foreground">
      Redirecting to Capacity Forecast...
    </div>
  );
}
