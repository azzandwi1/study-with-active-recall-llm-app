"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Settings } from "lucide-react"
import Link from "next/link"

interface ApiKeyGateProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function ApiKeyGate({ children, fallback }: ApiKeyGateProps) {
  const [hasApiKey, setHasApiKey] = useState(false)

  useEffect(() => {
    const key = localStorage.getItem("gemini_api_key")
    setHasApiKey(!!key)
  }, [])

  if (!hasApiKey) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="relative">
              <div className="opacity-50 pointer-events-none">{fallback || children}</div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Link href="/settings">
                  <Button variant="outline" size="sm" className="gap-2 bg-transparent">
                    <Settings className="h-4 w-4" />
                    Masukkan Kunci API
                  </Button>
                </Link>
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent>
            <p>Masukkan kunci API Gemini di Pengaturan untuk menggunakan fitur ini</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return <>{children}</>
}
